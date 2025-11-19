from fastapi import HTTPException, status
from repository.message_repository import MessageRepository
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.message_schema import *

class MessageService:
    @staticmethod
    async def get_message_by_keyword(db: AsyncSession, user_id: int, keyword: str):
        try:
            messages = await MessageRepository.get_message_by_keyword(db, user_id, keyword)
            if messages is None:
                return []
            message_list = [
                MessageResponse(
                    id=msg.id,
                    sender_id=msg.sender_id,
                    receiver_id=msg.receiver_id,
                    content=msg.content,
                    message_type=msg.message_type,
                    status=msg.status,
                    timestamp=msg.created_at
                ) for msg in messages]
            return message_list
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error searching messages with keyword '{keyword}': {e}"
            )
    
    @staticmethod
    async def create_message(db: AsyncSession, sender_id: int, receiver_id: int, message_data: MessageCreate):
        try:
            new_message = await MessageRepository.create_message(db, sender_id, receiver_id, message_data)
            if not new_message:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create message"
                )
            return MessageResponse(
                id=new_message.id,
                sender_id=new_message.sender_id,
                receiver_id=new_message.receiver_id,
                content=new_message.content,
                message_type=new_message.message_type,
                status=new_message.status,
                timestamp=new_message.created_at
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error creating message: {e}"
            )
        
    @staticmethod
    async def delete_message(db: AsyncSession, sender_id: int, message_id: int):
        try:
            success = await MessageRepository.delete_message(db, sender_id, message_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Message with ID {message_id} not found"
                )
            return {"detail": "Message deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error deleting message ID {message_id}: {e}"
            )