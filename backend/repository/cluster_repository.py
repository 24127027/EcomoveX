from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload
from models.cluster import Cluster, UserClusterAssociation, ClusterDestination
from schemas.cluster_schema import (
    ClusterCreate, ClusterUpdate, 
    UserClusterAssociationCreate, 
    ClusterDestinationCreate, ClusterDestinationUpdate
)
from typing import List, Optional

class ClusterRepository:
    @staticmethod
    async def get_all_clusters(db: AsyncSession) -> List[Cluster]:
        """Get all clusters"""
        try:
            result = await db.execute(select(Cluster))
            return result.scalars().all()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error fetching all clusters: {e}")
            return []

    @staticmethod
    async def get_cluster_by_id(db: AsyncSession, cluster_id: int) -> Optional[Cluster]:
        """Get a cluster by ID"""
        try:
            result = await db.execute(select(Cluster).where(Cluster.id == cluster_id))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error fetching cluster ID {cluster_id}: {e}")
            return None

    @staticmethod
    async def get_cluster_by_name(db: AsyncSession, name: str) -> Optional[Cluster]:
        """Get a cluster by name"""
        try:
            result = await db.execute(select(Cluster).where(Cluster.name == name))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error fetching cluster by name {name}: {e}")
            return None

    @staticmethod
    async def get_clusters_by_algorithm(db: AsyncSession, algorithm: str) -> List[Cluster]:
        """Get all clusters created with a specific algorithm"""
        try:
            result = await db.execute(select(Cluster).where(Cluster.algorithm == algorithm))
            return result.scalars().all()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error fetching clusters by algorithm {algorithm}: {e}")
            return []

    @staticmethod
    async def create_cluster(db: AsyncSession, cluster_data: ClusterCreate) -> Optional[Cluster]:
        """Create a new cluster"""
        try:
            new_cluster = Cluster(
                name=cluster_data.name,
                algorithm=cluster_data.algorithm
            )
            db.add(new_cluster)
            await db.commit()
            await db.refresh(new_cluster)
            return new_cluster
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error creating cluster: {e}")
            return None

    @staticmethod
    async def update_cluster(db: AsyncSession, cluster_id: int, updated_data: ClusterUpdate) -> Optional[Cluster]:
        """Update a cluster"""
        try:
            result = await db.execute(select(Cluster).where(Cluster.id == cluster_id))
            cluster = result.scalar_one_or_none()
            if not cluster:
                print(f"Cluster ID {cluster_id} not found")
                return None

            if updated_data.name is not None:
                cluster.name = updated_data.name
            if updated_data.algorithm is not None:
                cluster.algorithm = updated_data.algorithm

            db.add(cluster)
            await db.commit()
            await db.refresh(cluster)
            return cluster
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error updating cluster ID {cluster_id}: {e}")
            return None

    @staticmethod
    async def delete_cluster(db: AsyncSession, cluster_id: int) -> bool:
        """Delete a cluster (CASCADE will remove associations and destinations)"""
        try:
            result = await db.execute(select(Cluster).where(Cluster.id == cluster_id))
            cluster = result.scalar_one_or_none()
            if not cluster:
                print(f"Cluster ID {cluster_id} not found")
                return False

            await db.delete(cluster)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error deleting cluster ID {cluster_id}: {e}")
            return False

class UserClusterAssociationRepository:
    @staticmethod
    async def add_user_to_cluster(db: AsyncSession, association_data: UserClusterAssociationCreate) -> Optional[UserClusterAssociation]:
        """Associate a user with a cluster"""
        try:
            # Check if association already exists
            result = await db.execute(
                select(UserClusterAssociation).where(
                    and_(
                        UserClusterAssociation.user_id == association_data.user_id,
                        UserClusterAssociation.cluster_id == association_data.cluster_id
                    )
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                print(f"User {association_data.user_id} already associated with cluster {association_data.cluster_id}")
                return existing

            new_association = UserClusterAssociation(
                user_id=association_data.user_id,
                cluster_id=association_data.cluster_id
            )
            db.add(new_association)
            await db.commit()
            await db.refresh(new_association)
            return new_association
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error adding user {association_data.user_id} to cluster {association_data.cluster_id}: {e}")
            return None

    @staticmethod
    async def remove_user_from_cluster(db: AsyncSession, user_id: int, cluster_id: int) -> bool:
        """Remove user from cluster"""
        try:
            result = await db.execute(
                select(UserClusterAssociation).where(
                    and_(
                        UserClusterAssociation.user_id == user_id,
                        UserClusterAssociation.cluster_id == cluster_id
                    )
                )
            )
            association = result.scalar_one_or_none()
            if not association:
                print(f"Association between user {user_id} and cluster {cluster_id} not found")
                return False

            await db.delete(association)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error removing user {user_id} from cluster {cluster_id}: {e}")
            return False

    @staticmethod
    async def get_users_in_cluster(db: AsyncSession, cluster_id: int) -> List[int]:
        """Get all user IDs in a cluster"""
        try:
            result = await db.execute(
                select(UserClusterAssociation.user_id).where(
                    UserClusterAssociation.cluster_id == cluster_id
                )
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error fetching users in cluster {cluster_id}: {e}")
            return []

    @staticmethod
    async def get_clusters_for_user(db: AsyncSession, user_id: int) -> List[Cluster]:
        """Get all clusters a user belongs to"""
        try:
            result = await db.execute(
                select(Cluster)
                .join(UserClusterAssociation)
                .where(UserClusterAssociation.user_id == user_id)
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error fetching clusters for user {user_id}: {e}")
            return []

    @staticmethod
    async def remove_all_users_from_cluster(db: AsyncSession, cluster_id: int) -> bool:
        """Remove all users from a cluster"""
        try:
            result = await db.execute(
                select(UserClusterAssociation).where(
                    UserClusterAssociation.cluster_id == cluster_id
                )
            )
            associations = result.scalars().all()
            
            for association in associations:
                await db.delete(association)
            
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error removing all users from cluster {cluster_id}: {e}")
            return False

class ClusterDestinationRepository:
    @staticmethod
    async def add_destination_to_cluster(
        db: AsyncSession, 
        destination_data: ClusterDestinationCreate
    ) -> Optional[ClusterDestination]:
        """Associate a destination with a cluster"""
        try:
            # Check if association already exists
            result = await db.execute(
                select(ClusterDestination).where(
                    and_(
                        ClusterDestination.cluster_id == destination_data.cluster_id,
                        ClusterDestination.destination_id == destination_data.destination_id
                    )
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                # Update popularity score if provided
                if destination_data.popularity_score is not None:
                    existing.popularity_score = destination_data.popularity_score
                    await db.commit()
                    await db.refresh(existing)
                return existing

            new_cluster_dest = ClusterDestination(
                cluster_id=destination_data.cluster_id,
                destination_id=destination_data.destination_id,
                popularity_score=destination_data.popularity_score
            )
            db.add(new_cluster_dest)
            await db.commit()
            await db.refresh(new_cluster_dest)
            return new_cluster_dest
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error adding destination {destination_data.destination_id} to cluster {destination_data.cluster_id}: {e}")
            return None

    @staticmethod
    async def remove_destination_from_cluster(db: AsyncSession, cluster_id: int, destination_id: int) -> bool:
        """Remove destination from cluster"""
        try:
            result = await db.execute(
                select(ClusterDestination).where(
                    and_(
                        ClusterDestination.cluster_id == cluster_id,
                        ClusterDestination.destination_id == destination_id
                    )
                )
            )
            cluster_dest = result.scalar_one_or_none()
            if not cluster_dest:
                print(f"Destination {destination_id} not found in cluster {cluster_id}")
                return False

            await db.delete(cluster_dest)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error removing destination {destination_id} from cluster {cluster_id}: {e}")
            return False

    @staticmethod
    async def get_destinations_in_cluster(db: AsyncSession, cluster_id: int) -> List[ClusterDestination]:
        """Get all destinations in a cluster with their popularity scores"""
        try:
            result = await db.execute(
                select(ClusterDestination)
                .where(ClusterDestination.cluster_id == cluster_id)
                .order_by(ClusterDestination.popularity_score.desc())
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error fetching destinations in cluster {cluster_id}: {e}")
            return []

    @staticmethod
    async def get_clusters_for_destination(db: AsyncSession, destination_id: int) -> List[ClusterDestination]:
        """Get all clusters that include a specific destination"""
        try:
            result = await db.execute(
                select(ClusterDestination)
                .where(ClusterDestination.destination_id == destination_id)
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error fetching clusters for destination {destination_id}: {e}")
            return []

    @staticmethod
    async def update_destination_popularity(
        db: AsyncSession, 
        cluster_id: int, 
        destination_id: int, 
        updated_data: ClusterDestinationUpdate
    ) -> Optional[ClusterDestination]:
        """Update the popularity score of a destination in a cluster"""
        try:
            result = await db.execute(
                select(ClusterDestination).where(
                    and_(
                        ClusterDestination.cluster_id == cluster_id,
                        ClusterDestination.destination_id == destination_id
                    )
                )
            )
            cluster_dest = result.scalar_one_or_none()
            if not cluster_dest:
                print(f"Destination {destination_id} not found in cluster {cluster_id}")
                return None

            cluster_dest.popularity_score = updated_data.popularity_score
            db.add(cluster_dest)
            await db.commit()
            await db.refresh(cluster_dest)
            return cluster_dest
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error updating popularity score: {e}")
            return None

    @staticmethod
    async def remove_all_destinations_from_cluster(db: AsyncSession, cluster_id: int) -> bool:
        """Remove all destinations from a cluster"""
        try:
            result = await db.execute(
                select(ClusterDestination).where(
                    ClusterDestination.cluster_id == cluster_id
                )
            )
            cluster_dests = result.scalars().all()
            
            for cluster_dest in cluster_dests:
                await db.delete(cluster_dest)
            
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error removing all destinations from cluster {cluster_id}: {e}")
            return False

    @staticmethod
    async def get_top_destinations_in_cluster(
        db: AsyncSession, 
        cluster_id: int, 
        limit: int = 10
    ) -> List[ClusterDestination]:
        """Get top N destinations in a cluster by popularity score"""
        try:
            result = await db.execute(
                select(ClusterDestination)
                .where(ClusterDestination.cluster_id == cluster_id)
                .order_by(ClusterDestination.popularity_score.desc())
                .limit(limit)
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error fetching top destinations in cluster {cluster_id}: {e}")
            return []