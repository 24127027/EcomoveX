#!/usr/bin/env python3
"""
Local testing script for user clustering functionality.
Run this script to test the clustering algorithm with real database data.
"""

import sys
import asyncio
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import sessionmaker
from database.user_database import user_engine, UserBase
from services.cluster_users import run_user_clustering
from models.user import User, UserActivity
from models.cluster import Cluster, UserClusterAssociation, ClusterDestination
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ClusteringTester:
    def __init__(self):
        self.SessionLocal = sessionmaker(bind=user_engine)
    
    async def test_clustering(self):
        """Run the complete clustering test."""
        logger.info("🚀 Starting local clustering test")
        
        # Create database session
        session = self.SessionLocal()
        
        try:
            # Display current database state
            await self.display_current_state(session)
            
            # Run clustering
            logger.info("🔄 Running user clustering...")
            success = run_user_clustering(session)
            
            if success:
                logger.info("✅ Clustering completed successfully!")
                await self.display_clustering_results(session)
            else:
                logger.error("❌ Clustering failed!")
                
        except Exception as e:
            logger.error(f"❌ Error during clustering test: {e}")
            raise
        finally:
            session.close()
    
    async def display_current_state(self, session):
        """Display current database state before clustering."""
        logger.info("📊 Current Database State:")
        
        # Count users
        user_count = session.query(User).count()
        users_with_embeddings = session.query(User).filter(User.embedding.isnot(None)).count()
        logger.info(f"   Total users: {user_count}")
        logger.info(f"   Users with embeddings: {users_with_embeddings}")
        
        # Count activities
        activity_count = session.query(UserActivity).count()
        logger.info(f"   Total user activities: {activity_count}")
        
        # Count existing clusters
        cluster_count = session.query(Cluster).count()
        association_count = session.query(UserClusterAssociation).count()
        logger.info(f"   Existing clusters: {cluster_count}")
        logger.info(f"   User-cluster associations: {association_count}")
        
        # Show sample users
        sample_users = session.query(User).limit(3).all()
        logger.info("   Sample users:")
        for user in sample_users:
            logger.info(f"     - {user.username} (ID: {user.id}, Embedding: {'✓' if user.embedding else '✗'})")
    
    async def display_clustering_results(self, session):
        """Display clustering results after completion."""
        logger.info("🎯 Clustering Results:")
        
        # Show clusters
        clusters = session.query(Cluster).all()
        for cluster in clusters:
            user_count = session.query(UserClusterAssociation).filter_by(cluster_id=cluster.id).count()
            dest_count = session.query(ClusterDestination).filter_by(cluster_id=cluster.id).count()
            logger.info(f"   {cluster.name}: {user_count} users, {dest_count} top destinations")
        
        # Show detailed cluster membership
        for cluster in clusters:
            associations = session.query(UserClusterAssociation).filter_by(cluster_id=cluster.id).all()
            if associations:
                user_ids = [assoc.user_id for assoc in associations]
                logger.info(f"   {cluster.name} members: {user_ids}")
                
                # Show top destinations for this cluster
                top_dests = session.query(ClusterDestination).filter_by(
                    cluster_id=cluster.id
                ).order_by(ClusterDestination.popularity_score.desc()).limit(3).all()
                
                if top_dests:
                    dest_info = [f"Dest{dest.destination_id}({dest.popularity_score:.1f})" for dest in top_dests]
                    logger.info(f"   {cluster.name} top destinations: {', '.join(dest_info)}")

async def main():
    """Main function to run the clustering test."""
    print("🧪 EcomoveX Clustering Local Test")
    print("=" * 50)
    
    tester = ClusteringTester()
    
    try:
        await tester.test_clustering()
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())