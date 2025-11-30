from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from integration.text_generator_api import create_text_generator_api
from repository.message_repository import MessageRepository
from services.message_service import MessageService
from services.plan_service import PlanService
from services.route_service import RouteService
from utils.nlp.plan_validator import PlanValidator

SYSTEM_BOT_ID = 0

class ChatbotService:
    @staticmethod
    async def process_message(db: AsyncSession, user_id: int, room_id: int, user_text: str) -> Dict[str, Any]:
        text_generator_api = None
        try:
            # 1. Init LLM & Save User Message
            text_generator_api = await create_text_generator_api()
            await MessageRepository.create_text_message(db, user_id, room_id, user_text)

            # 2. Phân loại Intent & Xử lý Plan (Nếu có)
            # PlanService.handle_intent cần trả về Dict hoặc Pydantic model
            # Nếu user chỉ chat "Hello", handle_intent sẽ trả về action=None
            planner_result = await PlanService.handle_intent(db, user_id, room_id, user_text)
            
            # Lấy thông tin action (add/remove/modify...)
            # Nếu là object Pydantic thì dùng planner_result.action, nếu dict thì .get()
            action = planner_result.get("action") if isinstance(planner_result, dict) else getattr(planner_result, "action", None)
            
            # Dữ liệu plan để trả về frontend (Nên là Full List Destinations)
            plan_data = planner_result.get("data") if isinstance(planner_result, dict) else getattr(planner_result, "data", None)

            # 3. Logic tạo System Prompt
            base_system_prompt = (
                "Bạn là trợ lý du lịch thông minh của EcomoveX. "
                "Phong cách: Thân thiện, nhiệt tình, ngắn gọn.\n"
            )
            
            system_notes: List[str] = []

            # --- LOGIC QUAN TRỌNG: CHỈ TÍNH TOÁN KHI CÓ ACTION LIÊN QUAN PLAN ---
            if action and plan_data: 
                # a. Tính toán quãng đường (Chỉ chạy khi có plan)
                route_metrics = await RouteService.calculate_trip_metrics(plan_data)
                if route_metrics.get("total_distance_km", 0) > 0:
                    system_notes.append(
                        f"[INFO DI CHUYỂN]: Tổng quãng đường: {route_metrics['total_distance_km']}km, "
                        f"Thời gian: {route_metrics['total_duration_min']} phút."
                    )

                # b. Validate Plan (Chỉ chạy khi có plan)
                warnings = PlanValidator.validate_plan(plan_data)
                if warnings:
                    warning_msg = "; ".join(warnings)
                    system_notes.append(f"[GỢI Ý CHO USER]: {warning_msg}")
                
                # Cập nhật prompt để LLM biết vừa có thay đổi plan
                system_notes.insert(0, f"Hệ thống vừa thực hiện thao tác: {action}. Dữ liệu đã cập nhật.")

            # Ghép prompt
            if system_notes:
                extra_context = "\n".join(system_notes)
                system_prompt = (
                    f"{base_system_prompt}\n"
                    "--------------------------------------------------\n"
                    "THÔNG TIN HỆ THỐNG (Sử dụng để trả lời user, không bịa đặt số liệu):\n"
                    f"{extra_context}\n"
                    "--------------------------------------------------"
                )
            else:
                # Nếu chỉ chat thường, dùng prompt cơ bản
                system_prompt = base_system_prompt

            # 4. Chuẩn bị Messages cho LLM
            context = await MessageService.load_context(db, user_id, room_id)
            messages_for_llm = [{"role": "system", "content": system_prompt}]
            
            # Lấy lịch sử chat
            history = context.history if context.history else []
            for msg in history[-6:]: # Lấy 6 tin gần nhất là đủ context
                messages_for_llm.append({"role": msg.role, "content": msg.content})
            
            messages_for_llm.append({"role": "user", "content": user_text})

            # 5. Gọi LLM
            bot_reply = await text_generator_api.generate_reply(messages_for_llm)

            # 6. Save Bot Message & Update Context
            await MessageRepository.create_text_message(db, SYSTEM_BOT_ID, room_id, bot_reply)
            await MessageService.update_context_with_messages(context, user_text, bot_reply)

            # 7. TRẢ VỀ JSON CHO FRONTEND
            return {
                "ok": True,
                "message": bot_reply,     # Lời thoại của bot
                "action": action,         # Hành động vừa làm (add/remove/None)
                "plan": plan_data         # Dữ liệu Plan Mới Nhất (List) để Frontend render
            }

        except Exception as e:
            print(f"Chatbot Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Lỗi xử lý tin nhắn"
            )
        finally:
            if text_generator_api:
                await text_generator_api.close()