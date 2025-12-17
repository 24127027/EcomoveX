from typing import Any, Dict, List, Optional

import numpy as np
from math import radians, cos, sin, asin, sqrt
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from repository.destination_repository import DestinationRepository
from repository.cluster_repository import ClusterRepository
from schemas.recommendation_schema import RecommendationResponse, RecommendationScore, RecommendationDestination
from schemas.destination_schema import DestinationCreate
from services.cluster_service import ClusterService
from utils.embedded.faiss_utils import is_index_ready, search_index
from schemas.map_schema import (
    TextSearchRequest,
    Location,
    PlaceSearchResult,
    TextSearchResponse,
    NearbyPlacesResponse,
    NearbyPlaceRequest,
    LocalizedText,
    PhotoInfo,
)


def blend_scores(
    similarity_items: List[Dict[str, Any]],
    popularity_items: List[Dict[str, Any]],
    similarity_weight: float = 0.7,
    popularity_weight: float = 0.3,
    k: int = 20,
) -> RecommendationScore:
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
                scores["similarity"] * similarity_weight
                + scores["popularity"] * popularity_weight
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

    '''Change to receive TextSearchResponse and user_id'''
    @staticmethod
    async def sort_recommendations_by_user_cluster_affinity(
        db: AsyncSession, user_id: int, response: TextSearchResponse
    ) -> TextSearchResponse:
        try:
            if not response or not response.results:
                return response

            user_cluster = await ClusterRepository.get_user_latest_cluster(db, user_id)
            if user_cluster is None:
                return response

            cluster_vector = await ClusterService.compute_cluster_embedding(db, user_cluster)
            if cluster_vector is None:
                return response

            place_ids = [p.place_id for p in response.results]
            embeddings_list = await DestinationRepository.get_embeddings_by_ids(db, place_ids)

            # Chuẩn hoá embeddings
            dest_embeddings = {}
            if isinstance(embeddings_list, list):
                for emb in embeddings_list:
                    dest_embeddings[emb.destination_id] = emb.get_vector()
            else:
                dest_embeddings = embeddings_list

            cluster_vec = np.array(cluster_vector, dtype=np.float32)

            #  Tạo một map: id → affinity (không chạm vào object)
            affinities = {}

            for place in response.results:
                if place.place_id in dest_embeddings:
                    dest_vec = np.array(dest_embeddings[place.place_id], dtype=np.float32)
                    affinity = float(
                        np.dot(cluster_vec, dest_vec)
                        / (np.linalg.norm(cluster_vec) * np.linalg.norm(dest_vec) + 1e-8)
                    )
                else:
                    affinity = 0.0

                affinities[place.place_id] = affinity

            #  Sort kết quả theo map affinity
            response.results.sort(
                key=lambda p: affinities.get(p.place_id, 0.0),
                reverse=True
            )

            return response

        except Exception as e:
            print(f"Error in sort_recommendations_by_user_cluster_affinity: {type(e).__name__}: {str(e)}")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error sorting recommendations by user cluster: {type(e).__name__}: {str(e)}",
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

            cluster_vector = await ClusterService.compute_cluster_embedding(
                db, cluster_id
            )
            if cluster_vector is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Could not compute embedding for cluster {cluster_id}",
                )

            similar_destinations = search_index(cluster_vector.tolist(), k=k * 2)

            await ClusterService.compute_cluster_popularity(db, cluster_id)

            popular_destinations_raw = (
                await ClusterRepository.get_destinations_in_cluster(db, cluster_id)
            )

            popular_destinations: List[Dict[str, Any]] = [
                {
                    "destination_id": dest.destination_id,
                    "popularity_score": (dest.popularity_score or 0) / 100.0,
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
        k: int = 10,
    ) -> TextSearchResponse:
        try:
            # Import here to avoid circular import
            from services.map_service import MapService

            user_cluster = await ClusterRepository.get_user_latest_cluster(db, user_id)
            print(f"🔍 User {user_id} cluster: {user_cluster}")

            cluster_categories: List[str] = []

            if user_cluster is not None:
                cluster_prefs = await ClusterRepository.get_preference_by_user_id(
                    db, user_id
                )
                print(f"📊 Cluster preferences: {cluster_prefs}")
                if cluster_prefs and cluster_prefs.attraction_types:
                    # ✅ OPTIMIZATION: Limit to 3 categories max to reduce API calls (was 5)
                    cluster_categories = cluster_prefs.attraction_types[:3]
            
            # Fallback: if no cluster or no categories, use default popular categories
            if not cluster_categories:
                print(f"⚠️ No cluster categories found for user {user_id}, using defaults")
                # ✅ OPTIMIZATION: Reduced from 5 to 3 default categories
                cluster_categories = ["tourist_attraction", "park", "restaurant"]

            search_results: List[NearbyPlacesResponse] = []
            radius_meters: int = int(radius_km * 1000)

            print(f"📍 Searching with {len(cluster_categories)} categories: {cluster_categories}")
            # Use Text Search for better results
            for category in cluster_categories:
                try:
                    text_search_request = TextSearchRequest(
                        query=category,
                        location=current_location,
                        radius=radius_meters,
                        field_mask="places.displayName,places.formattedAddress,places.photos,places.types,places.location,places.rating,places.userRatingCount"
                    )
                    result = await MapService.text_search_place(
                        db=db,
                        data=text_search_request,
                        user_id=user_id,
                        convert_photo_urls=False
                    )
                    print(f"Text search results for '{category}': {len(result.results) if result else 0}")
                    if result and result.results:
                        search_results.append(result)
                except Exception as e:
                    print(f"Text search failed for category {category}: {e}")
                    continue

            # Store original PlaceSearchResult objects for reuse
            place_objects: Dict[str, PlaceSearchResult] = {}
            place_scores: Dict[str, Dict[str, Any]] = {}

            total_places_processed = 0
            places_without_location = 0
            places_outside_radius = 0

            for idx, result in enumerate(search_results):
                if not result.results:
                    continue

                category_weight: float = 1.0 - (idx * 0.2)

                # Process PlaceSearchResult objects
                for place in result.results:
                    total_places_processed += 1
                    place_id = place.place_id

                    if not place.location:
                        places_without_location += 1
                        continue

                    place_lat: float = place.location.lat
                    place_lng: float = place.location.lng

                    curr_lat: float = current_location.latitude
                    curr_lng: float = current_location.longitude

                    lat1, lon1 = radians(curr_lat), radians(curr_lng)
                    lat2, lon2 = radians(place_lat), radians(place_lng)

                    dlat: float = lat2 - lat1
                    dlon: float = lon2 - lon1
                    a: float = (
                        sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
                    )
                    c: float = 2 * asin(sqrt(a))
                    distance_km: float = 6371 * c

                    if distance_km > radius_km:
                        places_outside_radius += 1
                        continue

                    proximity_score: float = max(0.0, 1.0 - (distance_km / radius_km))

                    # PlaceSearchResult may not have rating field
                    rating_val: Optional[float] = getattr(place, 'rating', None)
                    rating_score: float = (
                        (rating_val or 3.0) / 5.0 if rating_val else 0.6
                    )

                    # Use user_ratings_total if available
                    user_ratings: Optional[int] = getattr(place, 'user_ratings_total', None)
                    review_score: float = min(1.0, (user_ratings or 0) / 500) if user_ratings else 0.3

                    combined_score: float = (
                        proximity_score * 0.4
                        + rating_score * 0.3
                        + review_score * 0.15
                        + category_weight * 0.15
                    )

                    # PlaceSearchResult has display_name field
                    place_name: str = place.display_name.text if place.display_name else "Unknown Place"

                    if (
                        place_id not in place_scores
                        or combined_score > place_scores[place_id]["combined_score"]
                    ):
                        place_scores[place_id] = {
                            "combined_score": round(combined_score, 3),
                            "distance_km": round(distance_km, 2),
                        }
                        # Store the original PlaceSearchResult object
                        place_objects[place_id] = place

            print("📊 Processing summary:")
            print(f"   Total places processed: {total_places_processed}")
            print(f"   Places without location: {places_without_location}")
            print(f"   Places outside radius ({radius_km}km): {places_outside_radius}")
            print(f"   Places within radius & scored: {len(place_scores)}")

            # Sort by combined score and get top K place IDs
            sorted_places = sorted(
                place_scores.items(), key=lambda x: x[1]["combined_score"], reverse=True
            )
            top_k_place_ids = [place_id for place_id, _ in sorted_places[:k]]
            print(f"✅ Returning {len(top_k_place_ids)} places to frontend")

            # Get top K places and convert photo references to URLs
            from integration.map_api import MapAPI
            map_api = MapAPI()

            top_results: List[PlaceSearchResult] = []
            photos_converted = 0
            for place_id in top_k_place_ids:
                place = place_objects[place_id]
                
                # Convert photo reference to URL if exists
                if place.photos and place.photos.photo_reference:
                    try:
                        photo_url = await map_api.generate_place_photo_url(
                            place.photos.photo_reference
                        )
                        # Create new PhotoInfo with the URL (Pydantic models are immutable)
                        place.photos = PhotoInfo(
                            photo_url=photo_url,
                            photo_reference=place.photos.photo_reference,
                            size=place.photos.size
                        )
                        photos_converted += 1
                    except Exception as e:
                        print(f"⚠️ Failed to convert photo URL for {place_id}: {e}")
                        # Keep the photo_reference, just set photo_url to None
                        place.photos = PhotoInfo(
                            photo_url=None,
                            photo_reference=place.photos.photo_reference,
                            size=place.photos.size
                        )
                
                # Create/update destination in DB
                try:
                    existing_dest = await DestinationRepository.get_destination_by_id(
                        db, place_id
                    )
                    if not existing_dest:
                        await DestinationRepository.create_destination(
                            db, DestinationCreate(place_id=place_id)
                        )
                except Exception as e:
                    print(f"⚠️ Could not get/create destination {place_id}: {e}")
                
                top_results.append(place)

            print(f"✅ Recommended {len(top_results)} nearby places for user {user_id} based on cluster tags.")
            print(f"📸 Converted {photos_converted}/{len(top_results)} photo URLs")
            
            # Return unified TextSearchResponse format
            response = TextSearchResponse(results=top_results)
            print(f"📤 Response structure: results count = {len(response.results)}")
            if response.results:
                first_place = response.results[0]
                print(f"   Sample place: {first_place.place_id}, name={first_place.display_name.text if first_place.display_name else 'N/A'}")
            return response

        except HTTPException:
            raise
        except Exception as e:
            print(f"DEBUG ERROR RECOMMENDATION: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error recommending nearby destinations: {str(e)}",
            )

    @staticmethod
    async def recommend_destinations_by_cluster_affinity(
        db: AsyncSession,
        user_id: int,
        k: int = 5,
    ) -> RecommendationDestination:
        """
        Recommends destinations from internal database based on cluster affinity.
        
        Computes cluster embedding from user preferences, then ranks destinations
        already associated with the cluster by their affinity score and popularity.
        
        Flow:
        1. Get user's cluster
        2. Compute cluster embedding (mean of user embeddings in cluster)
        3. Fetch destinations associated with that cluster from DB
        4. Compute affinity: cosine similarity between cluster embedding ↔ destination embedding
        5. Combine affinity (70%) + popularity (30%)
        6. Return top-K destination IDs
        
        Args:
            db: Database session
            user_id: ID of the user
            k: Number of recommendations to return (default: 5)
            
        Returns:
            List of destination IDs (strings) from internal database
        """
        try:
            # Step 1: Verify user exists
            from repository.user_repository import UserRepository
            user_exists = await UserRepository.get_user_by_id(db, user_id)
            if not user_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User {user_id} not found. Please log in again or register a new account."
                )

            # Step 2: Get user's latest cluster
            user_cluster = await ClusterRepository.get_user_latest_cluster(db, user_id)
            if user_cluster is None:
                # Check if user has preference record
                pref_exists = await ClusterRepository.get_preference_by_user_id(db, user_id)

                if not pref_exists:
                    # Create preference record if missing
                    print(f"⚠️ User {user_id} missing preference record, creating...")
                    await ClusterRepository.create_preference(db, user_id=user_id)
                    pref_exists = await ClusterRepository.get_preference_by_user_id(db, user_id)

                print(f"⚠️ User {user_id} has no cluster assignment, attempting to run clustering...")

                try:
                    clustering_result = await ClusterService.run_user_clustering(db)
                    print(f"✅ Clustering completed: {clustering_result.stats.clusters_updated} clusters, {clustering_result.stats.users_clustered} users clustered")
                    # Try to get cluster again after clustering
                    user_cluster = await ClusterRepository.get_user_latest_cluster(db, user_id)
                    if user_cluster is not None:
                        print(f"✅ User {user_id} assigned to cluster {user_cluster}")
                except Exception as cluster_error:
                    print(f"❌ Clustering failed: {cluster_error}")

                # If still no cluster, return empty recommendations
                if user_cluster is None:
                    print(f"ℹ️ User {user_id} still has no cluster after clustering attempt")
                    return RecommendationDestination(recommendation=[])

            # Step 2: Compute cluster embedding (mean of user embeddings)
            cluster_vector = await ClusterService.compute_cluster_embedding(db, user_cluster)
            if cluster_vector is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Could not compute embedding for cluster {user_cluster}"
                )

            # Step 3: Get all destinations associated with this cluster (from DB)
            cluster_destinations = await ClusterRepository.get_destinations_in_cluster(db, user_cluster)
            print(f"📍 Found {len(cluster_destinations)} destinations for cluster {user_cluster}")

            if not cluster_destinations:
                print(f"⚠️ No destinations associated with cluster {user_cluster}, using FAISS fallback...")

                # Fallback: Use FAISS-based recommendations instead
                if not is_index_ready():
                    print("❌ FAISS index not ready")
                    # Try to build index on-demand
                    try:
                        from database.db import get_sync_session
                        from utils.embedded.faiss_utils import build_index
                        print("🔧 Attempting to build FAISS index on-demand...")
                        with get_sync_session() as sync_db:
                            success = build_index(sync_db, normalize=False)
                            if not success:
                                print("❌ FAISS index build failed, returning empty recommendations")
                                return RecommendationDestination(recommendation=[])
                            print("✅ FAISS index built successfully")
                    except Exception as e:
                        print(f"❌ Failed to build FAISS index: {e}")
                        return RecommendationDestination(recommendation=[])

                # Search FAISS index using cluster embedding
                similar_destinations = search_index(cluster_vector.tolist(), k=k)
                destination_ids = [dest["destination_id"] for dest in similar_destinations[:k]]
                print(f"✅ FAISS fallback returned {len(destination_ids)} recommendations")
                return RecommendationDestination(recommendation=destination_ids)

            # Extract destination IDs
            destination_ids = [dest.destination_id for dest in cluster_destinations]

            # Get destination embeddings in batch
            embeddings_list = await DestinationRepository.get_embeddings_by_ids(db, destination_ids)

            # Normalize embeddings into a dictionary for O(1) lookup
            dest_embeddings = {}
            if isinstance(embeddings_list, list):
                for emb in embeddings_list:
                    dest_embeddings[emb.destination_id] = emb.get_vector()
            else:
                dest_embeddings = embeddings_list

            # Convert cluster vector to numpy array and pre-compute norm
            cluster_vec = np.array(cluster_vector, dtype=np.float32)
            cluster_norm = np.linalg.norm(cluster_vec)

            # Step 4: Calculate affinity scores for each destination
            recommendations = []
            for dest in cluster_destinations:
                dest_id = dest.destination_id

                # Skip if no embedding available
                if dest_id not in dest_embeddings:
                    continue

                # Get destination vector
                dest_vec = np.array(dest_embeddings[dest_id], dtype=np.float32)
                dest_norm = np.linalg.norm(dest_vec)

                # Calculate cosine similarity (affinity score)
                affinity_score = float(
                    np.dot(cluster_vec, dest_vec) / (cluster_norm * dest_norm + 1e-8)
                )

                # Normalize popularity score to 0-1 range
                popularity_normalized = (dest.popularity_score or 0.0) / 100.0

                # Step 5: Hybrid scoring - 70% affinity, 30% popularity
                combined_score = affinity_score * 0.7 + popularity_normalized * 0.3

                recommendations.append({
                    "destination_id": dest_id,
                    "combined_score": combined_score
                })

            # Step 6: Sort by combined score (descending) and return
            recommendations.sort(key=lambda x: x["combined_score"], reverse=True)

            # Extract destination IDs and return wrapped in schema
            destination_ids = [rec["destination_id"] for rec in recommendations[:k]]

            print(f"✅ Recommended {len(destination_ids)} destinations for user {user_id} based on cluster affinity.")
            return RecommendationDestination(recommendation=destination_ids)

        except HTTPException:
            raise
        except Exception as e:
            print(f"Error in recommend_destinations_by_cluster_affinity: {type(e).__name__}: {str(e)}")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error recommending destinations by cluster affinity: {str(e)}"
            )


