#!/usr/bin/env python3
"""
Command-line interface for clustering operations.
"""

import click
import sys
import asyncio
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import sessionmaker
from database.user_database import user_engine
from services.cluster_users import run_user_clustering
from scripts.generate_sample_data import SampleDataGenerator
from scripts.test_clustering_local import ClusteringTester
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.group()
def cli():
    """EcomoveX Clustering CLI Tool"""
    pass

@cli.command()
@click.option('--count', default=25, help='Number of sample users to generate')
def generate_data(count):
    """Generate sample data for testing clustering."""
    click.echo(f"🎲 Generating {count} sample users...")
    
    async def run_generation():
        generator = SampleDataGenerator()
        await generator.generate_users(count)
        await generator.display_generated_data()
    
    asyncio.run(run_generation())
    click.echo("✅ Sample data generation completed!")

@cli.command()
def run_clustering():
    """Run the user clustering process."""
    click.echo("🔄 Starting user clustering...")
    
    SessionLocal = sessionmaker(bind=user_engine)
    session = SessionLocal()
    
    try:
        success = run_user_clustering(session)
        if success:
            click.echo("✅ Clustering completed successfully!")
        else:
            click.echo("⚠️ Clustering completed with warnings")
    except Exception as e:
        click.echo(f"❌ Clustering failed: {e}")
        sys.exit(1)
    finally:
        session.close()

@cli.command()
def test_clustering():
    """Test clustering with detailed output."""
    click.echo("🧪 Running clustering test...")
    
    async def run_test():
        tester = ClusteringTester()
        await tester.test_clustering()
    
    asyncio.run(run_test())

@cli.command()
def status():
    """Show clustering status and statistics."""
    SessionLocal = sessionmaker(bind=user_engine)
    session = SessionLocal()
    
    try:
        from models.user import User
        from models.cluster import Cluster, UserClusterAssociation, ClusterDestination
        
        # Basic stats
        total_users = session.query(User).count()
        users_with_embeddings = session.query(User).filter(User.embedding.isnot(None)).count()
        total_clusters = session.query(Cluster).count()
        total_associations = session.query(UserClusterAssociation).count()
        
        click.echo("📊 Clustering Status:")
        click.echo(f"   Users: {total_users} total, {users_with_embeddings} with embeddings")
        click.echo(f"   Clusters: {total_clusters}")
        click.echo(f"   Associations: {total_associations}")
        
        # Show cluster distribution
        clusters = session.query(Cluster).all()
        for cluster in clusters:
            user_count = session.query(UserClusterAssociation).filter_by(cluster_id=cluster.id).count()
            dest_count = session.query(ClusterDestination).filter_by(cluster_id=cluster.id).count()
            click.echo(f"   {cluster.name}: {user_count} users, {dest_count} destinations")
            
    except Exception as e:
        click.echo(f"❌ Error getting status: {e}")
        sys.exit(1)
    finally:
        session.close()

@cli.command()
def reset():
    """Reset all clustering data."""
    if click.confirm('⚠️  This will delete all clustering data. Are you sure?'):
        SessionLocal = sessionmaker(bind=user_engine)
        session = SessionLocal()
        
        try:
            from models.user import User
            from models.cluster import Cluster, UserClusterAssociation, ClusterDestination
            
            # Delete clustering data
            session.query(ClusterDestination).delete()
            session.query(UserClusterAssociation).delete() 
            session.query(Cluster).delete()
            session.query(User).update({"embedding": None, "last_embedding_update": None})
            
            session.commit()
            click.echo("✅ Clustering data reset successfully!")
            
        except Exception as e:
            session.rollback()
            click.echo(f"❌ Error resetting data: {e}")
            sys.exit(1)
        finally:
            session.close()

if __name__ == '__main__':
    cli()