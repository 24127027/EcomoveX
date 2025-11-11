import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
from models.user import User, UserActivity, Activity

logger = logging.getLogger(__name__)

# Load the sentence transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

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
            # Create a basic embedding based on user ID if no data available
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
        
        # Get users in this cluster
        cluster_users = session.query(UserClusterAssociation).filter(
            UserClusterAssociation.cluster_id == cluster_id
        ).all()
        
        user_ids = [assoc.user_id for assoc in cluster_users]
        
        if not user_ids:
            logger.warning(f"No users found in cluster {cluster_id}")
            return []
        
        # Get activities of users in this cluster
        activities = session.query(UserActivity).filter(
            UserActivity.user_id.in_(user_ids),
            UserActivity.destination_id.isnot(None)
        ).all()
        
        # Count destination popularity
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
        
        # Calculate popularity scores
        top_destinations = []
        for dest_id, scores in destination_scores.items():
            # Weighted scoring: saves > reviews > searches
            popularity_score = (
                scores['save_count'] * 3 +
                scores['review_count'] * 2 +
                scores['search_count'] * 1
            )
            
            # Normalize to 0-100 scale
            normalized_score = min(100.0, (popularity_score / len(user_ids)) * 20)
            
            top_destinations.append({
                'destination_id': dest_id,
                'popularity_score': round(normalized_score, 2)
            })
        
        # Sort by popularity score and return top destinations
        top_destinations.sort(key=lambda x: x['popularity_score'], reverse=True)
        result = top_destinations[:limit]
        
        logger.info(f"Computed {len(result)} top destinations for cluster {cluster_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error computing top destinations for cluster {cluster_id}: {e}")
        return []