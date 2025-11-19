import numpy as np
import logging
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from models.user import User, UserActivity, Activity

logger = logging.getLogger(__name__)

# Fix PyTorch compatibility issue BEFORE importing sentence_transformers
def patch_torch_compatibility():
    """Patch torch.utils._pytree for compatibility with older transformers versions."""
    try:
        import torch.utils._pytree as pytree
        import sys
        
        # Check if patch is needed
        if not hasattr(pytree, 'register_pytree_node'):
            if hasattr(pytree, '_register_pytree_node'):
                # Create the missing function as an alias
                pytree.register_pytree_node = pytree._register_pytree_node
                logger.info("✓ Applied PyTorch pytree compatibility patch")
            else:
                logger.warning("⚠ Cannot find _register_pytree_node, patch may not work")
        
        # Also patch transformers.utils.generic if needed
        if 'transformers' not in sys.modules:
            # Monkey-patch before transformers loads
            import importlib.util
            spec = importlib.util.find_spec('transformers')
            if spec:
                # Pre-patch the module namespace
                logger.info("✓ Pre-patching transformers namespace")
    except Exception as e:
        logger.warning(f"⚠ Could not apply torch patch: {e}")

# Apply patch immediately
patch_torch_compatibility()

# Now safe to import sentence_transformers
try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    logger.info("✓ SentenceTransformer model loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load SentenceTransformer: {e}")
    # Fallback: create a dummy model that returns random embeddings
    class DummyModel:
        def encode(self, text):
            return np.random.randn(384)  # MiniLM-L6-v2 has 384 dimensions
    model = DummyModel()
    logger.warning("⚠ Using dummy model for embeddings")

def embed_user(user_id: int, session: Session) -> Optional[List[float]]:
    """
    Generate embedding for a user based on their preferences and activity.
    
    Args:
        user_id: ID of the user to generate embedding for
        session: Database session
        
    Returns:
        User embedding as a list of floats, or None if insufficient data
    """
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User {user_id} not found")
            return None
        
        # Collect user preference data
        user_text_data = []
        
        # Add user preferences
        if user.temp_min is not None and user.temp_max is not None:
            user_text_data.append(f"prefers temperature between {user.temp_min} and {user.temp_max} degrees")
        
        if user.budget_min is not None and user.budget_max is not None:
            user_text_data.append(f"budget range {user.budget_min} to {user.budget_max}")
        
        # Add user activity patterns
        activities = session.query(UserActivity).filter(
            UserActivity.user_id == user_id
        ).all()
        
        activity_counts = {}
        for activity in activities:
            activity_type = activity.activity.value
            activity_counts[activity_type] = activity_counts.get(activity_type, 0) + 1
        
        for activity_type, count in activity_counts.items():
            user_text_data.append(f"{activity_type} {count} times")
        
        # Add eco point information
        if user.eco_point and user.eco_point > 0:
            user_text_data.append(f"eco-conscious with {user.eco_point} eco points")
        
        # Add rank information
        if user.rank:
            user_text_data.append(f"travel experience level {user.rank.value}")
        
        if not user_text_data:
            user_text_data.append(f"user {user.username}")
        
        # Combine all text data
        user_text = " ".join(user_text_data)
        
        # Generate embedding
        embedding = model.encode(user_text).tolist()
        
        logger.info(f"Generated embedding for user {user_id} with {len(user_text_data)} features")
        return embedding
        
    except Exception as e:
        logger.error(f"Error generating embedding for user {user_id}: {e}")
        return None

def embed_destination(destination_data: Dict[str, Any]) -> List[float]:
    """
    Generate embedding for a destination.
    
    Args:
        destination_data: Dictionary containing destination information
        
    Returns:
        Destination embedding as a list of floats
    """
    text_parts = []
    
    if 'name' in destination_data:
        text_parts.append(destination_data['name'])
    
    if 'tags' in destination_data:
        if isinstance(destination_data['tags'], list):
            text_parts.extend(destination_data['tags'])
        else:
            text_parts.append(str(destination_data['tags']))
    
    if 'description' in destination_data:
        text_parts.append(destination_data['description'])
    
    text = " ".join(text_parts) if text_parts else "destination"
    return model.encode(text).tolist()

def compute_top_destinations_for_cluster(cluster_id: int, session: Session, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Compute top destinations for a cluster based on user activities.
    
    Args:
        cluster_id: ID of the cluster
        session: Database session
        limit: Maximum number of destinations to return
        
    Returns:
        List of dictionaries with destination_id and popularity_score
    """
    try:
        from models.cluster import UserClusterAssociation
        
        cluster_users = session.query(UserClusterAssociation).filter(
            UserClusterAssociation.cluster_id == cluster_id
        ).all()
        
        user_ids = [assoc.user_id for assoc in cluster_users]
        
        if not user_ids:
            logger.warning(f"No users found in cluster {cluster_id}")
            return []
        
        activities = session.query(UserActivity).filter(
            UserActivity.user_id.in_(user_ids),
            UserActivity.destination_id.isnot(None)
        ).all()
        
        destination_scores = {}
        for activity in activities:
            dest_id = activity.destination_id
            if dest_id not in destination_scores:
                destination_scores[dest_id] = {
                    'save_count': 0,
                    'search_count': 0,
                    'review_count': 0
                }
            
            if activity.activity == Activity.save_destination:
                destination_scores[dest_id]['save_count'] += 1
            elif activity.activity == Activity.search_destination:
                destination_scores[dest_id]['search_count'] += 1
            elif activity.activity == Activity.review_destination:
                destination_scores[dest_id]['review_count'] += 1
        
        top_destinations = []
        for dest_id, scores in destination_scores.items():
            popularity_score = (
                scores['save_count'] * 3 +
                scores['review_count'] * 2 +
                scores['search_count'] * 1
            )
            
            normalized_score = min(100.0, (popularity_score / len(user_ids)) * 20)
            
            top_destinations.append({
                'destination_id': dest_id,
                'popularity_score': round(normalized_score, 2)
            })
        
        top_destinations.sort(key=lambda x: x['popularity_score'], reverse=True)
        result = top_destinations[:limit]
        
        logger.info(f"Computed {len(result)} top destinations for cluster {cluster_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error computing top destinations for cluster {cluster_id}: {e}")
        return []