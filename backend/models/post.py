from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.database import Base
import enum


class PostStatus(str, enum.Enum):
    """Post status enumeration"""
    draft = "draft"
    published = "published"
    archived = "archived"


class ForumPost(Base):
    """Forum Post database model"""
    __tablename__ = "forum_posts"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Post content
    title = Column(String(200), nullable=False, index=True)
    content = Column(Text, nullable=False)
    
    status = Column(
        SQLEnum(PostStatus),
        default=PostStatus.published,
        nullable=False,
        index=True
    )
    
    # Engagement metrics
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    
    # Flags
    is_pinned = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True))
    
    # Relationships
    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ForumPost(id={self.id}, title='{self.title}', author_id={self.author_id})>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "author_id": self.author_id,
            "title": self.title,
            "content": self.content,
            "category": self.category.value if self.category else None,
            "status": self.status.value if self.status else None,
            "views": self.views,
            "likes": self.likes,
            "is_pinned": self.is_pinned,
            "is_deleted": self.is_deleted,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None
        }


class Comment(Base):
    """Comment database model"""
    __tablename__ = "comments"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    post_id = Column(Integer, ForeignKey("forum_posts.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    parent_comment_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)
    
    # Comment content
    content = Column(Text, nullable=False)
    
    # Engagement metrics
    likes = Column(Integer, default=0)
    
    # Flags
    is_deleted = Column(Boolean, default=False)
    is_edited = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    post = relationship("ForumPost", back_populates="comments")
    author = relationship("User", back_populates="comments")
    replies = relationship("Comment", backref="parent", remote_side=[id], cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Comment(id={self.id}, post_id={self.post_id}, author_id={self.author_id})>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "post_id": self.post_id,
            "author_id": self.author_id,
            "parent_comment_id": self.parent_comment_id,
            "content": self.content,
            "likes": self.likes,
            "is_deleted": self.is_deleted,
            "is_edited": self.is_edited,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
