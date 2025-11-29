from typing import Any, Dict, List

import numpy as np
import asyncio
from math import radians, cos, sin, asin, sqrt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from repository.cluster_repository import ClusterRepository
from schemas.recommendation_schema import RecommendationResponse, RecommendationScore
from schemas.destination_schema import Location, DestinationCreate
from fastapi import HTTPException, status
from repository.cluster_repository import ClusterRepository
from services.cluster_service import ClusterService

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
    async def sort_recommendations_by_place_details(
        db: AsyncSession,
        recommendations: List[Dict[str, Any]],
        sort_by: str = "rating",
        ascending: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Sort recommendations by place details (rating, review_count, price_level).
        
        Args:
            db: Database session
            recommendations: List of recommendation items with destination_id
            sort_by: Field to sort by (rating, review_count, price_level)
            ascending: Sort order (False for descending, True for ascending)
        """
        try:
            if not recommendations:
                return []
            
            destination_ids = [rec['destination_id'] for rec in recommendations]
            
            query = text("""
                SELECT destination_id, rating, review_count, price_level
                FROM destinations
                WHERE destination_id = ANY(:ids)
            """)
            
            result = await db.execute(query, {"ids": destination_ids})
            place_details = {row.destination_id: dict(row._mapping) for row in result}
            
            for rec in recommendations:
                dest_id = rec['destination_id']
                if dest_id in place_details:
                    rec['rating'] = place_details[dest_id].get('rating', 0)
                    rec['review_count'] = place_details[dest_id].get('review_count', 0)
                    rec['price_level'] = place_details[dest_id].get('price_level', 0)
                else:
                    rec['rating'] = 0
                    rec['review_count'] = 0
                    rec['price_level'] = 0
            
            recommendations.sort(
                key=lambda x: x.get(sort_by, 0),
                reverse=not ascending
            )
            
            return recommendations
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error sorting recommendations by place details: {str(e)}"
            )
    
    @staticmethod
    async def sort_recommendations_by_user_cluster_affinity(
        db: AsyncSession,
        user_id: int,
        recommendations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Sort recommendations by how well they match the user's cluster preferences.
        
        Args:
            db: Database session
            user_id: User ID
            recommendations: List of recommendation items with destination_id
        """
        try:
            if not recommendations:
                return []
            
            # Get user's cluster
            query = text("""
                SELECT cluster_id FROM user_clusters
                WHERE user_id = :user_id
                ORDER BY created_at DESC
                LIMIT 1
            """)
            result = await db.execute(query, {"user_id": user_id})
            user_cluster = result.scalar_one_or_none()
            
            if user_cluster is None:
                return recommendations
            
            # Get cluster embedding
            cluster_vector = await ClusterService.compute_cluster_embedding(db, user_cluster)
            if cluster_vector is None:
                return recommendations
            
            # Get embeddings for all recommended destinations
            destination_ids = [rec['destination_id'] for rec in recommendations]
            query = text("""
                SELECT destination_id, embedding
                FROM destinations
                WHERE destination_id = ANY(:ids) AND embedding IS NOT NULL
            """)
            result = await db.execute(query, {"ids": destination_ids})
            dest_embeddings = {row.destination_id: row.embedding for row in result}
            
            # Calculate affinity scores
            cluster_vec = np.array(cluster_vector, dtype=np.float32)
            
            for rec in recommendations:
                dest_id = rec['destination_id']
                if dest_id in dest_embeddings:
                    dest_vec = np.array(dest_embeddings[dest_id], dtype=np.float32)
                    # Cosine similarity
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
    async def sort_recommendations_by_popularity(
        db: AsyncSession,
        recommendations: List[Dict[str, Any]],
        cluster_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Sort recommendations by popularity score.
        
        Args:
            db: Database session
            recommendations: List of recommendation items with destination_id
            cluster_id: Optional cluster ID to get cluster-specific popularity
        """
        try:
            if not recommendations:
                return []
            
            destination_ids = [rec['destination_id'] for rec in recommendations]
            
            if cluster_id:
                # Get cluster-specific popularity
                query = text("""
                    SELECT destination_id, popularity_score
                    FROM cluster_destinations
                    WHERE cluster_id = :cluster_id AND destination_id = ANY(:ids)
                """)
                result = await db.execute(query, {"cluster_id": cluster_id, "ids": destination_ids})
            else:
                # Get global popularity (based on visit count and rating)
                query = text("""
                    SELECT d.destination_id, 
                           (COALESCE(v.visit_count, 0) * 0.6 + COALESCE(d.rating, 0) * 20 * 0.4) as popularity_score
                    FROM destinations d
                    LEFT JOIN (
                        SELECT destination_id, COUNT(*) as visit_count
                        FROM visits
                        WHERE destination_id = ANY(:ids)
                        GROUP BY destination_id
                    ) v ON d.destination_id = v.destination_id
                    WHERE d.destination_id = ANY(:ids)
                """)
                result = await db.execute(query, {"ids": destination_ids})
            
            popularity_scores = {row.destination_id: row.popularity_score for row in result}
            
            for rec in recommendations:
                dest_id = rec['destination_id']
                rec['popularity_score'] = popularity_scores.get(dest_id, 0.0)
            
            recommendations.sort(key=lambda x: x.get('popularity_score', 0), reverse=True)
            
            return recommendations
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error sorting recommendations by popularity: {str(e)}"
            )
    
    @staticmethod
    async def recommend_for_user(
        db: AsyncSession, user_id: int, k: int = 10, use_hybrid: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Generate personalized recommendations for a single user.
        """
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
        """
        Hybrid recommendation combining semantic similarity and popularity for a cluster.
        """
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
    async def recommend_for_cluster_similarity(
        db: AsyncSession, cluster_id: int, k: int = 10
    ) -> List[Dict[str, Any]]:
        """Pure similarity-based recommendations for a cluster."""
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

            results = search_index(cluster_vector.tolist(), k=k)
            return results

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating similarity recommendations for cluster {cluster_id}: {str(e)}",
            )

    @staticmethod
    async def recommend_for_cluster_popularity(
        db: AsyncSession,
        cluster_id: int,
    ) -> List[Dict[str, Any]]:
        try:
            await ClusterService.compute_cluster_popularity(db, cluster_id)

            popular_destinations_raw = await ClusterRepository.get_destinations_in_cluster(
                db, cluster_id
            )

            results = [
                {
                    "destination_id": dest.destination_id,
                    "popularity_score": dest.popularity_score / 100.0,
                }
                for dest in popular_destinations_raw
            ]

            return results
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating popularity recommendations for cluster {cluster_id}: {str(e)}",
            )

    @staticmethod
    async def recommend_destination_based_on_user_cluster(
        db: AsyncSession, user_id: int, cluster_id: int, k: int = 10
    ) -> List[str]:
        try:
            if not is_index_ready():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="FAISS index is not available",
                )

            user_vector = await ClusterService.embed_preference(db, user_id)
            if user_vector is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Could not generate embedding for user {user_id}",
                )

            cluster_vector = await ClusterService.compute_cluster_embedding(db, cluster_id)
            if cluster_vector is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Could not compute embedding for cluster {cluster_id}",
                )

            u_vec = np.array(user_vector, dtype=np.float32)
            c_vec = np.array(cluster_vector, dtype=np.float32)

            combined_vector = (u_vec + c_vec) / 2

            norm = np.linalg.norm(combined_vector)
            if norm > 0:
                combined_vector = combined_vector / norm

            results = search_index(combined_vector.tolist(), k=k)

            destination_ids = [item["destination_id"] for item in results]

            return destination_ids

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating recommendations for user {user_id} and cluster {cluster_id}: {str(e)}",
            )
    
    @staticmethod
    async def recommend_nearby_by_cluster_tags(
        db: AsyncSession,
        user_id: int,
        current_location: Location,
        radius_km: float = 5.0,
        k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Recommend nearby destinations using text search with cluster-based tags.
        
        Args:
            db: Database session
            user_id: User ID to get cluster preferences
            current_location: Current GPS location
            radius_km: Search radius in kilometers
            k: Number of recommendations to return
        
        Returns:
            List of recommended destinations with scores and details
        """
        try:
            # Get user's cluster
            query = text("""
                SELECT cluster_id FROM user_clusters
                WHERE user_id = :user_id
                ORDER BY created_at DESC
                LIMIT 1
            """)
            result = await db.execute(query, {"user_id": user_id})
            user_cluster = result.scalar_one_or_none()
            
            if user_cluster is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No cluster found for user {user_id}"
                )
            
            # Get cluster's preferred tags/categories
            query = text("""
                SELECT DISTINCT d.category, COUNT(*) as frequency
                FROM visits v
                JOIN destinations d ON v.destination_id = d.destination_id
                JOIN user_clusters uc ON v.user_id = uc.user_id
                WHERE uc.cluster_id = :cluster_id
                GROUP BY d.category
                ORDER BY frequency DESC
                LIMIT 5
            """)
            result = await db.execute(query, {"cluster_id": user_cluster})
            cluster_categories = [row.category for row in result if row.category]
            
            if not cluster_categories:
                # Fallback to common categories
                cluster_categories = ["tourist_attraction", "restaurant", "park", "museum", "shopping_mall"]
            
            # Import MapService to use text_search
            from services.map_service import MapService
            from schemas.map_schema import TextSearchRequest
            
            # Perform text searches for each category
            all_places = []
            search_tasks = []
            
            # Convert radius to meters for Google Places API
            radius_meters = int(radius_km * 1000)
            
            for category in cluster_categories[:3]:  # Limit to top 3 categories
                search_request = TextSearchRequest(
                    query=category,
                    location=current_location,
                    radius=radius_meters
                )
                search_tasks.append(
                    MapService.text_search_place(db, search_request)
                )
            
            # Execute all searches concurrently
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Process results
            place_scores = {}
            
            for idx, result in enumerate(search_results):
                if isinstance(result, Exception):
                    continue
                
                category_weight = 1.0 - (idx * 0.2)  # Higher weight for top categories
                
                for place in result.results:
                    place_id = place.place_id
                    
                    # Calculate distance from current location
                    place_lat = place.geometry.location.lat
                    place_lng = place.geometry.location.lng
                    
                    # Haversine distance calculation
                    from math import radians, cos, sin, asin, sqrt
                    
                    lat1, lon1 = radians(current_location.lat), radians(current_location.lng)
                    lat2, lon2 = radians(place_lat), radians(place_lng)
                    
                    dlat = lat2 - lat1
                    dlon = lon2 - lon1
                    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                    c = 2 * asin(sqrt(a))
                    distance_km = 6371 * c
                    
                    # Skip if outside radius
                    if distance_km > radius_km:
                        continue
                    
                    # Calculate proximity score (closer = higher)
                    proximity_score = max(0, 1.0 - (distance_km / radius_km))
                    
                    # Calculate rating score
                    rating_score = (place.rating or 3.0) / 5.0 if hasattr(place, 'rating') else 0.6
                    
                    # Calculate review count score (normalized)
                    review_count = place.user_ratings_total or 0 if hasattr(place, 'user_ratings_total') else 0
                    review_score = min(1.0, review_count / 100.0)
                    
                    # Combined score with category weight
                    combined_score = (
                        proximity_score * 0.4 +
                        rating_score * 0.3 +
                        review_score * 0.15 +
                        category_weight * 0.15
                    )
                    
                    # Keep highest score if place appears in multiple searches
                    if place_id not in place_scores or combined_score > place_scores[place_id]['combined_score']:
                        place_scores[place_id] = {
                            'place_id': place_id,
                            'name': place.name,
                            'formatted_address': place.formatted_address,
                            'latitude': place_lat,
                            'longitude': place_lng,
                            'distance_km': round(distance_km, 2),
                            'rating': place.rating if hasattr(place, 'rating') else None,
                            'review_count': review_count,
                            'types': place.types if hasattr(place, 'types') else [],
                            'proximity_score': round(proximity_score, 3),
                            'rating_score': round(rating_score, 3),
                            'review_score': round(review_score, 3),
                            'category_weight': round(category_weight, 3),
                            'combined_score': round(combined_score, 3)
                        }
            
            # Sort by combined score
            recommendations = sorted(
                place_scores.values(),
                key=lambda x: x['combined_score'],
                reverse=True
            )
            
            # Get or create destinations in database
            for rec in recommendations[:k]:
                try:
                    # Check if destination exists
                    dest_query = text("""
                        SELECT destination_id FROM destinations
                        WHERE place_id = :place_id
                    """)
                    dest_result = await db.execute(dest_query, {"place_id": rec['place_id']})
                    dest_id = dest_result.scalar_one_or_none()
                    
                    if dest_id:
                        rec['destination_id'] = dest_id
                    else:
                        # Create new destination
                        new_dest = await DestinationService.create_destination(
                            db,
                            DestinationCreate(place_id=rec['place_id'])
                        )
                        rec['destination_id'] = new_dest.destination_id
                        
                except Exception:
                    rec['destination_id'] = None
            
            return recommendations[:k]
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error recommending nearby destinations by cluster tags: {str(e)}"
            )
