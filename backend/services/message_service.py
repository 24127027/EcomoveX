import base64
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, Optional

from fastapi import HTTPException, UploadFile, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.datastructures import Headers

from repository.message_repository import MessageRepository
from repository.plan_repository import PlanRepository
from schemas.message_schema import *
from schemas.storage_schema import FileCategory
from services.room_service import RoomService
from services.socket_service import socket
from services.storage_service import StorageService
from utils.token.authentication_util import decode_access_token


from fastapi.encoders import jsonable_encoder

class MessageService:
    @staticmethod
    async def get_message_by_id(db: AsyncSession, user_id: int, message_id: int) -> MessageResponse:
        try:
            message = await MessageRepository.get_message_by_id(db, message_id)
            if not message:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Message ID {message_id} not found",
                )

            is_member = await RoomService.is_member(db, user_id, message.room_id)
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"User ID {user_id} is not a member of room ID {message.room_id}",
                )
            return await MessageService._map_to_response(message)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving message ID {message_id}: {e}",
            )

    @staticmethod
    async def get_message_by_keyword(
        db: AsyncSession, user_id: int, room_id: int, keyword: str
    ) -> list[MessageResponse]:
        try:
            if not keyword or not keyword.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Keyword cannot be empty",
                )

            is_member = await RoomService.is_member(db, user_id, room_id)
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"User ID {user_id} is not a member of room ID {room_id}",
                )
            messages = await MessageRepository.search_messages_by_keyword(db, room_id, keyword)
            if messages is None:
                return []
            import asyncio
            return await asyncio.gather(*[MessageService._map_to_response(msg) for msg in messages])
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error searching messages with keyword '{keyword}': {e}",
            )

    @staticmethod
    async def get_messages_by_room(
        db: AsyncSession, user_id: int, room_id: int
    ) -> list[MessageResponse]:
        try:
            is_member = await RoomService.is_member(db, user_id, room_id)
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"User ID {user_id} is not a member of room ID {room_id}",
                )
            messages = await MessageRepository.get_messages_by_room(db, room_id)
            if messages is None:
                return []
            import asyncio
            return await asyncio.gather(*[MessageService._map_to_response(msg) for msg in messages])
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving messages for room ID {room_id}: {e}",
            )

    @staticmethod
    async def create_message(
        db: AsyncSession,
        sender_id: int,
        room_id: int,
        message_text: Optional[str] = None,
        message_file: Optional[UploadFile] = None,
        plan_id: Optional[int] = None,
        message_type: MessageType = MessageType.text,
    ) -> MessageResponse:
        try:
            is_member = await RoomService.is_member(db, sender_id, room_id)
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"User ID {sender_id} is not a member of room ID {room_id}",
                )

            if not message_text and not message_file and message_type != MessageType.invitation:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Either message text or message file must be provided",
                )

            if message_type == MessageType.invitation:
                if not plan_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Plan ID is required for invitation messages",
                    )
                saved_msg = await MessageRepository.create_invitation_message(
                    db, sender_id, room_id, plan_id, message_text or "Invitation to join plan"
                )
            elif message_file:
                file = await StorageService.upload_file(
                    db=db,
                    file=message_file,
                    user_id=sender_id,
                    category=FileCategory.message,
                )
                saved_msg = await MessageRepository.create_file_message(
                    db, sender_id, room_id, file.blob_name
                )
            else:
                saved_msg = await MessageRepository.create_text_message(
                    db, sender_id, room_id, message_text
                )

            if not saved_msg:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create message",
                )

            url = None
            content = saved_msg.content
            if message_file and 'file' in locals():
                 url = file.url
                 if not content:
                     content = url

            response = MessageResponse(
                id=saved_msg.id,
                content=content,
                sender_id=saved_msg.sender_id,
                room_id=room_id,
                plan_id=saved_msg.plan_id,
                message_type=saved_msg.message_type,
                status=saved_msg.status,
                timestamp=saved_msg.created_at,
                url=url
            )

            # Broadcast to room
            await socket.broadcast(jsonable_encoder(response), room_id)

            return response
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error creating message in room ID {room_id}: {e}",
            )

    @staticmethod
    async def delete_message(db: AsyncSession, sender_id: int, message_id: int):
        try:
            message = await MessageRepository.get_message_by_id(db, message_id)
            if not message:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Message ID {message_id} not found",
                )

            if message.sender_id != sender_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User does not have permission to delete this message",
                )

            success = await MessageRepository.delete_message(db, message_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to delete message with ID {message_id}",
                )
            return {"detail": "Message deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error deleting message ID {message_id}: {e}",
            )

    @staticmethod
    async def handle_websocket_text_message(
        db: AsyncSession,
        user_id: int,
        room_id: int,
        message_text: Optional[str] = None,
    ) -> MessageResponse:
        try:
            return await MessageService.create_message(db, user_id, room_id, message_text)
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing message",
            )

    @staticmethod
    async def handle_websocket_file_message(
        db: AsyncSession,
        user_id: int,
        room_id: int,
        file_data_base64: str,
        filename: str,
        content_type: str,
    ) -> MessageResponse:
        try:
            file_bytes = base64.b64decode(file_data_base64)

            file_stream = BytesIO(file_bytes)

            upload_file = UploadFile(
                file=file_stream,
                filename=filename,
                headers=Headers({"content-type": content_type}),
            )

            saved_msg = await MessageService.create_message(
                db, user_id, room_id, message_text=None, message_file=upload_file
            )

            return saved_msg

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing file message: {str(e)}",
            )

    @staticmethod
    async def handle_websocket_connection(
        websocket: WebSocket, db: AsyncSession, room_id: int, token: str
    ):
        user_id = None
        try:
            try:
                user_data = decode_access_token(token)
                user_id = user_data["user_id"]
            except Exception:
                await websocket.close(code=1008)
                return None

            is_member = await RoomService.is_member(db, user_id, room_id)
            if not is_member:
                await websocket.close(code=1008)
                return None

            await socket.connect(websocket, room_id, user_id)
            return user_id
        except Exception as e:
            if user_id:
                socket.disconnect(websocket, room_id, user_id)
                print(f"🔴 WEBSOCKET ERROR: {e}")
            return None

    @staticmethod
    async def handle_websocket_message_loop(
        websocket: WebSocket, db: AsyncSession, user_id: int, room_id: int
    ):
        try:
            while True:
                data = await websocket.receive_json()
                msg_type = data.get("type", "text")

                if msg_type == "file":
                    file_data = data.get("data")  # Base64 encoded
                    filename = data.get("filename", "file")
                    content_type = data.get("content_type", "application/octet-stream")

                    if not file_data:
                        await socket.send_to_user(
                            {"error": "File data is required"}, room_id, user_id
                        )
                        continue

                    response = await MessageService.handle_websocket_file_message(
                        db, user_id, room_id, file_data, filename, content_type
                    )
                else:
                    content = data.get("content")
                    if not content:
                        await socket.send_to_user(
                            {"error": "Content is required"}, room_id, user_id
                        )
                        continue

                    response = await MessageService.handle_websocket_text_message(
                        db, user_id, room_id, message_text=content
                    )

                response_data = response.model_dump(mode="json")
                await socket.broadcast(response_data, room_id)

        except WebSocketDisconnect:
            print(f"User {user_id} disconnected from room {room_id}")
            socket.disconnect(websocket, room_id, user_id)
        except Exception as e:
            print(f"🔴 WEBSOCKET ERROR: {e}")
            import traceback

            traceback.print_exc()

            socket.disconnect(websocket, room_id, user_id)
            try:
                await websocket.close(code=1011)
            except Exception:
                pass

    @staticmethod
    async def load_context(db: AsyncSession, user_id: int, room_id: int) -> ContextLoadResponse:
        try:
            # Get messages from the room
            messages = await MessageRepository.get_messages_by_room(db, room_id)

            history = []
            if messages:
                sorted_messages = sorted(messages, key=lambda m: m.created_at)
                recent_messages = sorted_messages[-20:]

                for msg in recent_messages:
                    role = "assistant" if msg.sender_id == 0 else "user"
                    history.append(
                        MessageHistoryItem(
                            role=role,
                            content=msg.content or "",
                            timestamp=msg.created_at,
                        )
                    )

            # Load room context
            room_context = await MessageRepository.load_room_context(db, room_id)

            stored_context = None
            if "stored_context" in room_context:
                stored_context = StoredContextData(**room_context["stored_context"])

            active_trip = None
            activities = []

            if "active_trip_id" in room_context:
                trip_id = room_context["active_trip_id"]
                trip = await PlanRepository.get_plan_by_id(db, trip_id)

                if trip:
                    active_trip = ActiveTripData(
                        trip_id=trip.id,
                        destination=trip.destination,
                        start_date=trip.start_date,
                        end_date=trip.end_date,
                        budget=trip.budget if hasattr(trip, "budget") else None,
                        preferences=room_context.get("trip_preferences", {}),
                    )

            return ContextLoadResponse(
                history=history,
                stored_context=stored_context,
                active_trip=active_trip,
                activities=activities,
                room_context=room_context,
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error loading context for room {room_id}: {str(e)}",
            )

    @staticmethod
    async def update_context_with_messages(
        context: ContextLoadResponse, user_msg: str, bot_msg: str, max_history: int = 20
    ) -> ContextLoadResponse:
        try:
            context.history.append(
                MessageHistoryItem(role="user", content=user_msg, timestamp=datetime.utcnow())
            )
            context.history.append(
                MessageHistoryItem(role="assistant", content=bot_msg, timestamp=datetime.utcnow())
            )

            context.history = context.history[-max_history:]

            return context

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating context: {str(e)}",
            )

    @staticmethod
    async def save_room_context(
        db: AsyncSession, room_id: int, key: str, value: Optional[Dict[str, Any]] = None
    ) -> SessionContextResponse:
        try:
            context_data = RoomContextCreate(room_id=room_id, key=key, value=value)

            context = await MessageRepository.save_room_context(db, context_data)

            if not context:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to save context for room {room_id}",
                )

            return SessionContextResponse(
                room_id=context.room_id,
                key=context.key,
                value=context.value,
                updated_at=context.updated_at,
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving room context: {str(e)}",
            )

    @staticmethod
    async def get_room_context(db: AsyncSession, room_id: int, key: str) -> Optional[Any]:
        try:
            value = await MessageRepository.get_room_context(db, room_id, key)
            return value

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving room context: {str(e)}",
            )

    @staticmethod
    async def load_all_room_context(db: AsyncSession, room_id: int) -> SessionContextResponse:
        try:
            context = await MessageRepository.load_room_context(db, room_id)
            return SessionContextResponse(data=context)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error loading all room context: {str(e)}",
            )

    @staticmethod
    async def delete_room_context(db: AsyncSession, room_id: int, key: str) -> bool:
        try:
            success = await MessageRepository.delete_room_context(db, room_id, key)

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Context key '{key}' not found for room {room_id}",
                )

            return success

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting room context: {str(e)}",
            )

    @staticmethod
    async def clear_room_context(db: AsyncSession, room_id: int) -> bool:
        try:
            success = await MessageRepository.clear_room_context(db, room_id)

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to clear context for room {room_id}",
                )

            return success

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error clearing room context: {str(e)}",
            )

    @staticmethod
    async def save_stored_context(
        db: AsyncSession, room_id: int, stored_context: StoredContextData
    ) -> SessionContextResponse:
        try:
            return await MessageService.save_room_context(
                db,
                room_id,
                "stored_context",
                stored_context.model_dump(exclude_none=True),
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving stored context: {str(e)}",
            )

    @staticmethod
    async def save_active_trip_context(
        db: AsyncSession,
        room_id: int,
        trip_id: int,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> SessionContextResponse:
        try:
            await MessageService.save_room_context(
                db, room_id, "active_trip_id", {"trip_id": trip_id}
            )

            if preferences:
                return await MessageService.save_room_context(
                    db, room_id, "trip_preferences", preferences
                )

            return SessionContextResponse(
                room_id=room_id,
                key="active_trip_id",
                value={"trip_id": trip_id},
                updated_at=datetime.utcnow(),
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving active trip context: {str(e)}",
            )

    @staticmethod
    async def remove_active_trip_context(db: AsyncSession, room_id: int) -> bool:
        try:
            await MessageRepository.delete_room_context(db, room_id, "active_trip_id")
            await MessageRepository.delete_room_context(db, room_id, "trip_preferences")
            return True

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error removing active trip context: {str(e)}",
            )

    @staticmethod
    async def decline_invitation(db: AsyncSession, user_id: int, message_id: int) -> MessageResponse:
        try:
            message = await MessageRepository.get_message_by_id(db, message_id)
            if not message:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Message ID {message_id} not found",
                )

            is_member = await RoomService.is_member(db, user_id, message.room_id)
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"User ID {user_id} is not a member of room ID {message.room_id}",
                )

            if message.message_type != MessageType.invitation:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Message is not an invitation",
                )

            # Update content to indicate declined
            message.content = "Invitation Declined"
            # We might want to clear plan_id so the button disappears or stays as history
            # message.plan_id = None 
            
            await db.commit()
            await db.refresh(message)

            response = MessageResponse(
                id=message.id,
                content=message.content,
                sender_id=message.sender_id,
                room_id=message.room_id,
                plan_id=message.plan_id,
                message_type=message.message_type,
                status=message.status,
                timestamp=message.created_at,
            )

            # Broadcast update
            await socket.broadcast(jsonable_encoder(response), message.room_id)

            return response
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error declining invitation {message_id}: {e}",
            )

    @staticmethod
    async def _map_to_response(msg) -> MessageResponse:
        url = None
        content = msg.content
        if msg.message_type == MessageType.file and msg.file_metadata:
            url = await StorageService.generate_signed_url(
                msg.file_metadata.blob_name, msg.file_metadata.bucket
            )
            if not content:
                content = url
        
        return MessageResponse(
            id=msg.id,
            sender_id=msg.sender_id,
            room_id=msg.room_id,
            content=content,
            message_type=msg.message_type,
            status=msg.status,
            timestamp=msg.created_at,
            plan_id=msg.plan_id,
            url=url
        )
