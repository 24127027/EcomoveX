import logging
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from services.embedding_service import embed_user
from services.cluster_service import compute_cluster_embedding, compute_cluster_popularity
from utils.faiss_utils import search_index, is_index_ready

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Score blending utilities
# ----------------------------------------------------------------------
def blend_scores(
    similarity_items: List[Dict[str, Any]],
    popularity_items: List[Dict[str, Any]],
    similarity_weight: float = 0.7,
    popularity_weight: float = 0.3,
    k: int = 20
) -> List[Dict[str, Any]]:
    """
    Blend similarity and popularity scores with configurable weights.
    
    Args:
        similarity_items: List of items with 'destination_id' and 'similarity_score'
        popularity_items: List of items with 'destination_id' and 'popularity_score'
        similarity_weight: Weight for similarity score (0-1)
        popularity_weight: Weight for popularity score (0-1)
        k: Number of top results to return
    """
    try:
        destination_scores = {}
        
        # Add similarity scores
        for item in similarity_items:
            dest_id = item['destination_id']
            destination_scores[dest_id] = {
                'similarity': item.get('similarity_score', 0),
                'popularity': 0.0
            }
        
        # Add popularity scores
        for item in popularity_items:
            dest_id = item['destination_id']
            if dest_id not in destination_scores:
                destination_scores[dest_id] = {'similarity': 0.0, 'popularity': 0.0}
            destination_scores[dest_id]['popularity'] = item.get('popularity_score', 0)
        
        # Compute hybrid scores
        results = []
        for dest_id, scores in destination_scores.items():
            hybrid_score = (
                scores['similarity'] * similarity_weight +
                scores['popularity'] * popularity_weight
            )
            results.append({
                'destination_id': dest_id,
                'hybrid_score': round(hybrid_score, 2),
                'similarity_score': round(scores['similarity'], 2),
                'popularity_score': round(scores['popularity'], 2)
            })
        
        # Sort by hybrid score
        results.sort(key=lambda x: x['hybrid_score'], reverse=True)
        
        return results[:k]
        
    except Exception as e:
        logger.error(f"Error blending scores: {e}")
        return []

# ----------------------------------------------------------------------
# RecommendationService - To be implemented
# ----------------------------------------------------------------------
class RecommendationService:
    """Placeholder service class"""
    pass

# ----------------------------------------------------------------------
# User recommendations
# ----------------------------------------------------------------------
def recommend_for_user(
    user_id: int,
    session: Session,
    k: int = 10,
    use_hybrid: bool = False
) -> List[Dict[str, Any]]:
    """
    Generate personalized recommendations for a single user.
    
    Args:
        user_id: User ID
        session: Database session
        k: Number of recommendations
        use_hybrid: Whether to use hybrid scoring (not implemented for single user yet)
    """
    try:
        if not is_index_ready():
            logger.error("FAISS index not ready. Build index first.")
            return []
        
        # Get user embedding
        user_vector = embed_user(user_id, session)
        if not user_vector:
            logger.warning(f"Could not generate embedding for user {user_id}")
            return []
        
        # Search similar destinations
        recommendations = search_index(user_vector, k=k)
        
        logger.info(f"Generated {len(recommendations)} recommendations for user {user_id}")
        return recommendations
        
    except Exception as e:
        logger.error(f"Error recommending for user {user_id}: {e}")
        return []

# ----------------------------------------------------------------------
# Cluster recommendations
# ----------------------------------------------------------------------
def recommend_for_cluster_hybrid(
    cluster_id: int,
    session: Session,
    k: int = 20,
    similarity_weight: float = 0.7,
    popularity_weight: float = 0.3
) -> List[Dict[str, Any]]:
    """
    Hybrid recommendation combining semantic similarity and popularity for a cluster.
    
    Args:
        cluster_id: Cluster ID
        session: Database session
        k: Number of recommendations
        similarity_weight: Weight for similarity (0-1)
        popularity_weight: Weight for popularity (0-1)
    """
    try:
        if not is_index_ready():
            logger.error("FAISS index not ready. Build index first.")
            return []
        
        # Get cluster embedding
        cluster_vector = compute_cluster_embedding(cluster_id, session)
        if cluster_vector is None:
            logger.warning(f"Could not compute embedding for cluster {cluster_id}")
            return []

        # Get similarity-based recommendations
        similar_destinations = search_index(cluster_vector.tolist(), k=k*2)
        
        # Get popularity scores
        popular_destinations = compute_cluster_popularity(cluster_id, session, limit=k*2)
        
        # Blend scores
        results = blend_scores(
            similar_destinations,
            popular_destinations,
            similarity_weight,
            popularity_weight,
            k
        )
        
        logger.info(f"Generated {len(results)} hybrid recommendations for cluster {cluster_id}")
        return results

    except Exception as e:
        logger.error(f"Error in hybrid recommendation for cluster {cluster_id}: {e}")
        return []

def recommend_for_cluster_similarity(cluster_id: int, session: Session, k: int = 10) -> List[Dict[str, Any]]:
    """Pure similarity-based recommendations for a cluster."""
    try:
        if not is_index_ready():
            logger.error("FAISS index not ready. Build index first.")
            return []
        
        cluster_vector = compute_cluster_embedding(cluster_id, session)
        if cluster_vector is None:
            return []
        
        results = search_index(cluster_vector.tolist(), k=k)
        logger.info(f"Generated {len(results)} similarity-based recommendations for cluster {cluster_id}")
        return results
        
    except Exception as e:
        logger.error(f"Error in similarity recommendation for cluster {cluster_id}: {e}")
        return []

def recommend_for_cluster_popularity(cluster_id: int, session: Session, k: int = 10) -> List[Dict[str, Any]]:
    """Pure popularity-based recommendations for a cluster."""
    results = compute_cluster_popularity(cluster_id, session, limit=k)
    logger.info(f"Generated {len(results)} popularity-based recommendations for cluster {cluster_id}")
    return results
