import numpy as np
from sklearn.cluster import KMeans
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta, timezone as UTC
from typing import Dict, List, Optional
import logging
from models.user import User, UserActivity, Activity
from models.cluster import Cluster, UserClusterAssociation, ClusterDestination
from services.embedding.embedding_service import embed_user
from services.recommendation_service import (
    recommend_for_cluster_hybrid,
)

# Configuration constants
EMBEDDING_UPDATE_INTERVAL_DAYS = 7
NUM_CLUSTERS = 5

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cluster_users(user_embeddings: List[List[float]], n_clusters: int = 5) -> Dict[int, int]:
    """
    Cluster users based on their embeddings using KMeans.
    
    Args:
        user_embeddings: List of user embedding vectors
        n_clusters: Number of clusters to create
        
    Returns:
        Dictionary mapping user_id to cluster_id
    """
    if len(user_embeddings) < n_clusters:
        logger.warning(f"Only {len(user_embeddings)} users available, but {n_clusters} clusters requested. Using {len(user_embeddings)} clusters.")
        n_clusters = max(1, len(user_embeddings))
    
    # Extract embeddings and user IDs
    embeddings = []
    user_ids = []
    
    for user_id, embedding in user_embeddings:
        embeddings.append(embedding)
        user_ids.append(user_id)
    
    if not embeddings:
        return {}
    
    # Perform clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(np.array(embeddings))
    
    # Create user_id to cluster mapping
    user_cluster_mapping = {}
    for user_id, cluster_id in zip(user_ids, cluster_labels):
        user_cluster_mapping[user_id] = int(cluster_id)
    
    logger.info(f"Clustered {len(user_ids)} users into {n_clusters} clusters")
    return user_cluster_mapping

def run_user_clustering(session: Session) -> bool:
    """
    Main function to run the complete user clustering process.
    
    Args:
        session: Database session
        
    Returns:
        True if clustering was successful, False otherwise
    """
    try:
        logger.info("Starting scheduled user clustering process.")
        
        # Step 1: Find users who need embedding updates
        cutoff_date = datetime.now(UTC) - timedelta(days=EMBEDDING_UPDATE_INTERVAL_DAYS)
        
        users_needing_update = session.query(User).filter(
            or_(
                User.embedding.is_(None),
                User.last_embedding_update.is_(None),
                User.last_embedding_update < cutoff_date
            )
        ).all()
        
        logger.info(f"Found {len(users_needing_update)} users needing embedding updates")
        
        # Step 2: Generate embeddings for users who need them
        for user in users_needing_update:
            try:
                embedding = embed_user(user.id, session)
                if embedding:
                    user.embedding = embedding
                    user.last_embedding_update = datetime.now(UTC)
                    logger.info(f"Updated embedding for user {user.id}")
                else:
                    logger.warning(f"Failed to generate embedding for user {user.id}")
            except Exception as e:
                logger.error(f"Error generating embedding for user {user.id}: {e}")
        
        session.flush()
        
        # Step 3: Get all users with embeddings for clustering
        users_with_embeddings = session.query(User).filter(
            User.embedding.isnot(None)
        ).all()
        
        if not users_with_embeddings:
            logger.warning("No users with embeddings found. Skipping clustering.")
            session.commit()
            return False
        
        logger.info(f"Found {len(users_with_embeddings)} users with embeddings for clustering")
        
        # Step 4: Prepare data for clustering
        user_embeddings_data = [
            (user.id, user.embedding) for user in users_with_embeddings
        ]
        
        # Step 5: Perform clustering
        user_cluster_mapping = cluster_users(user_embeddings_data, NUM_CLUSTERS)
        
        if not user_cluster_mapping:
            logger.warning("Clustering returned no results")
            session.commit()
            return False
        
        # Step 6: Ensure clusters exist
        for cluster_id in range(NUM_CLUSTERS):
            existing_cluster = session.query(Cluster).filter_by(
                name=f"KMeans Cluster {cluster_id}",
                algorithm="KMeans"
            ).first()
            
            if not existing_cluster:
                new_cluster = Cluster(
                    name=f"KMeans Cluster {cluster_id}",
                    algorithm="KMeans"
                )
                session.add(new_cluster)
                logger.info(f"Created new cluster: KMeans Cluster {cluster_id}")
        
        session.flush()
        
        # Step 7: Clear existing user-cluster associations
        session.query(UserClusterAssociation).delete()
        
        # Step 8: Create new user-cluster associations
        cluster_objects = session.query(Cluster).filter_by(algorithm="KMeans").all()
        cluster_lookup = {
            int(cluster.name.split()[-1]): cluster.id 
            for cluster in cluster_objects
        }
        
        for user_id, cluster_id in user_cluster_mapping.items():
            if cluster_id in cluster_lookup:
                association = UserClusterAssociation(
                    user_id=user_id,
                    cluster_id=cluster_lookup[cluster_id]
                )
                session.add(association)
        
        # Step 9: Update cluster destinations
        for cluster_id in set(user_cluster_mapping.values()):
            if cluster_id in cluster_lookup:
                cluster_db_id = cluster_lookup[cluster_id]
                
                # Remove old cluster destinations
                session.query(ClusterDestination).filter_by(
                    cluster_id=cluster_db_id
                ).delete()
                
                # Compute new top destinations
                try:
                    top_destinations = recommend_for_cluster_hybrid(
                        cluster_db_id, session
                    )
                    
                    for dest_data in top_destinations:
                        cluster_dest = ClusterDestination(
                            cluster_id=cluster_db_id,
                            destination_id=dest_data["destination_id"],
                            popularity_score=dest_data["popularity_score"]
                        )
                        session.add(cluster_dest)
                        
                    logger.info(f"Updated {len(top_destinations)} destinations for cluster {cluster_id}")
                except Exception as e:
                    logger.error(f"Error computing destinations for cluster {cluster_id}: {e}")
        
        session.commit()
        logger.info("User clustering process completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error in user clustering process: {e}")
        session.rollback()
        raise
