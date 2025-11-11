from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database.user_database import get_db
from services.cluster_users import run_user_clustering
from schemas.cluster_schema import ClusterCreate, ClusterUpdate
from models.cluster import Cluster, UserClusterAssociation, ClusterDestination
from models.user import User
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/clustering", tags=["clustering"])

@router.post("/run", summary="Trigger User Clustering")
async def trigger_clustering(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Manually trigger the user clustering process.
    This will update user embeddings and recalculate clusters.
    """
    try:
        # Run clustering in background
        background_tasks.add_task(run_clustering_task, db)
        
        return {
            "message": "Clustering process started in background",
            "status": "initiated"
        }
    except Exception as e:
        logger.error(f"Error triggering clustering: {e}")
        raise HTTPException(status_code=500, detail="Failed to start clustering process")

async def run_clustering_task(db: Session):
    """Background task to run clustering."""
    try:
        success = run_user_clustering(db)
        if success:
            logger.info("Background clustering completed successfully")
        else:
            logger.warning("Background clustering completed with warnings")
    except Exception as e:
        logger.error(f"Background clustering failed: {e}")

@router.get("/status", summary="Get Clustering Status")
async def get_clustering_status(db: Session = Depends(get_db)):
    """Get current clustering status and statistics."""
    try:
        # Count users and embeddings
        total_users = db.query(User).count()
        users_with_embeddings = db.query(User).filter(User.embedding.isnot(None)).count()
        
        # Count clusters and associations
        total_clusters = db.query(Cluster).count()
        total_associations = db.query(UserClusterAssociation).count()
        
        # Get cluster distribution
        cluster_distribution = {}
        clusters = db.query(Cluster).all()
        
        for cluster in clusters:
            user_count = db.query(UserClusterAssociation).filter_by(cluster_id=cluster.id).count()
            destination_count = db.query(ClusterDestination).filter_by(cluster_id=cluster.id).count()
            
            cluster_distribution[cluster.name] = {
                "users": user_count,
                "destinations": destination_count
            }
        
        return {
            "users": {
                "total": total_users,
                "with_embeddings": users_with_embeddings,
                "embedding_coverage": round((users_with_embeddings / total_users * 100), 2) if total_users > 0 else 0
            },
            "clusters": {
                "total": total_clusters,
                "total_associations": total_associations,
                "distribution": cluster_distribution
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting clustering status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve clustering status")

@router.get("/clusters", summary="Get All Clusters")
async def get_all_clusters(db: Session = Depends(get_db)):
    """Get all clusters with their users and destinations."""
    try:
        clusters = db.query(Cluster).all()
        result = []
        
        for cluster in clusters:
            # Get users in cluster
            associations = db.query(UserClusterAssociation).filter_by(cluster_id=cluster.id).all()
            user_ids = [assoc.user_id for assoc in associations]
            
            # Get top destinations
            destinations = db.query(ClusterDestination).filter_by(
                cluster_id=cluster.id
            ).order_by(ClusterDestination.popularity_score.desc()).all()
            
            cluster_data = {
                "id": cluster.id,
                "name": cluster.name,
                "algorithm": cluster.algorithm,
                "created_at": cluster.created_at,
                "user_count": len(user_ids),
                "user_ids": user_ids,
                "destinations": [
                    {
                        "destination_id": dest.destination_id,
                        "popularity_score": dest.popularity_score
                    }
                    for dest in destinations
                ]
            }
            result.append(cluster_data)
        
        return {"clusters": result}
        
    except Exception as e:
        logger.error(f"Error getting clusters: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve clusters")

@router.get("/user/{user_id}/cluster", summary="Get User's Cluster")
async def get_user_cluster(user_id: int, db: Session = Depends(get_db)):
    """Get the cluster assignment for a specific user."""
    try:
        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's cluster association
        association = db.query(UserClusterAssociation).filter_by(user_id=user_id).first()
        
        if not association:
            return {
                "user_id": user_id,
                "cluster": None,
                "has_embedding": user.embedding is not None,
                "message": "User not assigned to any cluster"
            }
        
        # Get cluster details
        cluster = db.query(Cluster).filter(Cluster.id == association.cluster_id).first()
        
        # Get cluster destinations
        destinations = db.query(ClusterDestination).filter_by(
            cluster_id=cluster.id
        ).order_by(ClusterDestination.popularity_score.desc()).limit(5).all()
        
        return {
            "user_id": user_id,
            "cluster": {
                "id": cluster.id,
                "name": cluster.name,
                "algorithm": cluster.algorithm
            },
            "has_embedding": user.embedding is not None,
            "recommended_destinations": [
                {
                    "destination_id": dest.destination_id,
                    "popularity_score": dest.popularity_score
                }
                for dest in destinations
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user cluster: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user cluster")

@router.delete("/reset", summary="Reset All Clustering Data")
async def reset_clustering(db: Session = Depends(get_db)):
    """Reset all clustering data (for testing purposes)."""
    try:
        # Delete all clustering data
        db.query(ClusterDestination).delete()
        db.query(UserClusterAssociation).delete()
        db.query(Cluster).delete()
        
        # Reset user embeddings
        db.query(User).update({"embedding": None, "last_embedding_update": None})
        
        db.commit()
        
        return {
            "message": "All clustering data has been reset",
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error resetting clustering data: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to reset clustering data")