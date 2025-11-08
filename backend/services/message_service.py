from fastapi import HTTPException, status
from repository.message_repository import MessageRepository
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.message_schema import MessageCreate, MessageUpdate

class MessageService:
    @staticmethod
    async def get_message_by_id(db: AsyncSession, message_id: int):
        try:
            message = await MessageRepository.get_message_by_id(db, message_id)
            if not message:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Message with ID {message_id} not found"
                )
            return message
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving message ID {message_id}: {e}"
            )

    @staticmethod
    async def get_message_by_keyword(db: AsyncSession, keyword: str, user_id: int):
        try:
            messages = await MessageRepository.get_message_by_keyword(db, keyword, user_id)
            if messages is None:
                return []
            return messages
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error searching messages with keyword '{keyword}': {e}"
            )
    
    @staticmethod
    async def create_message(db: AsyncSession, message_data: MessageCreate, user_id: int):
        try:
            new_message = await MessageRepository.create_message(db, message_data, user_id)
            if not new_message:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create message"
                )
            return new_message
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error creating message: {e}"
            )
    
    @staticmethod
    async def update_message(db: AsyncSession, message_id: int, updated_data: MessageUpdate):
        try:
            updated_message = await MessageRepository.update_message(db, message_id, updated_data)
            if not updated_message:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Message with ID {message_id} not found"
                )
            return updated_message
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error updating message ID {message_id}: {e}"
            )
    
    @staticmethod
    async def delete_message(db: AsyncSession, message_id: int):
        try:
            success = await MessageRepository.delete_message(db, message_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Message with ID {message_id} not found"
                )
            return {"detail": "Message deleted successfully"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error deleting message ID {message_id}: {e}"
            )