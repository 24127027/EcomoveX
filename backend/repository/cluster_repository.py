from typing import List, Optional

from sqlalchemy import and_, delete, func, select, text, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.cluster import (
    Cluster,
    ClusterDestination,
    Preference,
    UserClusterAssociation,
)
from models.user import User
from schemas.cluster_schema import *


class ClusterRepository:
    @staticmethod
    async def get_all_clusters(
        db: AsyncSession,
    ):
        try:
            query = select(Cluster).order_by(Cluster.created_at.desc())

            result = await db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: fetching all clusters - {e}")
            return []

    @staticmethod
    async def get_cluster_by_id(
        db: AsyncSession,
        cluster_id: int,
        include_users: bool = False,
        include_destinations: bool = False,
    ):
        try:
            query = select(Cluster).where(Cluster.id == cluster_id)

            if include_users:
                query = query.options(selectinload(Cluster.users))
            if include_destinations:
                query = query.options(selectinload(Cluster.destinations))

            result = await db.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"ERROR: fetching cluster ID {cluster_id} - {e}")
            return None

    @staticmethod
    async def create_cluster(db: AsyncSession, cluster_data: ClusterCreate):
        try:
            new_cluster = Cluster(
                name=cluster_data.name,
                algorithm=cluster_data.algorithm,
                description=cluster_data.description,
            )
            db.add(new_cluster)
            await db.commit()
            await db.refresh(new_cluster)
            return new_cluster
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: creating cluster - {e}")
            return None

    @staticmethod
    async def update_cluster(db: AsyncSession, cluster_id: int, updated_data: ClusterUpdate):
        try:
            update_dict = {
                k: v
                for k, v in updated_data.model_dump(exclude_unset=True).items()
                if v is not None
            }

            if not update_dict:
                return await ClusterRepository.get_cluster_by_id(db, cluster_id)

            stmt = (
                update(Cluster)
                .where(Cluster.id == cluster_id)
                .values(**update_dict)
                .returning(Cluster)
            )
            result = await db.execute(stmt)
            await db.commit()

            cluster = result.scalar_one_or_none()
            if cluster:
                await db.refresh(cluster)
            return cluster
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: updating cluster ID {cluster_id} - {e}")
            return None

    @staticmethod
    async def delete_cluster(db: AsyncSession, cluster_id: int):
        try:
            stmt = delete(Cluster).where(Cluster.id == cluster_id)
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: deleting cluster ID {cluster_id} - {e}")
            return False

    @staticmethod
    async def add_user_to_cluster(db: AsyncSession, user_id: int, cluster_id: int):
        try:
            result = await db.execute(
                select(UserClusterAssociation).where(
                    and_(
                        UserClusterAssociation.user_id == user_id,
                        UserClusterAssociation.cluster_id == cluster_id,
                    )
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                return existing

            new_association = UserClusterAssociation(user_id=user_id, cluster_id=cluster_id)
            db.add(new_association)
            await db.commit()
            await db.refresh(new_association)
            return new_association
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: adding user {user_id} to cluster {cluster_id} - {e}")
            return None

    @staticmethod
    async def remove_user_from_cluster(db: AsyncSession, user_id: int, cluster_id: int):
        try:
            stmt = delete(UserClusterAssociation).where(
                and_(
                    UserClusterAssociation.user_id == user_id,
                    UserClusterAssociation.cluster_id == cluster_id,
                )
            )
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: removing user {user_id} from cluster {cluster_id} - {e}")
            return False

    @staticmethod
    async def get_users_in_cluster(
        db: AsyncSession,
        cluster_id: int,
    ):
        try:
            query = select(UserClusterAssociation.user_id).where(
                UserClusterAssociation.cluster_id == cluster_id
            )

            result = await db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: fetching users in cluster {cluster_id} - {e}")
            return []

    @staticmethod
    async def get_clusters_for_user(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(
                select(Cluster)
                .join(UserClusterAssociation)
                .where(UserClusterAssociation.user_id == user_id)
                .order_by(Cluster.created_at.desc())
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: fetching clusters for user {user_id} - {e}")
            return []

    @staticmethod
    async def is_user_in_cluster(db: AsyncSession, user_id: int, cluster_id: int):
        try:
            query = select(UserClusterAssociation).where(
                and_(
                    UserClusterAssociation.user_id == user_id,
                    UserClusterAssociation.cluster_id == cluster_id,
                )
            )
            result = await db.execute(query)
            return result.scalar_one_or_none() is not None
        except SQLAlchemyError as e:
            print(f"ERROR: checking user {user_id} in cluster {cluster_id} - {e}")
            return False

    @staticmethod
    async def add_destination_to_cluster(
        db: AsyncSession,
        cluster_id: int,
        destination_id: str,
        popularity_score: Optional[float] = None,
    ):
        try:
            result = await db.execute(
                select(ClusterDestination).where(
                    and_(
                        ClusterDestination.cluster_id == cluster_id,
                        ClusterDestination.destination_id == destination_id,
                    )
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                if popularity_score is not None:
                    existing.popularity_score = popularity_score
                    await db.commit()
                    await db.refresh(existing)
                return existing

            new_cluster_dest = ClusterDestination(
                cluster_id=cluster_id,
                destination_id=destination_id,
                popularity_score=popularity_score,
            )
            db.add(new_cluster_dest)
            await db.commit()
            await db.refresh(new_cluster_dest)
            return new_cluster_dest
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: adding destination to cluster - {e}")
            return None

    @staticmethod
    async def remove_destination_from_cluster(
        db: AsyncSession, cluster_id: int, destination_id: str
    ):
        try:
            stmt = delete(ClusterDestination).where(
                and_(
                    ClusterDestination.cluster_id == cluster_id,
                    ClusterDestination.destination_id == destination_id,
                )
            )
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: removing destination from cluster - {e}")
            return False

    @staticmethod
    async def update_destination_popularity(
        db: AsyncSession, cluster_id: int, destination_id: str, popularity_score: float
    ):
        try:
            stmt = (
                update(ClusterDestination)
                .where(
                    and_(
                        ClusterDestination.cluster_id == cluster_id,
                        ClusterDestination.destination_id == destination_id,
                    )
                )
                .values(popularity_score=popularity_score)
                .returning(ClusterDestination)
            )
            result = await db.execute(stmt)
            await db.commit()

            cluster_dest = result.scalar_one_or_none()
            await db.refresh(cluster_dest)
            return cluster_dest
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: updating popularity score - {e}")
            return None

    @staticmethod
    async def get_destinations_in_cluster(
        db: AsyncSession,
        cluster_id: int,
    ):
        try:
            query = (
                select(ClusterDestination)
                .where(ClusterDestination.cluster_id == cluster_id)
                .order_by(ClusterDestination.popularity_score.desc())
            )
            result = await db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: fetching destinations in cluster {cluster_id} - {e}")
            return []

    @staticmethod
    async def get_cluster_destination(db: AsyncSession, cluster_id: int, destination_id: str):
        try:
            query = select(ClusterDestination).where(
                and_(
                    ClusterDestination.cluster_id == cluster_id,
                    ClusterDestination.destination_id == destination_id,
                )
            )
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"ERROR: fetching destination {destination_id} in cluster {cluster_id} - {e}")
            return None

    @staticmethod
    async def get_top_destinations_in_cluster(db: AsyncSession, cluster_id: int, limit: int = 10):
        try:
            query = (
                select(ClusterDestination)
                .where(ClusterDestination.cluster_id == cluster_id)
                .order_by(ClusterDestination.popularity_score.desc())
                .limit(limit)
            )
            result = await db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: fetching top destinations in cluster {cluster_id} - {e}")
            return []

    @staticmethod
    async def get_users_needing_embedding_update(db: AsyncSession, cutoff_date: int):
        try:
            recent_prefs = select(Preference.user_id).where(
                and_(
                    Preference.embedding.isnot(None),
                    Preference.last_updated > cutoff_date,
                )
            )
            query = select(User).where(User.id.notin_(recent_prefs))

            result = await db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: fetching users needing embedding update - {e}")
            return []

    @staticmethod
    async def get_users_with_embeddings(db: AsyncSession):
        try:
            query = select(Preference).where(Preference.embedding.isnot(None))
            result = await db.execute(query)
            return result.unique().scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: fetching users with embeddings - {e}")
            return []

    @staticmethod
    async def update_user_embedding(
        db: AsyncSession,
        user_id: int,
        embedding: List[float],
    ):
        try:
            pref_query = select(Preference).where(Preference.user_id == user_id)
            result = await db.execute(pref_query)
            existing_pref = result.scalar_one_or_none()

            if existing_pref:
                stmt = (
                    update(Preference)
                    .where(Preference.user_id == user_id)
                    .values(embedding=embedding, last_updated=func.now())
                )
                await db.execute(stmt)
            else:
                new_pref = Preference(user_id=user_id, embedding=embedding, last_updated=func.now())
                db.add(new_pref)

            await db.flush()
            return True
        except SQLAlchemyError as e:
            print(f"ERROR: updating embedding for user {user_id} - {e}")
            return False

    @staticmethod
    async def get_preference_by_user_id(db: AsyncSession, user_id: int):
        try:
            query = select(Preference).where(Preference.user_id == user_id)
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"ERROR: fetching preference for user {user_id} - {e}")
            return None

    @staticmethod
    async def update_preference_cluster(db: AsyncSession, user_id: int, cluster_id: int):
        try:
            stmt = (
                update(Preference)
                .where(Preference.user_id == user_id)
                .values(cluster_id=cluster_id, last_updated=func.now())
            )
            await db.execute(stmt)
            await db.flush()
            return True
        except SQLAlchemyError as e:
            print(f"ERROR: updating cluster for user {user_id} preference - {e}")
            return False

    @staticmethod
    async def get_users_without_cluster(
        db: AsyncSession,
    ):
        try:
            subquery = select(UserClusterAssociation.user_id).distinct()
            query = select(User).where(User.id.notin_(subquery))

            result = await db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: fetching users without cluster - {e}")
            return []

    @staticmethod
    async def create_or_update_preference(
        db: AsyncSession,
        user_id: int,
        weather_pref: Optional[dict] = None,
        attraction_types: Optional[list] = None,
        budget_range: Optional[dict] = None,
        kids_friendly: Optional[bool] = None,
        visited_destinations: Optional[list] = None,
        embedding: Optional[list] = None,
        weight: Optional[float] = None,
        cluster_id: Optional[int] = None,
    ):
        try:
            result = await db.execute(select(Preference).where(Preference.user_id == user_id))
            preference = result.scalar_one_or_none()

            if preference:
                if weather_pref is not None:
                    preference.weather_pref = weather_pref
                if attraction_types is not None:
                    preference.attraction_types = attraction_types
                if budget_range is not None:
                    preference.budget_range = budget_range
                if kids_friendly is not None:
                    preference.kids_friendly = kids_friendly
                if visited_destinations is not None:
                    preference.visited_destinations = visited_destinations
                if embedding is not None:
                    preference.embedding = embedding
                if weight is not None:
                    preference.weight = weight
                if cluster_id is not None:
                    preference.cluster_id = cluster_id
                preference.last_updated = func.now()
            else:
                preference = Preference(
                    user_id=user_id,
                    weather_pref=weather_pref,
                    attraction_types=attraction_types,
                    budget_range=budget_range,
                    kids_friendly=kids_friendly or False,
                    visited_destinations=visited_destinations,
                    embedding=embedding,
                    weight=weight or 1.0,
                    cluster_id=cluster_id,
                )
                db.add(preference)

            await db.commit()
            await db.refresh(preference)
            return preference
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: creating/updating preference for user {user_id} - {e}")
            return None

    @staticmethod
    async def delete_preference(db: AsyncSession, user_id: int):
        try:
            result = await db.execute(select(Preference).where(Preference.user_id == user_id))
            preference = result.scalar_one_or_none()
            if not preference:
                print(f"WARNING: Preference for user {user_id} not found")
                return False

            await db.delete(preference)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"ERROR: deleting preference for user {user_id} - {e}")
            return False

    @staticmethod
    async def get_all_preferences(db: AsyncSession, skip: int = 0, limit: int = 100):
        try:
            result = await db.execute(
                select(Preference)
                .order_by(Preference.last_updated.desc())
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"ERROR: fetching all preferences - {e}")
            return []

    @staticmethod
    async def get_user_latest_cluster(db: AsyncSession, user_id: int) -> Optional[int]:
        """Get the most recent cluster_id for a user."""
        try:
            query = select(UserClusterAssociation.cluster_id).where(
                UserClusterAssociation.user_id == user_id
            ).order_by(UserClusterAssociation.created_at.desc()).limit(1)
            
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"ERROR: fetching latest cluster for user {user_id} - {e}")
            return None

    @staticmethod
    async def get_cluster_preferred_categories(
        db: AsyncSession, 
        cluster_id: int, 
        limit: int = 5
    ) -> List[str]:
        """Get most frequent categories visited by users in a cluster."""
        try:
            query = text("""
                SELECT DISTINCT d.category, COUNT(*) as frequency
                FROM visits v
                JOIN destinations d ON v.destination_id = d.destination_id
                JOIN user_clusters uc ON v.user_id = uc.user_id
                WHERE uc.cluster_id = :cluster_id AND d.category IS NOT NULL
                GROUP BY d.category
                ORDER BY frequency DESC
                LIMIT :limit
            """)
            result = await db.execute(query, {"cluster_id": cluster_id, "limit": limit})
            return [row.category for row in result]
        except SQLAlchemyError as e:
            print(f"ERROR: fetching preferred categories for cluster {cluster_id} - {e}")
            return []

    @staticmethod
    async def get_cluster_embedding(db: AsyncSession, cluster_id: int) -> Optional[List[float]]:
        """Get cluster embedding vector."""
        try:
            result = await db.execute(
                select(Cluster.embedding).where(Cluster.id == cluster_id)
            )
            embedding = result.scalar_one_or_none()
            return embedding if embedding else None
        except SQLAlchemyError as e:
            print(f"ERROR: fetching cluster embedding for cluster {cluster_id} - {e}")
            return None
