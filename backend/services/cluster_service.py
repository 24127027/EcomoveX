from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
import hdbscan
import numpy as np
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.user_service import UserService
from models.user import Activity, UserActivity
from repository.cluster_repository import ClusterRepository
from repository.user_repository import UserRepository
from schemas.cluster_schema import (
    ClusteringResultResponse,
    ClusteringStats,
)
from schemas.cluster_schema import PreferenceUpdate
from utils.embedded.embedding_utils import encode_text

EMBEDDING_UPDATE_INTERVAL_DAYS = 7
MIN_CLUSTER_SIZE = 2  # Minimum users per cluster for HDBSCAN


class ClusterService:
    @staticmethod
    async def compute_cluster_embedding( # tính toán vector trung bình của cụm
        db: AsyncSession, cluster_id: int
    ) -> Optional[np.ndarray]:
        try:
            user_ids = await ClusterRepository.get_users_in_cluster(db, cluster_id)

            if not user_ids:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No users found in cluster {cluster_id}",
                )

            user_embeddings = []
            for user_id in user_ids:
                preference = await ClusterRepository.get_preference_by_user_id(
                    db, user_id
                )
                if preference and preference.embedding:
                    user_embeddings.append(np.array(preference.embedding))

            if not user_embeddings:
                return None

            cluster_vector = np.mean(user_embeddings, axis=0)
            return cluster_vector

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error computing cluster embedding: {e}",
            )

    @staticmethod
    async def embed_preference(db: AsyncSession, user_id: int) -> Optional[List[float]]: # tạo embedding từ sở thích người dùng
        try:
            user = await UserService.get_user_by_id(db, user_id)
            if not user:
                return None

            text_parts = []

            preference = await ClusterRepository.get_preference_by_user_id(db, user_id)
            if preference:
                if preference.weather_pref:
                    weather = preference.weather_pref
                    if "min_temp" in weather and "max_temp" in weather:
                        text_parts.append(
                            f"prefers temperature between {weather['min_temp']} "
                            f"and {weather['max_temp']} degrees"
                        )

                if preference.budget_range:
                    budget = preference.budget_range
                    if "min" in budget and "max" in budget:
                        text_parts.append(
                            f"budget range {budget['min']} to {budget['max']}"
                        )

                if preference.attraction_types:
                    text_parts.append(
                        f"interested in {', '.join(preference.attraction_types)}"
                    )

                if preference.kids_friendly:
                    text_parts.append("prefers kid-friendly destinations")

            activities_result = await db.execute(
                select(UserActivity).where(UserActivity.user_id == user_id)
            )
            activities = activities_result.scalars().all()

            activity_counts = {}
            for activity in activities:
                activity_type = activity.activity.value
                activity_counts[activity_type] = (
                    activity_counts.get(activity_type, 0) + 1
                )
            for act, count in activity_counts.items():
                text_parts.append(f"{act} {count} times")

            if user.eco_point and user.eco_point > 0:
                text_parts.append(f"eco-conscious with {user.eco_point} eco points")
            if user.rank:
                text_parts.append(f"travel experience level {user.rank.value}")

            if not text_parts:
                # Default embedding for new users with no data
                text_parts.append("new traveler interested in exploring destinations")

            user_text = " ".join(text_parts)
            print(f"🔤 Generating embedding for user {user_id}: '{user_text[:100]}...'")
            embedding = encode_text(user_text)
            if embedding:
                print(f"✅ Generated embedding with {len(embedding)} dimensions for user {user_id}")
            else:
                print(f"❌ Failed to generate embedding for user {user_id}")
            return embedding

        except Exception as e:
            print(f"❌ Error in embed_preference for user {user_id}: {e}")

            return None

    @staticmethod
    async def save_preference_embedding(
        db: AsyncSession, user_id: int, embedding: List[float]
    ) -> bool:
        try:
            return await ClusterRepository.update_user_embedding(db, user_id, embedding)
        except Exception:
            return False

    @staticmethod
    async def get_preference(db: AsyncSession, user_id: int):
        try:
            return await ClusterRepository.get_preference_by_user_id(db, user_id)
        except Exception:
            return None

    @staticmethod
    async def get_users_with_embeddings(db: AsyncSession):
        try:
            return await ClusterRepository.get_users_with_embeddings(db)
        except Exception:
            return []

    @staticmethod
    async def get_users_needing_embedding_update(
        db: AsyncSession, cutoff_date: datetime
    ):
        try:
            return await ClusterRepository.get_users_needing_embedding_update(
                db, cutoff_date
            )
        except Exception:
            return []

    @staticmethod
    async def compute_cluster_popularity(        # tính toán điểm phổ biến của cụm
        db: AsyncSession,
        cluster_id: int,
    ):
        try:
            user_ids = await ClusterRepository.get_users_in_cluster(db, cluster_id)

            if not user_ids:
                print(f"⚠️ No users found in cluster {cluster_id}, skipping popularity computation")
                return

            # Fetch activities for all users in the cluster
            activities = []
            for user_id in user_ids:
                user_activities = await UserRepository.get_user_activities(db, user_id)
                activities.extend(user_activities)

            print(f"📊 Cluster {cluster_id}: {len(user_ids)} users, {len(activities)} total activities")

            if not activities:
                print(f"⚠️ No activities found for cluster {cluster_id}")
                return

            destination_scores = {}
            for activity in activities:
                dest_id = activity.destination_id
                if not dest_id:
                    continue

                if dest_id not in destination_scores:
                    destination_scores[dest_id] = {"save": 0, "search": 0, "review": 0}

                if activity.activity == Activity.save_destination:
                    destination_scores[dest_id]["save"] += 1
                elif activity.activity == Activity.search_destination:
                    destination_scores[dest_id]["search"] += 1
                elif activity.activity == Activity.review_destination:
                    destination_scores[dest_id]["review"] += 1

            print(f"📍 Cluster {cluster_id}: Found {len(destination_scores)} unique destinations from activities")

            destinations_added = 0
            for dest_id, scores in destination_scores.items():
                popularity_score = (
                    scores["save"] * 3 + scores["review"] * 2 + scores["search"] * 1
                )
                # Lower threshold and adjust normalization for small datasets
                # Minimum score of 1 activity = 1 point, normalize to at least get some destinations
                normalized_score = min(100.0, max(10.0, (popularity_score / len(user_ids)) * 20))
                
                # Lower threshold to 10 to include destinations with at least 1 activity
                if normalized_score >= 10:
                    if (
                        await ClusterRepository.get_cluster_destination(
                            db, cluster_id, dest_id
                        )
                        is None
                    ):
                        await ClusterRepository.add_destination_to_cluster(
                            db, cluster_id, dest_id, normalized_score
                        )
                        destinations_added += 1
                    else:
                        await ClusterRepository.update_destination_popularity(
                            db, cluster_id, dest_id, normalized_score
                        )

            print(f"✅ Cluster {cluster_id}: Added/updated {destinations_added} destinations")

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error computing cluster popularity: {e}",
            )

    @staticmethod
    def cluster_users_hdbscan(
        user_embeddings: List[Tuple[int, List[float]]], min_cluster_size: int = 2
    ) -> Dict[int, int]:
        #=======================================================
        #=======================================================
        embeddings = []
        user_ids = []

        for user_id, embedding in user_embeddings:
            embeddings.append(embedding)
            user_ids.append(user_id)

        if not embeddings:
            return {}

        # Handle very small datasets - HDBSCAN requires at least 2 points
        # and min_samples must be <= number of points
        num_points = len(embeddings)
        if num_points < 2:
            # Single user case: assign to cluster 0
            return {user_ids[0]: 0} if user_ids else {}

#=======================================================
        # Handle small datasets by adjusting min_cluster_size
        effective_min_size = min(min_cluster_size, max(2, num_points // 3))
        # Ensure min_samples doesn't exceed the number of points
        effective_min_samples = min(1, num_points - 1) if num_points > 1 else 1

        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=effective_min_size,
            min_samples=effective_min_samples,
            metric='euclidean',
            cluster_selection_method='eom'
        )
        cluster_labels = clusterer.fit_predict(np.array(embeddings))

        # Handle noise points (label -1) by assigning them to nearest cluster
        unique_labels = set(cluster_labels)
        if -1 in unique_labels:
            unique_labels.remove(-1)

        # If all points are noise or no clusters formed, create one cluster
        if len(unique_labels) == 0:
            cluster_labels = np.zeros(len(cluster_labels), dtype=int)
        else:
            # Assign noise points to the largest cluster
            noise_indices = np.where(cluster_labels == -1)[0]
            if len(noise_indices) > 0:
                # Find the most common cluster
                valid_labels = cluster_labels[cluster_labels != -1]
                if len(valid_labels) > 0:
                    largest_cluster = np.bincount(valid_labels).argmax()
                    cluster_labels[noise_indices] = largest_cluster

        # Remap cluster IDs to be continuous starting from 0
        unique_clusters = sorted(set(cluster_labels))
        cluster_mapping = {old_id: new_id for new_id, old_id in enumerate(unique_clusters)}
        remapped_labels = np.array([cluster_mapping[label] for label in cluster_labels])
#=======================================================
        user_cluster_mapping = {}
        #=======================================================
        for user_id, cluster_id in zip(user_ids, remapped_labels):
            user_cluster_mapping[user_id] = int(cluster_id)

        return user_cluster_mapping

    @staticmethod
    async def update_user_embeddings(db: AsyncSession) -> int:
        try:
            # Use timezone-naive datetime to match the database column type (TIMESTAMP WITHOUT TIME ZONE)
            cutoff_date = datetime.utcnow() - timedelta(
                days=EMBEDDING_UPDATE_INTERVAL_DAYS
            )

            users_needing_update = (
                await ClusterRepository.get_users_needing_embedding_update(
                    db, cutoff_date
                )
            )

            # Debug: Log user IDs needing update
            user_ids_needing_update = [u.id for u in users_needing_update]
            print(f"📋 User IDs needing update: {user_ids_needing_update[:10]}...{user_ids_needing_update[-5:] if len(user_ids_needing_update) > 10 else ''}")

            updated_count = 0
            skipped_users = []
            for user in users_needing_update:
                # Check if user has a preference record first
                pref = await ClusterRepository.get_preference_by_user_id(db, user.id)
                if not pref:
                    skipped_users.append(user.id)
                    print(f"⚠️ User {user.id} has no preference record, skipping")
                    continue

                embedding = await ClusterService.embed_preference(db, user.id)
                if embedding:
                    success = await ClusterService.save_preference_embedding(
                        db, user.id, embedding
                    )
                    if success:
                        updated_count += 1
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to update embedding for user {user.id}",
                        )
                else:
                    print(f"⚠️ Failed to generate embedding for user {user.id}")

            if skipped_users:
                print(f"⚠️ Skipped {len(skipped_users)} users without preferences: {skipped_users[:10]}")

            return updated_count
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating user embeddings: {e}",
            )

    @staticmethod
    async def create_user_cluster_associations( #hàm này tạo liên kết người dùng-cụm
        db: AsyncSession, user_cluster_mapping: Dict[int, int]
    ) -> int:
        try:
            created_count = 0
            failed_users = []

            for user_id, cluster_id in user_cluster_mapping.items():
                try:
                    association = await ClusterRepository.add_user_to_cluster(
                        db, user_id, cluster_id
                    )
                    if association:
                        created_count += 1
                        await ClusterRepository.update_preference_cluster(
                            db, user_id, cluster_id
                        )
                    else:
                        failed_users.append(user_id)
                        print(f"WARNING: Failed to create association for user_id={user_id}")
                except Exception as inner_e:
                    failed_users.append(user_id)
                    print(f"ERROR: Failed to assign user_id={user_id} to cluster_id={cluster_id}: {inner_e}")
                    await db.rollback()

            if failed_users:
                print(f"WARNING: Failed to assign {len(failed_users)} users: {failed_users}")

            return created_count
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating user-cluster associations: {e}",
            )

    @staticmethod
    async def run_user_clustering(db: AsyncSession) -> ClusteringResultResponse: # hàm chính để chạy quá trình phân cụm người dùng
        try:
            print("🔄 Starting clustering: updating user embeddings...")
            embeddings_updated = await ClusterService.update_user_embeddings(db)
            print(f"✅ Updated {embeddings_updated} user embeddings")

            users_with_embeddings = await ClusterRepository.get_users_with_embeddings(
                db
            )
            
            # Force generate embeddings for users with preferences but no embedding
            all_preferences = await ClusterRepository.get_all_preferences(db)
            users_missing_embeddings = [
                pref for pref in all_preferences 
                if pref.embedding is None
            ]
            
            if users_missing_embeddings:
                print(f"🔧 Force generating embeddings for {len(users_missing_embeddings)} users with missing embeddings...")
                for pref in users_missing_embeddings:
                    try:
                        embedding = await ClusterService.embed_preference(db, pref.user_id)
                        if embedding:
                            success = await ClusterService.save_preference_embedding(
                                db, pref.user_id, embedding
                            )
                            if success:
                                embeddings_updated += 1
                                print(f"  ✅ Generated embedding for user {pref.user_id}")
                            else:
                                print(f"  ❌ Failed to save embedding for user {pref.user_id}")
                        else:
                            print(f"  ❌ Failed to generate embedding for user {pref.user_id}")
                    except Exception as e:
                        print(f"  ❌ Error generating embedding for user {pref.user_id}: {e}")
                
                # Refresh the list after generating embeddings
                users_with_embeddings = await ClusterRepository.get_users_with_embeddings(db)

            if not users_with_embeddings:
                return ClusteringResultResponse(
                    success=False,
                    message="No users with preference embeddings found",
                    stats=ClusteringStats(
                        embeddings_updated=embeddings_updated,
                        users_clustered=0,
                        associations_created=0,
                        clusters_updated=0,
                    ),
                )

            print(f"📊 Found {len(users_with_embeddings)} users with embeddings")

            # Validate that user IDs actually exist in the database
            user_embeddings_data = []
            valid_user_ids = set()

            for pref in users_with_embeddings:
                if pref and pref.embedding and pref.user_id:
                    # Verify user still exists
                    user_exists = await UserRepository.get_user_by_id(db, pref.user_id)
                    if user_exists:
                        user_embeddings_data.append((pref.user_id, pref.embedding))
                        valid_user_ids.add(pref.user_id)
                    else:
                        print(f"WARNING: Preference exists for non-existent user_id={pref.user_id}")
                else:
                    if pref and pref.user_id:
                        print(f"⚠️ User {pref.user_id} has preference but no embedding")

            if not user_embeddings_data:
                return ClusteringResultResponse(
                    success=False,
                    message="No valid users with embeddings found",
                    stats=ClusteringStats(
                        embeddings_updated=embeddings_updated,
                        users_clustered=0,
                        associations_created=0,
                        clusters_updated=0,
                    ),
                )

            user_cluster_mapping = ClusterService.cluster_users_hdbscan(
                user_embeddings_data, MIN_CLUSTER_SIZE
            )

            if not user_cluster_mapping:
                return ClusteringResultResponse(
                    success=False,
                    message="HDBSCAN clustering failed",
                    stats=ClusteringStats(
                        embeddings_updated=embeddings_updated,
                        users_clustered=0,
                        associations_created=0,
                        clusters_updated=0,
                    ),
                )

            cluster_counts = {}
            for cluster_id in user_cluster_mapping.values():
                cluster_counts[cluster_id] = cluster_counts.get(cluster_id, 0) + 1
#==========================================================================================
            # First, ensure cluster records exist in database
            for cluster_id in sorted(cluster_counts.keys()):
                print(f"    - Cluster {cluster_id}: {cluster_counts[cluster_id]} users")

                # Check if cluster exists, create if not
                existing_cluster = await ClusterRepository.get_cluster_by_id(db, cluster_id + 1)
                if not existing_cluster:
                    from schemas.cluster_schema import ClusterCreate
                    cluster_data = ClusterCreate(
                        name=f"Cluster {cluster_id + 1}",
                        algorithm="HDBSCAN",
                        description=f"Auto-generated cluster with {cluster_counts[cluster_id]} users"
                    )
                    await ClusterRepository.create_cluster(db, cluster_data)

            # Remap cluster IDs from 0-based to 1-based (database IDs start at 1)
            adjusted_mapping = {user_id: cluster_id + 1 for user_id, cluster_id in user_cluster_mapping.items()}

#==========================================================================================
            associations_created = (
                await ClusterService.create_user_cluster_associations(
                    db, adjusted_mapping
                )
            )
            #==========================================================================================
            # Compute popularity for adjusted cluster IDs
            popularity_errors = 0
            for cluster_id in set(adjusted_mapping.values()):
                try:
                    await ClusterService.compute_cluster_popularity(db, cluster_id)
                except Exception as pop_error:
                    popularity_errors += 1
                    print(f"ERROR: Failed to compute popularity for cluster_id={cluster_id}: {pop_error}")

            if popularity_errors > 0:
                print(f"WARNING: Failed to compute popularity for {popularity_errors} clusters")
#==========================================================================================
            return ClusteringResultResponse(
                success=True,
                message="Clustering completed successfully",
                stats=ClusteringStats(
                    embeddings_updated=embeddings_updated,
                    users_clustered=len(user_cluster_mapping),
                    associations_created=associations_created,
                    clusters_updated=len(cluster_counts),
                ),
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error during user clustering process: {e}",
            )

    @staticmethod
    async def assign_new_user_to_cluster(db: AsyncSession, user_id: int) -> bool:
        """
        Assign a newly registered user to the most similar existing cluster
        based on their preference embedding. If no clusters exist, create a default one.
        
        Returns True if assignment succeeded, False otherwise.
        """
        try:
            print(f"🔄 Assigning cluster for new user {user_id}...")
            
            # Generate embedding for the new user
            embedding = await ClusterService.embed_preference(db, user_id)
            if not embedding:
                print(f"⚠️ Could not generate embedding for user {user_id}")
                return False
            
            # Save the embedding
            await ClusterService.save_preference_embedding(db, user_id, embedding)
            
            # Get all existing clusters
            existing_clusters = await ClusterRepository.get_all_clusters(db)
            
            if not existing_clusters:
                # No clusters exist yet - create default cluster and assign user
                from schemas.cluster_schema import ClusterCreate
                cluster_data = ClusterCreate(
                    name="Cluster 1",
                    algorithm="HDBSCAN",
                    description="Default cluster for first users"
                )
                new_cluster = await ClusterRepository.create_cluster(db, cluster_data)
                cluster_id = new_cluster.id
                print(f"✅ Created new default cluster {cluster_id} for first user")
            else:
                # Find the most similar cluster
                user_embedding = np.array(embedding)
                best_cluster_id = None
                min_distance = float('inf')
                
                for cluster in existing_clusters:
                    # Compute cluster centroid
                    cluster_embedding = await ClusterService.compute_cluster_embedding(db, cluster.id)
                    if cluster_embedding is not None:
                        # Calculate Euclidean distance
                        distance = np.linalg.norm(user_embedding - cluster_embedding)
                        if distance < min_distance:
                            min_distance = distance
                            best_cluster_id = cluster.id
                
                if best_cluster_id is None:
                    # Fallback: assign to first cluster
                    best_cluster_id = existing_clusters[0].id
                    print(f"⚠️ Could not compute cluster similarities, assigning to cluster {best_cluster_id}")
                else:
                    print(f"✅ User {user_id} assigned to cluster {best_cluster_id} (distance: {min_distance:.4f})")
                
                cluster_id = best_cluster_id
            
            # Create user-cluster association
            await ClusterRepository.add_user_to_cluster(db, user_id, cluster_id)
            
            # Update cluster popularity
            try:
                await ClusterService.compute_cluster_popularity(db, cluster_id)
            except Exception as pop_error:
                print(f"⚠️ Warning: Failed to update cluster popularity: {pop_error}")
            
            print(f"✅ Successfully assigned user {user_id} to cluster {cluster_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error assigning cluster to user {user_id}: {e}")
            return False

    @staticmethod
    async def get_preference_by_user_id(db: AsyncSession, user_id: int):
        try:
            return await ClusterRepository.get_preference_by_user_id(db, user_id)
        except Exception:
            return None

    @staticmethod
    async def is_user_have_preference(db: AsyncSession, user_id: int) -> bool:
        try:
            preference = await ClusterRepository.get_preference_by_user_id(db, user_id)
            # check nếu mọi field trừ user_id đều None
            if preference.weather_pref is None and preference.attraction_types is None and \
                preference.budget_range is None and preference.kids_friendly is False:
                return False
            return True
        except Exception:
            return False

    # Conversion mappings for preference data
    CLIMATE_TO_TEMP = {
        "warm": {"min_temp": 25, "max_temp": 35},
        "cool": {"min_temp": 15, "max_temp": 25},
        "cold": {"min_temp": 0, "max_temp": 15},
        "any": {"min_temp": 0, "max_temp": 40}
    }

    BUDGET_TO_RANGE = {
        "low": {"min": 0.0, "max": 500000.0},
        "mid": {"min": 500000.0, "max": 2000000.0},
        "luxury": {"min": 2000000.0, "max": 10000000.0}
    }

    # Default values
    DEFAULT_CLIMATE = "any"
    DEFAULT_BUDGET_LEVEL = "mid"
    DEFAULT_ATTRACTION_TYPES = ["nature", "culture", "entertainment"]
    DEFAULT_KIDS_FRIENDLY = False

    @staticmethod
    def _convert_preference_data(raw_data: Optional[Dict]) -> PreferenceUpdate:
        """Convert frontend format to backend format with default fallbacks."""
        if raw_data is None:
            raw_data = {}

        # Weather preference with fallback
        climate = ClusterService.DEFAULT_CLIMATE
        if raw_data.get("weather_pref"):
            climate = raw_data["weather_pref"].get("climate", ClusterService.DEFAULT_CLIMATE)
        weather_pref = ClusterService.CLIMATE_TO_TEMP.get(
            climate, ClusterService.CLIMATE_TO_TEMP[ClusterService.DEFAULT_CLIMATE]
        )

        # Budget range with fallback
        level = ClusterService.DEFAULT_BUDGET_LEVEL
        if raw_data.get("budget_range"):
            level = raw_data["budget_range"].get("level", ClusterService.DEFAULT_BUDGET_LEVEL)
        budget_range = ClusterService.BUDGET_TO_RANGE.get(
            level, ClusterService.BUDGET_TO_RANGE[ClusterService.DEFAULT_BUDGET_LEVEL]
        )

        # Attraction types with fallback
        attraction_types = raw_data.get("attraction_types") or ClusterService.DEFAULT_ATTRACTION_TYPES

        # Kids friendly with fallback
        kids_friendly = raw_data.get("kids_friendly", ClusterService.DEFAULT_KIDS_FRIENDLY)

        return PreferenceUpdate(
            weather_pref=weather_pref,
            attraction_types=attraction_types,
            budget_range=budget_range,
            kids_friendly=kids_friendly
        )

    @staticmethod
    async def update_preference(
        db: AsyncSession, user_id: int, raw_data: Optional[Dict] = None
    ):
        try:
            preference_data = ClusterService._convert_preference_data(raw_data)
            return await ClusterRepository.update_preference(db, user_id, preference_data)
        except Exception:
            return None
