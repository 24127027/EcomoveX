from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
import hdbscan
import numpy as np
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import Activity, User, UserActivity
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
            user_result = await db.execute(select(User).where(User.id == user_id))       # wtf this violate monolith rule should be get user by id
            user = user_result.scalar_one_or_none()
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
                text_parts.append(f"user {user.username}")

            user_text = " ".join(text_parts)
            embedding = encode_text(user_text)
            return embedding

        except Exception:
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
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No users found in cluster {cluster_id}",
                )

            # Fetch activities for all users in the cluster
            activities = []
            for user_id in user_ids:
                user_activities = await UserRepository.get_user_activities(db, user_id)
                activities.extend(user_activities)

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

            for dest_id, scores in destination_scores.items():
                popularity_score = (
                    scores["save"] * 3 + scores["review"] * 2 + scores["search"] * 1
                )
                normalized_score = min(100.0, (popularity_score / len(user_ids)) * 20)
                if normalized_score > 50:
                    if (
                        await ClusterRepository.get_cluster_destination(
                            db, cluster_id, dest_id
                        )
                        is None
                    ):
                            await ClusterRepository.add_destination_to_cluster(
                                db, cluster_id, dest_id, normalized_score
                        )
                    else:
                        await ClusterRepository.update_destination_popularity(
                            db, cluster_id, dest_id, normalized_score
                        )

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
#=======================================================
        # Handle small datasets by adjusting min_cluster_size
        effective_min_size = min(min_cluster_size, max(2, len(user_embeddings) // 3))
        
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=effective_min_size,
            min_samples=1,
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
            cutoff_date = datetime.now() - timedelta(
                days=EMBEDDING_UPDATE_INTERVAL_DAYS
            )

            users_needing_update = (
                await ClusterRepository.get_users_needing_embedding_update(
                    db, cutoff_date
                )
            )

            updated_count = 0
            for user in users_needing_update:
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
            embeddings_updated = await ClusterService.update_user_embeddings(db)
            users_with_embeddings = await ClusterRepository.get_users_with_embeddings(
                db
            )
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
        
    @staticmethod
    async def update_preference(
        db: AsyncSession, user_id: int, preference_data: PreferenceUpdate
    ):
        try:
            return await ClusterRepository.update_preference(db, user_id, preference_data)
        except Exception:
            return None