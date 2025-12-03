import base64
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, UploadFile, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.datastructures import Headers

from repository.message_repository import MessageRepository
from repository.plan_repository import PlanRepository
from schemas.message_schema import (
    ActivePlanContext,
    ActiveTripData,
    ContextLoadResponse,
    ConversationState,
    DestinationContext,
    LLMContextData,
    MessageHistoryItem,
    MessageResponse,
    PlanDestinationContext,
    RoomContextCreate,
    SessionContextResponse,
    StoredContextData,
    UserPreferences,
)
from models.message import MessageType
from schemas.storage_schema import FileCategory
from services.room_service import RoomService
from services.socket_service import socket
from services.storage_service import StorageService
from utils.token.authentication_util import decode_access_token


from fastapi.encoders import jsonable_encoder


class MessageService:
    @staticmethod
    async def get_message_by_id(
        db: AsyncSession, user_id: int, message_id: int
    ) -> MessageResponse:
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
            return MessageResponse(
                id=message.id,
                sender_id=message.sender_id,
                room_id=message.room_id,
                content=message.content,
                message_type=message.message_type,
                status=message.status,
                timestamp=message.created_at,
            )
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
            messages = await MessageRepository.search_messages_by_keyword(
                db, room_id, keyword
            )
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
            message_list = [
                MessageResponse(
                    id=msg.id,
                    sender_id=msg.sender_id,
                    room_id=msg.room_id,
                    content=msg.content,
                    message_type=msg.message_type,
                    status=msg.status,
                    timestamp=msg.created_at,
                )
                for msg in messages
            ]
            return message_list
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
        message_type: MessageType = MessageType.text,
    ) -> MessageResponse:
        try:
            is_member = await RoomService.is_member(db, sender_id, room_id)
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"User ID {sender_id} is not a member of room ID {room_id}",
                )

            if not message_text and not message_file:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Either message text or message file must be provided",
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
                message_type=saved_msg.message_type,
                status=saved_msg.status,
                timestamp=saved_msg.created_at,
                url=url
            )

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
            return await MessageService.create_message(
                db, user_id, room_id, message_text
            )
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
    async def load_context(
        db: AsyncSession, user_id: int, room_id: int
    ) -> ContextLoadResponse:
        try:
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

            room_context = await MessageRepository.load_room_context(db, room_id)

            user_preferences = None
            if "user_preferences" in room_context:
                pref_data = room_context["user_preferences"]
                user_preferences = UserPreferences(**pref_data) if pref_data else None

            active_plan_context = None
            plans = await PlanRepository.get_plan_by_user_id(db, user_id)
            if plans and len(plans) > 0:
                active_plan_id = room_context.get("active_plan_id")
                if active_plan_id:
                    plan = await PlanRepository.get_plan_by_id(db, active_plan_id)
                else:
                    plan = plans[0]

                if plan:
                    destinations = await PlanRepository.get_plan_destinations(
                        db, plan.id
                    )
                    dest_contexts = []
                    for dest in destinations:
                        dest_contexts.append(
                            PlanDestinationContext(
                                id=dest.id,
                                destination_id=dest.destination_id,
                                name=(
                                    dest.destination.name
                                    if hasattr(dest, "destination") and dest.destination
                                    else None
                                ),
                                visit_date=(
                                    str(dest.visit_date) if dest.visit_date else None
                                ),
                                time_slot=(
                                    dest.time_slot.value if dest.time_slot else None
                                ),
                                order_in_day=dest.order_in_day,
                                note=dest.note,
                            )
                        )

                    active_plan_context = ActivePlanContext(
                        plan_id=plan.id,
                        place_name=plan.place_name,
                        start_date=str(plan.start_date) if plan.start_date else None,
                        end_date=str(plan.end_date) if plan.end_date else None,
                        budget_limit=plan.budget_limit,
                        destinations=dest_contexts,
                    )

            conversation_state = ConversationState(
                current_intent=room_context.get("current_intent"),
                pending_action=room_context.get("pending_action"),
                last_mentioned_destination=(
                    DestinationContext(**room_context["last_destination"])
                    if "last_destination" in room_context
                    and room_context["last_destination"]
                    else None
                ),
                last_mentioned_date=room_context.get("last_date"),
                last_mentioned_time_slot=room_context.get("last_time_slot"),
                awaiting_confirmation=room_context.get("awaiting_confirmation", False),
                missing_params=room_context.get("missing_params", []),
            )

            llm_context = LLMContextData(
                user_id=user_id,
                user_preferences=user_preferences,
                active_plan=active_plan_context,
                conversation_state=conversation_state,
                custom_data=room_context.get("custom_data", {}),
            )

            stored_context = None
            if "stored_context" in room_context:
                stored_context = StoredContextData(**room_context["stored_context"])

            active_trip = None
            if "active_trip_id" in room_context:
                trip_data = room_context["active_trip_id"]
                trip_id = (
                    trip_data["trip_id"] if isinstance(trip_data, dict) else trip_data
                )
                trip = await PlanRepository.get_plan_by_id(db, trip_id)

                if trip:
                    active_trip = ActiveTripData(
                        trip_id=trip.id,
                        place_name=trip.place_name,
                        start_date=trip.start_date,
                        end_date=trip.end_date,
                        budget_limit=trip.budget_limit,
                        preferences=room_context.get("trip_preferences", {}),
                    )

            return ContextLoadResponse(
                history=history,
                llm_context=llm_context,
                stored_context=stored_context,
                active_trip=active_trip,
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
                MessageHistoryItem(
                    role="user", content=user_msg, timestamp=datetime.now(timezone.utc)
                )
            )
            context.history.append(
                MessageHistoryItem(
                    role="assistant",
                    content=bot_msg,
                    timestamp=datetime.now(timezone.utc),
                )
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
    async def get_room_context(
        db: AsyncSession, room_id: int
    ) -> List[SessionContextResponse]:
        try:
            values = await MessageRepository.get_room_context(db, room_id)
            return [
                SessionContextResponse(
                    room_id=value.room_id,
                    key=value.key,
                    value=value.value,
                    updated_at=value.updated_at,
                )
                for value in values
            ]

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving room context: {str(e)}",
            )

    @staticmethod
    async def load_all_room_context(
        db: AsyncSession, room_id: int
    ) -> List[SessionContextResponse]:
        try:
            contexts = await MessageRepository.get_room_context(db, room_id)
            return [
                SessionContextResponse(
                    room_id=context.room_id,
                    key=context.key,
                    value=context.value,
                    updated_at=context.updated_at,
                )
                for context in contexts
            ]

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error loading all room context: {str(e)}",
            )

    @staticmethod
    async def delete_room_context(db: AsyncSession, room_id: int, key: str):
        try:
            success = await MessageRepository.delete_room_context(db, room_id, key)

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Context key '{key}' not found for room {room_id}",
                )

            return {"detail": "Room context deleted successfully"}

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting room context: {str(e)}",
            )

    @staticmethod
    async def clear_room_context(db: AsyncSession, room_id: int):
        try:
            success = await MessageRepository.clear_room_context(db, room_id)

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to clear context for room {room_id}",
                )

            return {"detail": "Room context cleared successfully"}

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
            response = await MessageService.save_room_context(
                db, room_id, "active_trip_id", {"trip_id": trip_id}
            )

            if preferences:
                await MessageService.save_room_context(
                    db, room_id, "trip_preferences", preferences
                )

            return response

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
    async def update_conversation_state(
        db: AsyncSession,
        room_id: int,
        current_intent: Optional[str] = None,
        pending_action: Optional[str] = None,
        last_destination: Optional[Dict[str, Any]] = None,
        last_date: Optional[str] = None,
        last_time_slot: Optional[str] = None,
        awaiting_confirmation: bool = False,
        missing_params: Optional[List[str]] = None,
    ):
        try:
            if current_intent is not None:
                await MessageService.save_room_context(
                    db, room_id, "current_intent", {"value": current_intent}
                )
            if pending_action is not None:
                await MessageService.save_room_context(
                    db, room_id, "pending_action", {"value": pending_action}
                )
            if last_destination is not None:
                await MessageService.save_room_context(
                    db, room_id, "last_destination", last_destination
                )
            if last_date is not None:
                await MessageService.save_room_context(
                    db, room_id, "last_date", {"value": last_date}
                )
            if last_time_slot is not None:
                await MessageService.save_room_context(
                    db, room_id, "last_time_slot", {"value": last_time_slot}
                )

            await MessageService.save_room_context(
                db, room_id, "awaiting_confirmation", {"value": awaiting_confirmation}
            )

            if missing_params is not None:
                await MessageService.save_room_context(
                    db, room_id, "missing_params", {"value": missing_params}
                )

        except Exception as e:
            print(f"Warning: Failed to update conversation state: {e}")

    @staticmethod
    async def set_active_plan(db: AsyncSession, room_id: int, plan_id: int):
        try:
            await MessageService.save_room_context(
                db, room_id, "active_plan_id", {"value": plan_id}
            )
        except Exception as e:
            print(f"Warning: Failed to set active plan: {e}")

    @staticmethod
    async def save_user_preferences(
        db: AsyncSession,
        room_id: int,
        preferences: Dict[str, Any],
    ):
        try:
            await MessageService.save_room_context(
                db, room_id, "user_preferences", preferences
            )
        except Exception as e:
            print(f"Warning: Failed to save user preferences: {e}")

    @staticmethod
    async def clear_conversation_state(db: AsyncSession, room_id: int):
        try:
            keys_to_clear = [
                "current_intent",
                "pending_action",
                "last_destination",
                "last_date",
                "last_time_slot",
                "awaiting_confirmation",
                "missing_params",
            ]
            for key in keys_to_clear:
                await MessageRepository.delete_room_context(db, room_id, key)
        except Exception as e:
            print(f"Warning: Failed to clear conversation state: {e}")

    @staticmethod
    def build_llm_system_prompt(llm_context: LLMContextData) -> str:
        prompt_parts = [
            "You are EcomoveX's intelligent travel assistant.",
            "Style: Friendly, enthusiastic, concise.",
            "",
            "=== CONTEXT INFORMATION ===",
        ]

        if llm_context.user_preferences:
            pref = llm_context.user_preferences
            prompt_parts.append("\n[USER PREFERENCES]")
            if pref.preferred_activities:
                prompt_parts.append(
                    f"- Preferred activities: {', '.join(pref.preferred_activities)}"
                )
            if pref.budget_range:
                prompt_parts.append(f"- Budget: {pref.budget_range}")
            if pref.travel_style:
                prompt_parts.append(f"- Travel style: {pref.travel_style}")

        if llm_context.active_plan:
            plan = llm_context.active_plan
            prompt_parts.append("\n[CURRENT PLAN]")
            prompt_parts.append(f"- Plan ID: {plan.plan_id}")
            prompt_parts.append(f"- Destination: {plan.place_name}")
            if plan.start_date and plan.end_date:
                prompt_parts.append(f"- Duration: {plan.start_date} to {plan.end_date}")
            if plan.budget_limit:
                prompt_parts.append(f"- Budget: {plan.budget_limit:,.0f} VND")

            if plan.destinations:
                prompt_parts.append(
                    f"\n[PLANNED DESTINATIONS] ({len(plan.destinations)} places)"
                )
                for i, dest in enumerate(plan.destinations, 1):
                    dest_info = f"  {i}. ID={dest.id}"
                    if dest.name:
                        dest_info += f", {dest.name}"
                    if dest.visit_date:
                        dest_info += f", date {dest.visit_date}"
                    if dest.time_slot:
                        dest_info += f", {dest.time_slot}"
                    prompt_parts.append(dest_info)

        state = llm_context.conversation_state
        if state.current_intent or state.pending_action:
            prompt_parts.append("\n[CONVERSATION STATE]")
            if state.current_intent:
                prompt_parts.append(f"- Current intent: {state.current_intent}")
            if state.pending_action:
                prompt_parts.append(f"- Pending action: {state.pending_action}")
            if state.last_mentioned_destination:
                dest = state.last_mentioned_destination
                prompt_parts.append(
                    f"- Last mentioned destination: {dest.name or dest.destination_id}"
                )
            if state.last_mentioned_date:
                prompt_parts.append(
                    f"- Last mentioned date: {state.last_mentioned_date}"
                )
            if state.missing_params:
                prompt_parts.append(
                    f"- Missing parameters: {', '.join(state.missing_params)}"
                )

        prompt_parts.append("\n=== END CONTEXT ===")

        return "\n".join(prompt_parts)
