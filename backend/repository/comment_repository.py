from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from models.comment import Comment
from datetime import datetime
from schema.comment_schema import CommentCreate, CommentUpdate

class CommentRepository:
    @staticmethod
    async def get_comments_by_post(db: AsyncSession, post_id: int):
        try:
            result = await db.execute(select(Comment).where(Comment.post_id == post_id))
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"Error fetching comments for post {post_id}: {e}")
            return []

    @staticmethod
    async def get_comment_by_author(db: AsyncSession, author_id: int):
        try:
            result = await db.execute(select(Comment).where(Comment.author_id == author_id))
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"Error fetching comments by author {author_id}: {e}")
            return []

    @staticmethod
    async def create_comment(db: AsyncSession, comment_data: CommentCreate):
        try:
            new_comment = Comment(
                post_id=comment_data.post_id,
                author_id=comment_data.author_id,
                content=comment_data.content
            )
            new_comment.created_at = datetime.utcnow()
            db.add(new_comment)
            await db.commit()
            await db.refresh(new_comment)
            return new_comment
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error creating comment: {e}")
            return None

    @staticmethod
    async def update_comment(db: AsyncSession, comment_id: int, updated_data: CommentUpdate):
        try:
            result = await db.execute(select(Comment).where(Comment.id == comment_id))
            comment = result.scalar_one_or_none()
            if not comment:
                print(f"Comment ID {comment_id} not found")
                return None

            for key, value in updated_data.items():
                setattr(comment, key, value)

            db.add(comment)
            await db.commit()
            await db.refresh(comment)
            return comment
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error updating comment ID {comment_id}: {e}")
            return None

    @staticmethod
    async def delete_comment(db: AsyncSession, comment_id: int):
        try:
            result = await db.execute(select(Comment).where(Comment.id == comment_id))
            comment = result.scalar_one_or_none()
            if not comment:
                print(f"Comment ID {comment_id} not found")
                return False

            await db.delete(comment)
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"Error deleting comment ID {comment_id}: {e}")
            return False