from typing import Any, Dict, List

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from repository.plan_repository import PlanRepository
from integration.text_generator_api import create_text_generator_api
from repository.message_repository import MessageRepository
from services.message_service import MessageService
from services.plan_service import PlanService
from services.route_service import RouteService
from utils.nlp.plan_validator import PlanValidator

SYSTEM_BOT_ID = 0


class ChatbotService:
    @staticmethod
    async def process_message(
        db: AsyncSession, user_id: int, room_id: int, user_text: str
    ) -> Dict[str, Any]:
        text_generator_api = None
        try:
            text_generator_api = await create_text_generator_api()
            await MessageRepository.create_text_message(db, user_id, room_id, user_text)

            context = await MessageService.load_context(db, user_id, room_id)

            planner_result = await PlanService.handle_intent(
                db, user_id, room_id, user_text
            )

            action = (
                planner_result.get("action")
                if isinstance(planner_result, dict)
                else getattr(planner_result, "action", None)
            )
            plan_id = (
                planner_result.get("plan_id")
                if isinstance(planner_result, dict)
                else getattr(planner_result, "plan_id", None)
            )

            plan_data = None
            if action in ["add", "remove", "modify_time"] and plan_id:
                plan_data = await PlanRepository.get_plan_destinations(db, plan_id)

            if context.llm_context:
                base_system_prompt = MessageService.build_llm_system_prompt(
                    context.llm_context
                )
            else:
                base_system_prompt = (
                    "You are EcomoveX's intelligent travel assistant. "
                    "Style: Friendly, enthusiastic, concise.\n"
                )

            system_notes: List[str] = []

            if action in ["add", "remove", "modify_time"] and plan_data is not None:
                route_metrics = await RouteService.calculate_trip_metrics(plan_data)
                if route_metrics.get("total_distance_km", 0) > 0:
                    system_notes.append(
                        f"[TRAVEL INFO]: Total distance: {route_metrics['total_distance_km']}km, "
                        f"Duration: {route_metrics['total_duration_min']} minutes."
                    )

                warnings = PlanValidator.validate_plan(plan_data)
                if warnings:
                    warning_msg = "; ".join(warnings)
                    system_notes.append(f"[SUGGESTIONS FOR USER]: {warning_msg}")

                system_notes.insert(
                    0,
                    f"System has performed action: {action}. Data has been updated.",
                )

                await MessageService.clear_conversation_state(db, room_id)

            if system_notes:
                extra_context = "\n".join(system_notes)
                system_prompt = (
                    f"{base_system_prompt}\n"
                    "--------------------------------------------------\n"
                    "SYSTEM INFORMATION (Use to answer user, do not fabricate data):\n"
                    f"{extra_context}\n"
                    "--------------------------------------------------"
                )
            else:
                system_prompt = base_system_prompt

            messages_for_llm = [{"role": "system", "content": system_prompt}]

            history = context.history if context.history else []
            for msg in history[-6:]:
                messages_for_llm.append({"role": msg.role, "content": msg.content})

            messages_for_llm.append({"role": "user", "content": user_text})

            bot_reply = await text_generator_api.generate_reply(messages_for_llm)

            await MessageRepository.create_text_message(
                db, SYSTEM_BOT_ID, room_id, bot_reply
            )
            await MessageService.update_context_with_messages(
                context, user_text, bot_reply
            )

            return {
                "ok": True,
                "message": bot_reply,
                "action": action,
                "plan": plan_data,
            }

        except Exception as e:
            print(f"Chatbot Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing message",
            )
        finally:
            if text_generator_api:
                await text_generator_api.close()
