from fastapi import HTTPException, status
from repository.room_repository import RoomRepository
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

class RoomService:
    @staticmethod
    async def is_user_in_room(db: AsyncSession, user_id: int, room_id: int) -> bool:
        try:
            return await RoomRepository.is_member(db, user_id, room_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error checking room membership for user ID {user_id} in room ID {room_id}: {e}"
            )
    
    @staticmethod
    async def get_room(db: AsyncSession, user_id: int, room_id: int):
        try:
            is_member = await RoomRepository.is_member(db, user_id, room_id)
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"User ID {user_id} is not a member of room ID {room_id}"
                )
            room = await RoomRepository.get_room_by_id(db, room_id)
            if not room:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Room ID {room_id} not found"
                )
            return room
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving room ID {room_id} for user ID {user_id}: {e}"
            )
    
    @staticmethod
    async def create_room(db: AsyncSession, user_id: int, room_name: str, member_ids: List[int] = None):
        try:
            new_room = await RoomRepository.create_room(db, user_id, room_name)
            if not new_room:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create room"
                )
            for member_id in member_ids:
                if member_id != user_id:
                    member = await RoomRepository.add_member(db, member_id, new_room.id)
                    if not member:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to add member ID {member_id} to room ID {new_room.id}"
                        )
            return new_room
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error creating room '{room_name}': {e}"
            )
            
    @staticmethod
    async def add_user_to_room(db: AsyncSession, current_user_id: int, user_id: int, room_id: int):
        try:
            is_current_user_member = await RoomRepository.is_member(db, current_user_id, room_id)
            if not is_current_user_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Current user ID {current_user_id} is not a member of room ID {room_id}"
                )
            is_member = await RoomRepository.is_member(db, user_id, room_id)
            if is_member:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User ID {user_id} is already a member of room ID {room_id}"
                )
            success = await RoomRepository.add_member(db, user_id, room_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to add user ID {user_id} to room ID {room_id}"
                )
            return success
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error adding user ID {user_id} to room ID {room_id}: {e}"
            )
            
    @staticmethod
    async def remove_user_from_room(db: AsyncSession, current_user_id: int, user_id: int, room_id: int):
        try:
            is_owner = await RoomRepository.is_owner(db, current_user_id, room_id)
            if not is_owner:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Current user ID {current_user_id} is not the owner of room ID {room_id}"
                )
            success = await RoomRepository.remove_member(db, user_id, room_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to remove user ID {user_id} from room ID {room_id}"
                )
            return success
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error removing user ID {user_id} from room ID {room_id}: {e}"
            )