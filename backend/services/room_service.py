from typing import List

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.room import MemberRole, RoomType
from repository.room_repository import RoomRepository
from schemas.room_schema import (
    AddMemberRequest,
    RemoveMemberRequest,
    RoomCreate,
    RoomMemberCreate,
    RoomResponse,
)


class RoomService:
    @staticmethod
    async def is_room_owner(db: AsyncSession, user_id: int, room_id: int) -> bool:
        try:
            return await RoomRepository.is_owner(db, user_id, room_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error checking room ownership for user ID {user_id} and room ID {room_id}: {e}",
            )

    @staticmethod
    async def is_member(db: AsyncSession, user_id: int, room_id: int) -> bool:
        try:
            return await RoomRepository.is_member(db, user_id, room_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error checking room membership for user ID {user_id} in room ID {room_id}: {e}",
            )

    @staticmethod
    async def get_all_rooms_for_user(
        db: AsyncSession, user_id: int
    ) -> List[RoomResponse]:
        try:
            rooms = await RoomRepository.list_rooms_for_user(db, user_id)
            room_responses = []
            for room in rooms:
                members = await RoomRepository.list_members(db, room.id)
                room_responses.append(
                    RoomResponse(
                        id=room.id,
                        name=room.name,
                        room_type=room.room_type,
                        created_at=room.created_at,
                        member_ids=[member.user_id for member in members],
                    )
                )
            return room_responses
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving rooms for user ID {user_id}: {e}",
            )

    @staticmethod
    async def get_room(db: AsyncSession, user_id: int, room_id: int) -> RoomResponse:
        try:
            is_member = await RoomRepository.is_member(db, user_id, room_id)
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"User ID {user_id} is not a member of room ID {room_id}",
                )
            room = await RoomRepository.get_room_by_id(db, room_id)
            if not room or room.room_type != RoomType.group:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Room ID {room_id} not found",
                )
            members = await RoomRepository.list_members(db, room_id)
            return RoomResponse(
                id=room_id,
                name=room.name,
                room_type=room.room_type,
                created_at=room.created_at,
                member_ids=[member.user_id for member in members],
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving room ID {room_id} for user ID {user_id}: {e}",
            )

    @staticmethod
    async def get_all_direct_rooms_for_user(
        db: AsyncSession, user_id: int
    ) -> List[RoomResponse]:
        try:
            direct_rooms = await RoomRepository.list_direct_rooms_for_user(db, user_id)
            return [
                RoomResponse(
                    id=room.id, room_type=room.room_type, created_at=room.created_at
                )
                for room in direct_rooms
            ]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving direct rooms for user ID {user_id}: {e}",
            )

    @staticmethod
    async def is_direct_room_between_users(
        db: AsyncSession, user1_id: int, user2_id: int
    ) -> bool:
        try:
            room = await RoomRepository.get_direct_room_between_users(
                db, user1_id, user2_id
            )
            return room is not None
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error checking direct room between user ID {user1_id} and user ID {user2_id}: {e}",
            )

    @staticmethod
    async def get_direct_rooms_between_users(
        db: AsyncSession, user1_id: int, user2_id: int
    ) -> RoomResponse:
        try:
            u1_norm = min(user1_id, user2_id)
            u2_norm = max(user1_id, user2_id)
            room = await RoomRepository.get_direct_room_between_users(
                db, u1_norm, u2_norm
            )
            if not room:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Direct room between user ID {u1_norm} and user ID {u2_norm} not found",
                )
            return RoomResponse(
                id=room.id, room_type=room.room_type, created_at=room.created_at
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving direct room between user ID {u1_norm} and user ID {u2_norm}: {e}",
            )

    @staticmethod
    async def get_direct_room(db: AsyncSession, room_id: int) -> RoomResponse:
        try:
            room = await RoomRepository.get_room_by_id(db, room_id)
            if not room or room.room_type != RoomType.direct:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Direct room ID {room_id} not found",
                )
            return RoomResponse(
                id=room.id, room_type=room.room_type, created_at=room.created_at
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving direct room ID {room_id} : {e}",
            )

    @staticmethod
    async def create_room(
        db: AsyncSession, user_id: int, data: RoomCreate
    ) -> RoomResponse:
        try:
            new_room = await RoomRepository.create_room(db, data)
            if not new_room:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create room",
                )
            room_owner = RoomMemberCreate(
                user_id=user_id, room_id=new_room.id, role=MemberRole.admin
            )
            await RoomRepository.add_member(db, new_room.id, room_owner)
            for member_id in data.member_ids:
                if member_id != user_id:
                    member_data = RoomMemberCreate(
                        user_id=member_id, room_id=new_room.id, role=MemberRole.member
                    )
                    member = await RoomRepository.add_member(
                        db, new_room.id, member_data
                    )
                    if not member:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to add member ID {member_id} to room ID {new_room.id}",
                        )
            return RoomResponse(
                id=new_room.id,
                name=new_room.name,
                room_type=new_room.room_type,
                created_at=new_room.created_at,
                member_ids=data.member_ids or [],
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error creating room '{data.name}': {e}",
            )

    @staticmethod
    async def create_direct_room(
        db: AsyncSession, user1_id: int, user2_id: int
    ) -> RoomResponse:
        try:
            if user1_id == user2_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot create a direct room with the same user",
                )

            u1_norm = min(user1_id, user2_id)
            u2_norm = max(user1_id, user2_id)

            existing_room = await RoomRepository.get_direct_room_between_users(
                db, u1_norm, u2_norm
            )
            if existing_room:
                return RoomResponse(
                    id=existing_room.id,
                    room_type=existing_room.room_type,
                    created_at=existing_room.created_at,
                )

            new_room = await RoomRepository.create_direct_room(db, u1_norm, u2_norm)
            if not new_room:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create direct room",
                )
            return RoomResponse(
                id=new_room.id,
                room_type=new_room.room_type,
                created_at=new_room.created_at,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error creating direct room between user ID {user1_id} and user ID {user2_id}: {e}",
            )

    @staticmethod
    async def add_users_to_room(
        db: AsyncSession, current_user_id: int, room_id: int, data: AddMemberRequest
    ) -> RoomResponse:
        try:
            room = await RoomRepository.get_room_by_id(db, room_id)
            if not room or room.room_type != RoomType.group:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Room ID {room_id} not found",
                )

            is_current_user_member = await RoomRepository.is_member(
                db, current_user_id, room_id
            )
            if not is_current_user_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Current user ID {current_user_id} is not a member of room ID {room_id}",
                )

            for user_data in data.data:
                if user_data.user_id <= 0:
                    continue
                is_member = await RoomRepository.is_member(
                    db, user_data.user_id, room_id
                )
                if is_member:
                    continue
                success = await RoomRepository.add_member(db, room_id, user_data)
                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to add user ID {user_data.user_id} to room ID {room_id}",
                    )
            room = await RoomRepository.get_room_by_id(db, room_id)
            members = await RoomRepository.list_members(db, room_id)
            member_ids = [member.user_id for member in members]
            return RoomResponse(
                id=room_id,
                name=room.name,
                room_type=room.room_type,
                created_at=room.created_at,
                member_ids=member_ids,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error adding user to room ID {room_id}: {e}",
            )

    @staticmethod
    async def remove_users_from_room(
        db: AsyncSession, current_user_id: int, room_id: int, data: RemoveMemberRequest
    ) -> RoomResponse:
        try:
            room = await RoomRepository.get_room_by_id(db, room_id)
            if not room or room.room_type != RoomType.group:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Room ID {room_id} not found",
                )

            is_owner = await RoomRepository.is_owner(db, current_user_id, room_id)
            if not is_owner:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Current user ID {current_user_id} is not the owner of room ID {room_id}",
                )

            for user_id in data.ids:
                is_user_owner = await RoomRepository.is_owner(db, user_id, room_id)
                if is_user_owner:
                    continue

                success = await RoomRepository.remove_member(db, user_id, room_id)
                if not success:
                    continue

            room = await RoomRepository.get_room_by_id(db, room_id)
            members = await RoomRepository.list_members(db, room_id)
            member_ids = [member.user_id for member in members]
            return RoomResponse(
                id=room_id,
                name=room.name,
                room_type=room.room_type,
                created_at=room.created_at,
                member_ids=member_ids,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error removing users from room ID {room_id}: {e}",
            )

    @staticmethod
    async def delete_room(db: AsyncSession, current_user_id: int, room_id: int):
        try:
            room = await RoomRepository.get_room_by_id(db, room_id)
            if not room:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Room ID {room_id} not found",
                )

            is_owner = await RoomRepository.is_owner(db, current_user_id, room_id)
            if not is_owner:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Only the room owner can delete room ID {room_id}",
                )

            success = await RoomRepository.delete_room(db, room_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to delete room ID {room_id}",
                )

            return {"detail": "Room deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error deleting room ID {room_id}: {e}",
            )
