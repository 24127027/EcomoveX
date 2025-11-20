import numpy as np
import logging
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from models.user import User, UserActivity, Activity
from models.cluster import Cluster, UserClusterAssociation
from services.embedding_service import embed_user

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# User-Cluster assignment
# ----------------------------------------------------------------------
def assign_user_to_cluster(user_id: int, cluster_id: int, session: Session) -> bool:
    """Assign a user to a cluster."""
    try:
        # Check if association already exists
        existing = session.query(UserClusterAssociation).filter(
            UserClusterAssociation.user_id == user_id,
            UserClusterAssociation.cluster_id == cluster_id
        ).first()
        
        if existing:
            logger.info(f"User {user_id} already in cluster {cluster_id}")
            return True
        
        # Create new association
        association = UserClusterAssociation(user_id=user_id, cluster_id=cluster_id)
        session.add(association)
        session.commit()
        logger.info(f"Assigned user {user_id} to cluster {cluster_id}")
        return True
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error assigning user {user_id} to cluster {cluster_id}: {e}")
        return False

def remove_user_from_cluster(user_id: int, cluster_id: int, session: Session) -> bool:
    """Remove a user from a cluster."""
    try:
        association = session.query(UserClusterAssociation).filter(
            UserClusterAssociation.user_id == user_id,
            UserClusterAssociation.cluster_id == cluster_id
        ).first()
        
        if association:
            session.delete(association)
            session.commit()
            logger.info(f"Removed user {user_id} from cluster {cluster_id}")
            return True
        
        logger.warning(f"User {user_id} not in cluster {cluster_id}")
        return False
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error removing user {user_id} from cluster {cluster_id}: {e}")
        return False

# ----------------------------------------------------------------------
# Load cluster data
# ----------------------------------------------------------------------
def load_cluster_users(cluster_id: int, session: Session) -> List[int]:
    """Load all user IDs in a cluster."""
    try:
        associations = session.query(UserClusterAssociation).filter(
            UserClusterAssociation.cluster_id == cluster_id
        ).all()
        
        user_ids = [assoc.user_id for assoc in associations]
        logger.info(f"Loaded {len(user_ids)} users from cluster {cluster_id}")
        return user_ids
        
    except Exception as e:
        logger.error(f"Error loading users from cluster {cluster_id}: {e}")
        return []

def load_cluster_info(cluster_id: int, session: Session) -> Optional[Dict[str, Any]]:
    """Load cluster information."""
    try:
        cluster = session.query(Cluster).filter(Cluster.id == cluster_id).first()
        if not cluster:
            logger.warning(f"Cluster {cluster_id} not found")
            return None
        
        user_ids = load_cluster_users(cluster_id, session)
        
        return {
            'id': cluster.id,
            'name': cluster.name,
            'algorithm': cluster.algorithm,
            'user_count': len(user_ids),
            'user_ids': user_ids
        }
        
    except Exception as e:
        logger.error(f"Error loading cluster info for {cluster_id}: {e}")
        return None

# ----------------------------------------------------------------------
# Cluster embedding
# ----------------------------------------------------------------------
def compute_cluster_embedding(cluster_id: int, session: Session) -> Optional[np.ndarray]:
    """Compute average embedding for a cluster from all user embeddings."""
    try:
        user_ids = load_cluster_users(cluster_id, session)
        
        if not user_ids:
            logger.warning(f"No users found in cluster {cluster_id}")
            return None

        # Generate embeddings for all users
        user_embeddings = []
        for user_id in user_ids:
            embedding = embed_user(user_id, session)
            if embedding:
                user_embeddings.append(np.array(embedding))

        if not user_embeddings:
            logger.warning(f"No valid embeddings for cluster {cluster_id}")
            return None

        # Compute centroid (average)
        cluster_vector = np.mean(user_embeddings, axis=0)
        logger.info(f"Computed cluster embedding for cluster {cluster_id} from {len(user_embeddings)} users")
        
        return cluster_vector

    except Exception as e:
        logger.error(f"Error computing cluster embedding for cluster {cluster_id}: {e}")
        return None

# ----------------------------------------------------------------------
# Cluster popularity scoring
# ----------------------------------------------------------------------
def compute_cluster_popularity(cluster_id: int, session: Session, limit: int = 20) -> List[Dict[str, Any]]:
    """Compute top destinations for a cluster based on user activities."""
    try:
        user_ids = load_cluster_users(cluster_id, session)

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
                destination_scores[dest_id] = {'save': 0, 'search': 0, 'review': 0}
            
            if activity.activity == Activity.save_destination:
                destination_scores[dest_id]['save'] += 1
            elif activity.activity == Activity.search_destination:
                destination_scores[dest_id]['search'] += 1
            elif activity.activity == Activity.review_destination:
                destination_scores[dest_id]['review'] += 1

        # Calculate popularity scores
        top_destinations = []
        for dest_id, scores in destination_scores.items():
            # Weighted scoring: save=3, review=2, search=1
            popularity_score = scores['save'] * 3 + scores['review'] * 2 + scores['search'] * 1
            # Normalize by number of users (scale to 0-100)
            normalized_score = min(100.0, (popularity_score / len(user_ids)) * 20)
            
            top_destinations.append({
                'destination_id': dest_id,
                'popularity_score': round(normalized_score, 2),
                'save_count': scores['save'],
                'review_count': scores['review'],
                'search_count': scores['search']
            })

        # Sort by popularity
        top_destinations.sort(key=lambda x: x['popularity_score'], reverse=True)
        result = top_destinations[:limit]
        
        logger.info(f"Computed {len(result)} top destinations for cluster {cluster_id}")
        return result

    except Exception as e:
        logger.error(f"Error computing cluster popularity for {cluster_id}: {e}")
        return []