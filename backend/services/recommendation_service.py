from typing import Any, Dict, List, Optional

import numpy as np
import asyncio
from math import radians, cos, sin, asin, sqrt
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from repository.destination_repository import DestinationRepository
from repository.cluster_repository import ClusterRepository
from schemas.recommendation_schema import RecommendationResponse, RecommendationScore
from schemas.destination_schema import DestinationCreate
from services.cluster_service import ClusterService
from utils.embedded.faiss_utils import is_index_ready, search_index
from services.destination_service import DestinationService 
from services.map_service import MapService
from schemas.map_schema import TextSearchRequest, Location

def blend_scores(
    similarity_items: List[Dict[str, Any]],
    popularity_items: List[Dict[str, Any]],
    similarity_weight: float = 0.7,
    popularity_weight: float = 0.3,
    k: int = 20,
) -> RecommendationResponse:
    try:
        destination_scores = {}

        for item in similarity_items:
            dest_id = item["destination_id"]
            destination_scores[dest_id] = {
                "similarity": item.get("similarity_score", 0),
                "popularity": 0.0,
            }

        for item in popularity_items:
            dest_id = item["destination_id"]
            if dest_id not in destination_scores:
                destination_scores[dest_id] = {"similarity": 0.0, "popularity": 0.0}
            destination_scores[dest_id]["popularity"] = item.get("popularity_score", 0)

        results = []
        for dest_id, scores in destination_scores.items():
            hybrid_score = (
                scores["similarity"] * similarity_weight + scores["popularity"] * popularity_weight
            )
            results.append(
                RecommendationScore(
                    destination_id=dest_id,
                    hybrid_score=round(hybrid_score, 2),
                    similarity_score=round(scores["similarity"], 2),
                    popularity_score=round(scores["popularity"], 2),
                )
            )

        results.sort(key=lambda x: x.hybrid_score, reverse=True)

        return RecommendationResponse(recommendations=results[:k])

    except Exception:
        return RecommendationResponse(recommendations=[])


class RecommendationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        if not is_index_ready():
            raise RuntimeError("FAISS index is not available.")
    
    @staticmethod
    async def sort_recommendations_by_user_cluster_affinity(
        db: AsyncSession,
        user_id: int,
        recommendations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        try:
            if not recommendations:
                return []
            
            user_cluster = await ClusterRepository.get_user_latest_cluster(db, user_id)
            
            if user_cluster is None:
                return recommendations
            
            cluster_vector = await ClusterService.compute_cluster_embedding(db, user_cluster)
            if cluster_vector is None:
                return recommendations
            
            destination_ids = [rec['destination_id'] for rec in recommendations]
            dest_embeddings = await DestinationRepository.get_embeddings_by_ids(
                db, destination_ids
            )
            
            cluster_vec = np.array(cluster_vector, dtype=np.float32)
            
            for rec in recommendations:
                dest_id = rec['destination_id']
                if dest_id in dest_embeddings:
                    dest_vec = np.array(dest_embeddings[dest_id], dtype=np.float32)
                    affinity = np.dot(cluster_vec, dest_vec) / (
                        np.linalg.norm(cluster_vec) * np.linalg.norm(dest_vec) + 1e-8
                    )
                    rec['cluster_affinity'] = float(affinity)
                else:
                    rec['cluster_affinity'] = 0.0
            
            recommendations.sort(key=lambda x: x.get('cluster_affinity', 0), reverse=True)
            
            return recommendations
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error sorting recommendations by user cluster: {str(e)}"
            )
    
    @staticmethod
    async def recommend_for_user(
        db: AsyncSession, user_id: int, k: int = 10, use_hybrid: bool = False
    ) -> List[Dict[str, Any]]:
        try:
            if not is_index_ready():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="FAISS index is not available",
                )

            user_vector = await ClusterService.embed_preference(db, user_id)
            if not user_vector:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Could not generate embedding for user {user_id}",
                )

            recommendations = search_index(user_vector, k=k)
            return recommendations

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating recommendations for user {user_id}: {str(e)}",
            )

    @staticmethod
    async def recommend_for_cluster_hybrid(
        db: AsyncSession,
        cluster_id: int,
        k: int = 20,
        similarity_weight: float = 0.7,
        popularity_weight: float = 0.3,
    ) -> RecommendationResponse:
        try:
            if not is_index_ready():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="FAISS index is not available",
                )

            cluster_vector = await ClusterService.compute_cluster_embedding(db, cluster_id)
            if cluster_vector is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Could not compute embedding for cluster {cluster_id}",
                )

            similar_destinations = search_index(cluster_vector.tolist(), k=k * 2)

            await ClusterService.compute_cluster_popularity(db, cluster_id)

            popular_destinations_raw = await ClusterRepository.get_cluster_destinations(
                db, cluster_id
            )

            popular_destinations = [
                {
                    "destination_id": dest.destination_id,
                    "popularity_score": dest.popularity_score / 100.0,
                }
                for dest in popular_destinations_raw
            ]

            results = blend_scores(
                similar_destinations,
                popular_destinations,
                similarity_weight,
                popularity_weight,
                k,
            )

            return results

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating hybrid recommendations for cluster {cluster_id}: {str(e)}",
            )

    
    @staticmethod
    async def recommend_nearby_by_cluster_tags(
        db: AsyncSession,
        user_id: int,
        current_location: Location,
        radius_km: float = 5.0,
        k: int = 10
    ) -> List[Dict[str, Any]]:
        try:
            user_cluster = await ClusterRepository.get_user_latest_cluster(db, user_id)
            cluster_categories = []
            
            if user_cluster:
                cluster_categories = await ClusterRepository.get_cluster_preferred_categories(
                    db, user_cluster, limit=5
                )
            
            if not cluster_categories:
                cluster_categories = ["park", "garden", "tourist_attraction", "museum"]

            search_results = []
            radius_meters = int(radius_km * 1000)
            
            for category in cluster_categories[:3]:
                try:
                    search_request = TextSearchRequest(
                        query=category,
                        location=current_location,
                        radius=radius_meters
                    )
                    result = await MapService.text_search_place(db, search_request)
                    search_results.append(result)
                except Exception as e:
                    print(f"Search failed for category {category}: {e}")
                    continue
            
            place_scores = {}
            
            for idx, result in enumerate(search_results):
                if not result or not result.results:
                    continue
                
                category_weight = 1.0 - (idx * 0.2)
                
                for place in result.results:
                    place_id = place.place_id
                    
                    if not place.location:
                        continue
                    
                    place_lat = place.location.latitude
                    place_lng = place.location.longitude
                    
                    curr_lat = current_location.latitude
                    curr_lng = current_location.longitude
                    
                    lat1, lon1 = radians(curr_lat), radians(curr_lng)
                    lat2, lon2 = radians(place_lat), radians(place_lng)
                    
                    dlat = lat2 - lat1
                    dlon = lon2 - lon1
                    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                    c = 2 * asin(sqrt(a))
                    distance_km = 6371 * c
                    
                    if distance_km > radius_km:
                        continue
                    
                    proximity_score = max(0, 1.0 - (distance_km / radius_km))
                    
                    rating_val = getattr(place, 'rating', None)
                    rating_score = (rating_val or 3.0) / 5.0 if rating_val else 0.6
                    
                    user_ratings = getattr(place, 'user_ratings_total', 0)
                    review_score = min(1.0, (user_ratings or 0) / 100.0)
                    
                    combined_score = (
                        proximity_score * 0.4 +
                        rating_score * 0.3 +
                        review_score * 0.15 +
                        category_weight * 0.15
                    )
                    
                    place_name = place.display_name.text if place.display_name else "Unknown Place"

                    if place_id not in place_scores or combined_score > place_scores[place_id]['combined_score']:
                        place_scores[place_id] = {
                            'place_id': place_id,
                            'name': place_name,
                            'formatted_address': place.formatted_address,
                            'latitude': place_lat,
                            'longitude': place_lng,
                            'distance_km': round(distance_km, 2),
                            'rating': rating_val,
                            'review_count': user_ratings,
                            'types': place.types,
                            'proximity_score': round(proximity_score, 3),
                            'rating_score': round(rating_score, 3),
                            'review_score': round(review_score, 3),
                            'category_weight': round(category_weight, 3),
                            'combined_score': round(combined_score, 3)
                        }
            
            recommendations = sorted(
                place_scores.values(),
                key=lambda x: x['combined_score'],
                reverse=True
            )
            
            # [FIX QUAN TRỌNG] Xử lý lưu DB: Dùng place_id thay vì destination_id
            top_recs = recommendations[:k]
            
            for rec in top_recs:
                place_id = rec['place_id']
                try:
                    # Gọi get_or_create_destination (hàm này nên trả về Destination object)
                    new_dest = await DestinationRepository.get_or_create_destination(db, place_id)
                    if new_dest:
                        # [FIX] Dùng .place_id thay vì .destination_id
                        rec['destination_id'] = new_dest.place_id 
                    else:
                        rec['destination_id'] = None
                except Exception as e:
                    # Log lỗi nhưng không crash API
                    print(f"Warning: Could not get/create destination {place_id}: {e}")
                    rec['destination_id'] = None
            
            return top_recs
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"DEBUG ERROR RECOMENDATION: {e}") 
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error recommending nearby destinations: {str(e)}"
            )