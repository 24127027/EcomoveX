from fastapi import HTTPException, status
from repository.message_repository import MessageRepository
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.message_schema import *
from services.room_service import RoomService

class MessageService:
    @staticmethod
    async def get_message_by_id(db: AsyncSession, user_id: int, message_id: int) -> MessageResponse:
        try:
            message = await MessageRepository.get_message_by_id(db, message_id)
            if not message:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Message ID {message_id} not found"
                )
            is_member = await RoomService.is_user_in_room(db, user_id, message.room_id)
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"User ID {user_id} is not a member of room ID {message.room_id}"
                )
            return MessageResponse(
                id=message.id,
                sender_id=message.sender_id,
                room_id=message.room_id,
                content=message.content,
                message_type=message.message_type,
                status=message.status,
                timestamp=message.created_at
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving message ID {message_id}: {e}"
            )
    
    @staticmethod
    async def get_message_by_keyword(db: AsyncSession, user_id: int, room_id: int, keyword: str) -> list[MessageResponse]:
        try:
            is_member = await RoomService.is_user_in_room(db, user_id, room_id)
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"User ID {user_id} is not a member of room ID {room_id}"
                )
            messages = await MessageRepository.search_messages_by_keyword(db, room_id, keyword)
            if messages is None:
                return []
            message_list = [
                MessageResponse(
                    id=msg.id,
                    sender_id=msg.sender_id,
                    room_id=msg.room_id,
                    content=msg.content,
                    message_type=msg.message_type,
                    status=msg.status,
                    timestamp=msg.created_at
                ) for msg in messages]
            return message_list
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error searching messages with keyword '{keyword}': {e}"
            )
    
    @staticmethod
    async def get_messages_by_room(db: AsyncSession, user_id: int, room_id: int) -> list[MessageResponse]:
        try:
            is_member = await RoomService.is_user_in_room(db, user_id, room_id)
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"User ID {user_id} is not a member of room ID {room_id}"
                )
            messages = await MessageRepository.get_messages_by_room(db, room_id)
            if messages is None:
                return []
            message_list = [
                MessageResponse(
                    id=msg.id,
                    sender_id=msg.sender_id,
                    room_id=msg.room_id,
                    content=msg.content,
                    message_type=msg.message_type,
                    status=msg.status,
                    timestamp=msg.created_at
                ) for msg in messages]
            return message_list
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving messages for room ID {room_id}: {e}"
            )
    
    @staticmethod
    async def create_message(db: AsyncSession, sender_id: int, room_id: int, message_data: MessageCreate) -> MessageResponse:
        try:
            is_member = await RoomService.is_user_in_room(db, sender_id, room_id)
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"User ID {sender_id} is not a member of room ID {room_id}"
                )
            new_message = await MessageRepository.create_message(db, sender_id, room_id, message_data)
            if not new_message:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create message"
                )
            return MessageResponse(
                id=new_message.id,
                sender_id=new_message.sender_id,
                room_id=new_message.room_id,
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