from fastapi import HTTPException, status
from repository.room_repository import RoomRepository
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from schemas.room_schema import *

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
    async def get_all_rooms_for_user(db: AsyncSession, user_id: int) -> List[RoomResponse]:
        try:
            rooms = await RoomRepository.list_rooms_for_user(db, user_id)
            room_responses = []
            for room in rooms:
                members = await RoomRepository.list_members(db, room.id)
                member_ids = [member.user_id for member in members]
                room_responses.append(
                    RoomResponse(
                        id=room.id,
                        name=room.name,
                        user_id=room.user_id,
                        created_at=room.created_at,
                        member_ids=member_ids
                    )
                )
            return room_responses
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving rooms for user ID {user_id}: {e}"
            )
    
    @staticmethod
    async def get_room(db: AsyncSession, user_id: int, room_id: int) -> RoomResponse:
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
            members = await RoomRepository.list_members(db, room_id)
            member_ids = [member.user_id for member in members]
            return RoomResponse(
                id=room_id,
                name=room.name,
                user_id=room.user_id,
                created_at=room.created_at,
                member_ids=member_ids
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving room ID {room_id} for user ID {user_id}: {e}"
            )
    
    @staticmethod
    async def create_room(db: AsyncSession, user_id: int, room_name: str, member_ids: List[int] = None) -> RoomResponse:
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
            return RoomResponse(
                id=new_room.id,
                name=new_room.name,
                user_id=new_room.user_id,
                created_at=new_room.created_at,
                member_ids=member_ids or []
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error creating room '{room_name}': {e}"
            )
            
    @staticmethod
    async def add_users_to_room(db: AsyncSession, current_user_id: int, room_id: int, data: AddMemberRequest) -> RoomResponse:
        try:
            is_current_user_member = await RoomRepository.is_member(db, current_user_id, room_id)
            if not is_current_user_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Current user ID {current_user_id} is not a member of room ID {room_id}"
                )
            for user_id in data.ids:
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
            room = await RoomRepository.get_room_by_id(db, room_id)
            members = await RoomRepository.list_members(db, room_id)
            member_ids = [member.user_id for member in members]
            return RoomResponse(
                id=room_id,
                name=room.name,
                user_id=room.user_id,
                created_at=room.created_at,
                member_ids=member_ids
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error adding user ID {user_id} to room ID {room_id}: {e}"
            )
            
    @staticmethod
    async def remove_users_from_room(db: AsyncSession, current_user_id: int, room_id: int, data: RemoveMemberRequest) -> RoomResponse:
        try:
            is_owner = await RoomRepository.is_owner(db, current_user_id, room_id)
            if not is_owner:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Current user ID {current_user_id} is not the owner of room ID {room_id}"
                )
            for user_id in data.ids:
                success = await RoomRepository.remove_member(db, user_id, room_id)
                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to remove user ID {user_id} from room ID {room_id}"
                )
            room = await RoomRepository.get_room_by_id(db, room_id)
            members = await RoomRepository.list_members(db, room_id)
            member_ids = [member.user_id for member in members]
            return RoomResponse(
                id=room_id,
                name=room.name,
                user_id=room.user_id,
                created_at=room.created_at,
                member_ids=member_ids
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error removing user ID {user_id} from room ID {room_id}: {e}"
            )