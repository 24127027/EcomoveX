from fastapi import HTTPException, status, WebSocket, WebSocketDisconnect
from repository.message_repository import MessageRepository
from repository.plan_repository import PlanRepository
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.message_schema import *
from services.room_service import RoomService
from services.socket_service import socket
from utils.token.authentication_util import decode_access_token
from typing import Optional, Dict, Any, List
from datetime import datetime

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
            is_member = await RoomService.is_member(db, user_id, room_id)
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
            is_member = await RoomService.is_member(db, user_id, room_id)
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
            is_member = await RoomService.is_member(db, sender_id, room_id)
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
    
    @staticmethod
    async def handle_websocket_message(
        db: AsyncSession,
        user_id: int,
        room_id: int,
        msg_request: WebSocketMessageRequest
    ) -> WebSocketMessageResponse:
        try:
            msg_input = MessageCreate(content=msg_request.content, message_type=msg_request.message_type)
            saved_msg = await MessageService.create_message(db, user_id, room_id, msg_input)
            
            return WebSocketMessageResponse(
                type="message",
                id=saved_msg.id,
                content=saved_msg.content,
                sender_id=saved_msg.sender_id,
                room_id=room_id,
                timestamp=saved_msg.timestamp.isoformat(),
                message_type=saved_msg.message_type,
                status=saved_msg.status
            )
        except HTTPException as e:
            raise HTTPException(
                status_code=e.status_code,
                detail=e.detail
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing message"
            )
            
    @staticmethod
    async def handle_websocket_connection(websocket: WebSocket, db: AsyncSession, room_id: int, token: str):
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
                print(f"BẮT ĐƯỢC LỖI SOCKET: {e}")  # <--- Thêm dòng này
            return None
        
    @staticmethod
    async def handle_websocket_message_loop(websocket: WebSocket, db: AsyncSession, user_id: int, room_id: int):
        try:
            while True:
                data = await websocket.receive_json()
                request = WebSocketMessageRequest(
                    content=data.get("content"),
                    message_type=data.get("message_type", "text")
                )
                
                response = await MessageService.handle_websocket_message(db, user_id, room_id, request)
                response_data = response.model_dump(mode='json')
                if response.type == "message":
                    await socket.broadcast(response_data, room_id)
                else:
                    await socket.send_to_user(response_data, room_id, user_id)
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
    async def load_context(
        db: AsyncSession,
        user_id: int,
        session_id: int
    ) -> ContextLoadResponse:
        try:
            session = await MessageRepository.get_session_by_id(
                db,
                session_id,
                include_messages=True,
                include_contexts=True
            )
            
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Chat session {session_id} not found"
                )

            history = []
            if session.messages:
                sorted_messages = sorted(session.messages, key=lambda m: m.created_at)
                recent_messages = sorted_messages[-20:]
                
                for msg in recent_messages:
                    role = "assistant" if msg.sender_id == 0 else "user"
                    history.append(MessageHistoryItem(
                        role=role,
                        content=msg.content or "",
                        timestamp=msg.created_at
                    ))

            session_context = {}
            if session.contexts:
                session_context = {ctx.key: ctx.value for ctx in session.contexts}

            stored_context = None
            if "stored_context" in session_context:
                stored_context = StoredContextData(**session_context["stored_context"])

            active_trip = None
            activities = []
            
            if "active_trip_id" in session_context:
                trip_id = session_context["active_trip_id"]
                trip = await PlanRepository.get_plan_by_id(db, trip_id)
                
                if trip:
                    active_trip = ActiveTripData(
                        trip_id=trip.id,
                        destination=trip.destination,
                        start_date=trip.start_date,
                        end_date=trip.end_date,
                        budget=trip.budget if hasattr(trip, 'budget') else None,
                        preferences=session_context.get("trip_preferences", {})
                    )
                    
            return ContextLoadResponse(
                history=history,
                stored_context=stored_context,
                active_trip=active_trip,
                activities=activities,
                session_context=session_context
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error loading context for session {session_id}: {str(e)}"
            )

    @staticmethod
    async def update_context_with_messages(
        context: ContextLoadResponse,
        user_msg: str,
        bot_msg: str,
        max_history: int = 20
    ) -> ContextLoadResponse:
        try:
            context.history.append(MessageHistoryItem(
                role="user",
                content=user_msg,
                timestamp=datetime.utcnow()
            ))
            context.history.append(MessageHistoryItem(
                role="assistant",
                content=bot_msg,
                timestamp=datetime.utcnow()
            ))
            
            context.history = context.history[-max_history:]
            
            return context

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating context: {str(e)}"
            )

    @staticmethod
    async def save_session_context(
        db: AsyncSession,
        session_id: int,
        key: str,
        value: Optional[Dict[str, Any]] = None
    ) -> SessionContextResponse:
        try:
            context_data = ChatSessionContextCreate(
                session_id=session_id,
                key=key,
                value=value
            )
            
            context = await MessageRepository.save_session_context(db, context_data)
            
            if not context:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to save context for session {session_id}"
                )

            return SessionContextResponse(
                session_id=context.session_id,
                key=context.key,
                value=context.value,
                updated_at=context.updated_at
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving session context: {str(e)}"
            )

    @staticmethod
    async def get_session_context(
        db: AsyncSession,
        session_id: int,
        key: str
    ) -> Optional[Any]:
        try:
            value = await MessageRepository.get_session_context(db, session_id, key)
            return value

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving session context: {str(e)}"
            )

    @staticmethod
    async def load_all_session_context(
        db: AsyncSession,
        session_id: int
    ) -> SessionContextResponse:
        try:
            context = await MessageRepository.load_session_context(db, session_id)
            return SessionContextResponse(data=context)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error loading all session context: {str(e)}"
            )

    @staticmethod
    async def delete_session_context(
        db: AsyncSession,
        session_id: int,
        key: str
    ) -> bool:
        try:
            success = await MessageRepository.delete_session_context(db, session_id, key)
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Context key '{key}' not found for session {session_id}"
                )
            
            return success

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting session context: {str(e)}"
            )

    @staticmethod
    async def clear_session_context(
        db: AsyncSession,
        session_id: int
    ) -> bool:
        try:
            success = await MessageRepository.clear_session_context(db, session_id)
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to clear context for session {session_id}"
                )
            
            return success

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error clearing session context: {str(e)}"
            )

    @staticmethod
    async def save_stored_context(
        db: AsyncSession,
        session_id: int,
        stored_context: StoredContextData
    ) -> SessionContextResponse:
        try:
            return await MessageService.save_session_context(
                db,
                session_id,
                "stored_context",
                stored_context.model_dump(exclude_none=True)
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving stored context: {str(e)}"
            )

    @staticmethod
    async def save_active_trip_context(
        db: AsyncSession,
        session_id: int,
        trip_id: int,
        preferences: Optional[Dict[str, Any]] = None
    ) -> SessionContextResponse:
        try:
            await MessageService.save_session_context(
                db,
                session_id,
                "active_trip_id",
                {"trip_id": trip_id}
            )
            
            if preferences:
                return await MessageService.save_session_context(
                    db,
                    session_id,
                    "trip_preferences",
                    preferences
                )
            
            return SessionContextResponse(
                session_id=session_id,
                key="active_trip_id",
                value={"trip_id": trip_id},
                updated_at=datetime.utcnow()
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving active trip context: {str(e)}"
            )

    @staticmethod
    async def remove_active_trip_context(
        db: AsyncSession,
        session_id: int
    ) -> bool:
        try:
            await MessageRepository.delete_session_context(db, session_id, "active_trip_id")
            await MessageRepository.delete_session_context(db, session_id, "trip_preferences")
            return True

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error removing active trip context: {str(e)}"
            )