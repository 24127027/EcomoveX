import numpy as np
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sklearn.cluster import KMeans
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from backend.schemas.cluster_schema import ClusterCreate
from models.user import Activity
from services.embedding_service import embed_user
from services.recommendation_service import recommend_for_cluster_hybrid
from repository.cluster_repository import ClusterRepository
from repository.user_repository import UserRepository

EMBEDDING_UPDATE_INTERVAL_DAYS = 7
NUM_CLUSTERS = 5

class ClusterService:
    @staticmethod
    async def compute_cluster_embedding(
        db: AsyncSession, 
        cluster_id: int
    ) -> Optional[np.ndarray]:
        try:
            user_ids = await ClusterRepository.get_users_in_cluster(db, cluster_id)
            
            if not user_ids:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No users found in cluster {cluster_id}"
                )

            user_embeddings = []
            for user_id in user_ids:
                preference = await ClusterRepository.get_preference_by_user_id(db, user_id)
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
                detail=f"Error computing cluster embedding: {e}"
            )
    
    @staticmethod
    async def compute_cluster_popularity(
        db: AsyncSession,
        cluster_id: int, 
    ):
        try:
            user_ids = await ClusterRepository.get_users_in_cluster(db, cluster_id)

            if not user_ids:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No users found in cluster {cluster_id}"
                )

            activities = await UserRepository.get_user_activities(db, user_ids)

            destination_scores = {}
            for activity in activities:
                dest_id = activity.destination_id
                if not dest_id:
                    continue
                    
                if dest_id not in destination_scores:
                    destination_scores[dest_id] = {
                        'save': 0, 
                        'search': 0, 
                        'review': 0
                    }
                
                if activity.activity == Activity.save_destination:
                    destination_scores[dest_id]['save'] += 1
                elif activity.activity == Activity.search_destination:
                    destination_scores[dest_id]['search'] += 1
                elif activity.activity == Activity.review_destination:
                    destination_scores[dest_id]['review'] += 1

            for dest_id, scores in destination_scores.items():
                popularity_score = (
                    scores['save'] * 3 + 
                    scores['review'] * 2 + 
                    scores['search'] * 1
                )
                normalized_score = min(
                    100.0, 
                    (popularity_score / len(user_ids)) * 20
                )
                if normalized_score > 50:
                    if await ClusterRepository.get_cluster_destination(db, cluster_id, dest_id) is None:
                        await ClusterRepository.add_destination_to_cluster(db, cluster_id, dest_id, normalized_score)
                    else:
                        await ClusterRepository.update_destination_popularity(db, cluster_id, dest_id, normalized_score)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error computing cluster popularity: {e}"
            )
            
    @staticmethod
    def cluster_users_kmeans(
        user_embeddings: List[Tuple[int, List[float]]], 
        n_clusters: int = 5
    ) -> Dict[int, int]:
        if len(user_embeddings) < n_clusters:
            n_clusters = max(1, len(user_embeddings))
        
        embeddings = []
        user_ids = []
        
        for user_id, embedding in user_embeddings:
            embeddings.append(embedding)
            user_ids.append(user_id)
        
        if not embeddings:
            return {}
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(np.array(embeddings))
        
        user_cluster_mapping = {}
        for user_id, cluster_id in zip(user_ids, cluster_labels):
            user_cluster_mapping[user_id] = int(cluster_id)
        
        return user_cluster_mapping
    
    @staticmethod
    async def update_user_embeddings(db: AsyncSession):
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(
                days=EMBEDDING_UPDATE_INTERVAL_DAYS
            )
            
            users_needing_update = await ClusterRepository.get_users_needing_embedding_update(db, cutoff_date)
            
            for user in users_needing_update:
                embedding = embed_user(user.id, db)
                if embedding:
                    success = await ClusterRepository.update_user_embedding(
                        db, 
                        user.id,
                        embedding, 
                        datetime.now(timezone.utc) 
                    )
                    if not success:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to update embedding for user {user.id}"
                        )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating user embeddings: {e}"
            )
    
    @staticmethod
    async def create_user_cluster_associations(
        db: AsyncSession, 
        user_cluster_mapping: Dict[int, int]
    ) -> int:
        try:
            for user_id, cluster_id in user_cluster_mapping.items():
                    association = await ClusterRepository.add_user_to_cluster(
                        db, user_id, cluster_id
                    )
                    if association:
                        await ClusterRepository.update_preference_cluster(
                            db, user_id, cluster_id
                        )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating user-cluster associations: {e}"
            )
        
    @staticmethod
    async def run_user_clustering(db: AsyncSession) -> Dict[str, Any]:
        try:
            embeddings_updated = await ClusterService.update_user_embeddings(db)            
            users_with_embeddings = await ClusterRepository.get_users_with_embeddings(db)            
            if not users_with_embeddings:
                return {
                    "success": False,
                    "message": "No users with preference embeddings found",
                    "stats": {
                        "embeddings_updated": embeddings_updated,
                        "users_clustered": 0,
                        "associations_created": 0,
                        "clusters_updated": 0
                    }
                }
            
            user_embeddings_data = []
            for user in users_with_embeddings:
                if user and user.embedding:
                    user_embeddings_data.append((user.id, user.embedding))
            
            user_cluster_mapping = ClusterService.cluster_users_kmeans(
                user_embeddings_data, NUM_CLUSTERS
            )
            
            if not user_cluster_mapping:
                return {
                    "success": False,
                    "message": "KMeans clustering failed",
                    "stats": {
                        "embeddings_updated": embeddings_updated,
                        "users_clustered": 0,
                        "associations_created": 0,
                        "clusters_updated": 0
                    }
                }
            
            cluster_counts = {}
            for cluster_id in user_cluster_mapping.values():
                cluster_counts[cluster_id] = cluster_counts.get(cluster_id, 0) + 1
            
            for cluster_id in sorted(cluster_counts.keys()):
                print(f"    - Cluster {cluster_id}: {cluster_counts[cluster_id]} users")
            
            associations_created = await ClusterService.create_user_cluster_associations(
                db, user_cluster_mapping
            )
            for cluster_id in user_cluster_mapping.values():
                await ClusterService.compute_cluster_popularity(db, cluster_id)
            
            return {
                "success": True,
                "message": "Clustering completed successfully",
                "stats": {
                    "embeddings_updated": embeddings_updated,
                    "users_clustered": len(user_cluster_mapping),
                    "associations_created": associations_created,
                    "cluster_distribution": cluster_counts
                }
            }
            
        except Exception as e:
            raise  HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error during user clustering process: {e}"
            )