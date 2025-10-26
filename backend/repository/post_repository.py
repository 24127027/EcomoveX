from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from models.post import Post
from datetime import datetime
from schema.post_schema import PostCreate, PostUpdate

class PostRepository:
    @staticmethod
    async def get_all_posts(db: AsyncSession):
        try:
            result = await db.execute(select(Post))
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"Error fetching all posts: {e}")
            return []

    @staticmethod
    async def get_post_by_id(db: AsyncSession, post_id: int):
        try:
            result = await db.execute(select(Post).where(Post.id == post_id))
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"Error fetching post ID {post_id}: {e}")
            return None

    @staticmethod
    async def get_posts_by_author(db: AsyncSession, author_id: int):
        try:
            result = await db.execute(select(Post).where(Post.author_id == author_id))
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"Error fetching posts by author {author_id}: {e}")
            return []

    @staticmethod
    async def create_post(db: AsyncSession, post_data: PostCreate):
        try:
            new_post = Post(
                title=post_data.title,
                content=post_data.content,
                author_id=post_data.author_id,
                status=post_data.status
            )
            db.add(new_post)
            await db.commit()
            await db.refresh(new_post)
            return new_post
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error creating post: {e}")
            return None

    @staticmethod
    async def update_post(db: AsyncSession, post_id: int, updated_data: PostUpdate):
        try:
            result = await db.execute(select(Post).where(Post.id == post_id))
            post = result.scalar_one_or_none()
            if not post:
                print(f"Post ID {post_id} not found")
                return None

            for key, value in updated_data.items():
                setattr(post, key, value)
            post.updated_at = datetime.utcnow()

            db.add(post)
            await db.commit()
            await db.refresh(post)
            return post
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error updating post ID {post_id}: {e}")
            return None

    @staticmethod
    async def delete_post(db: AsyncSession, post_id: int):
        try:
            result = await db.execute(select(Post).where(Post.id == post_id))
            post = result.scalar_one_or_none()
            if not post:
                print(f"Post ID {post_id} not found")
                return False

            await db.delete(post)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error deleting post ID {post_id}: {e}")
            return False
