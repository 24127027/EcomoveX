import numpy as np
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from utils.embedded.faiss_utils import search_index, is_index_ready
from schemas.recommendation_schema import RecommendationResponse, RecommendationScore
from fastapi import HTTPException, status
from repository.cluster_repository import ClusterRepository
from services.cluster_service import ClusterService

def blend_scores(
    similarity_items: List[Dict[str, Any]],
    popularity_items: List[Dict[str, Any]],
    similarity_weight: float = 0.7,
    popularity_weight: float = 0.3,
    k: int = 20
) -> RecommendationResponse:
    try:
        destination_scores = {}
        
        for item in similarity_items:
            dest_id = item['destination_id']
            destination_scores[dest_id] = {
                'similarity': item.get('similarity_score', 0),
                'popularity': 0.0
            }
        
        for item in popularity_items:
            dest_id = item['destination_id']
            if dest_id not in destination_scores:
                destination_scores[dest_id] = {'similarity': 0.0, 'popularity': 0.0}
            destination_scores[dest_id]['popularity'] = item.get('popularity_score', 0)
        
        results = []
        for dest_id, scores in destination_scores.items():
            hybrid_score = (
                scores['similarity'] * similarity_weight +
                scores['popularity'] * popularity_weight
            )
            results.append(RecommendationScore(
                destination_id=dest_id,
                hybrid_score=round(hybrid_score, 2),
                similarity_score=round(scores['similarity'], 2),
                popularity_score=round(scores['popularity'], 2)
            ))
        
        results.sort(key=lambda x: x.hybrid_score, reverse=True)
        
        return RecommendationResponse(recommendations=results[:k])
        
    except Exception as e:
        return RecommendationResponse(recommendations=[])

class RecommendationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        if not is_index_ready():
            raise RuntimeError("FAISS index is not available.")
    
    @staticmethod
    async def recommend_for_user(
        db: AsyncSession,
        user_id: int,
        k: int = 10,
        use_hybrid: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Generate personalized recommendations for a single user.
        """
        try:
            if not is_index_ready():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="FAISS index is not available"
                )
            
            user_vector = await ClusterService.embed_preference(db, user_id)
            if not user_vector:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Could not generate embedding for user {user_id}"
                )
            
            recommendations = search_index(user_vector, k=k)
            return recommendations
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating recommendations for user {user_id}: {str(e)}"
            )
    
    @staticmethod
    async def recommend_for_cluster_hybrid(
        db: AsyncSession,
        cluster_id: int,
        k: int = 20,
        similarity_weight: float = 0.7,
        popularity_weight: float = 0.3
    ) -> RecommendationResponse:
        """
        Hybrid recommendation combining semantic similarity and popularity for a cluster.
        """
        try:
            if not is_index_ready():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="FAISS index is not available"
                )
            
            cluster_vector = await ClusterService.compute_cluster_embedding(db, cluster_id)
            if cluster_vector is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Could not compute embedding for cluster {cluster_id}"
                )

            similar_destinations = search_index(cluster_vector.tolist(), k=k*2)
            
            await ClusterService.compute_cluster_popularity(db, cluster_id)
            
            popular_destinations_raw = await ClusterRepository.get_cluster_destinations(db, cluster_id)
            
            popular_destinations = [
                {
                    'destination_id': dest.destination_id,
                    'popularity_score': dest.popularity_score / 100.0
                }
                for dest in popular_destinations_raw
            ]
            
            results = blend_scores(
                similar_destinations,
                popular_destinations,
                similarity_weight,
                popularity_weight,
                k
            )
            
            return results

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating hybrid recommendations for cluster {cluster_id}: {str(e)}"
            )
    
    @staticmethod
    async def recommend_for_cluster_similarity(
        db: AsyncSession,
        cluster_id: int,
        k: int = 10
    ) -> List[Dict[str, Any]]:
        """Pure similarity-based recommendations for a cluster."""
        try:
            if not is_index_ready():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="FAISS index is not available"
                )
            
            cluster_vector = await ClusterService.compute_cluster_embedding(db, cluster_id)
            if cluster_vector is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Could not compute embedding for cluster {cluster_id}"
                )
            
            results = search_index(cluster_vector.tolist(), k=k)
            return results
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating similarity recommendations for cluster {cluster_id}: {str(e)}"
            )
    
    @staticmethod
    async def recommend_for_cluster_popularity(
        db: AsyncSession,
        cluster_id: int,
    ) -> List[Dict[str, Any]]:
        try:            
            await ClusterService.compute_cluster_popularity(db, cluster_id)
            
            popular_destinations_raw = await ClusterRepository.get_destinations_in_cluster(db, cluster_id)
            
            results = [
                {
                    'destination_id': dest.destination_id,
                    'popularity_score': dest.popularity_score / 100.0
                }
                for dest in popular_destinations_raw
            ]
            
            return results
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating popularity recommendations for cluster {cluster_id}: {str(e)}"
            )
    
    @staticmethod
    async def recommend_destination_based_on_user_cluster(
        db: AsyncSession,
        user_id: int,
        cluster_id: int,
        k: int = 10
    ) -> List[str]:
        try:
            if not is_index_ready():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="FAISS index is not available"
                )

            user_vector = await ClusterService.embed_preference(db, user_id)
            if user_vector is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Could not generate embedding for user {user_id}"
                )

            cluster_vector = await ClusterService.compute_cluster_embedding(db, cluster_id)
            if cluster_vector is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Could not compute embedding for cluster {cluster_id}"
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
                detail=f"Error generating recommendations for user {user_id} and cluster {cluster_id}: {str(e)}"
            )
