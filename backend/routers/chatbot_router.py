
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.plan_schema import PlanCreate
from database.db import get_db
from schemas.message_schema import ChatMessage, ChatbotResponse
from services.agents.chatbot_service import ChatbotService
from services.agents.planner_agent import PlannerAgent

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

@router.post("/plan/generate")
async def generate_plan(request: Request, plan_data: PlanCreate, db: AsyncSession = Depends(get_db)):
    """
    Generate & validate plan with AI.
    Returns validated plan with AI suggestions and optimized order.
    """
    # Log raw body for debugging
    body = await request.body()
    print(f"📥 Raw request body: {body.decode()}")
    print(f"📥 Parsed plan_data: {plan_data.model_dump()}")

    agent = PlannerAgent(db)

    # Validate and get AI suggestions with intelligent distribution
    print("🤖 Running sub-agents with action='optimize'...")
    result = await agent._run_sub_agents(plan_data, action="optimize")
    print(f"✅ Sub-agents result: {len(result.get('distributed_plan', {}).get('destinations', []))} destinations")
    print(f"⚠️ Warnings: {len(result.get('warnings', []))}")
    print(f"📝 Modifications: {len(result.get('modifications', []))}")

    # Use the distributed plan if available, otherwise fall back to original
    distributed_plan = result.get("distributed_plan")
    if distributed_plan and distributed_plan.get("destinations"):
        # Use the intelligently distributed destinations
        final_destinations = distributed_plan["destinations"]
    else:
        # Fallback to original (shouldn't happen but safety first)
        final_destinations = [
            {
                "destination_id": d.destination_id,
                "destination_type": d.destination_type.value if hasattr(d.destination_type, 'value') else str(d.destination_type),
                "visit_date": str(d.visit_date),
                "order_in_day": d.order_in_day,
                "time_slot": d.time_slot.value if hasattr(d.time_slot, 'value') else str(d.time_slot),
                "note": d.note
            }
            for d in plan_data.destinations
        ]

    # Build final plan response with distributed destinations
    plan_dict = {
        "place_name": plan_data.place_name,
        "start_date": str(plan_data.start_date),
        "end_date": str(plan_data.end_date),
        "budget_limit": plan_data.budget_limit,
        "destinations": [
            {
                "destination_id": d.get("destination_id") if isinstance(d, dict) else d.destination_id,
                "destination_type": d.get("destination_type") or d.get("type") if isinstance(d, dict) else (d.destination_type.value if hasattr(d.destination_type, 'value') else str(d.destination_type)),
                "visit_date": str(d.get("visit_date")) if isinstance(d, dict) else str(d.visit_date),
                "order_in_day": d.get("order_in_day") if isinstance(d, dict) else d.order_in_day,
                "time_slot": d.get("time_slot") if isinstance(d, dict) else (d.time_slot.value if hasattr(d.time_slot, 'value') else str(d.time_slot)),
                "note": d.get("note") if isinstance(d, dict) else d.note
            }
            for d in final_destinations
        ]
    }

    # Generate success message
    num_days = (plan_data.end_date - plan_data.start_date).days + 1
    num_destinations = len(final_destinations)
    message = f"✅ Plan optimized successfully! {num_destinations} destinations distributed across {num_days} days."

    return {
        "success": True,
        "plan": plan_dict,
        "warnings": result.get("warnings", []),
        "modifications": result.get("modifications", []),
        "message": message
    }

@router.post("/message", response_model=ChatbotResponse, status_code=status.HTTP_200_OK)
async def send_message(chat_msg: ChatMessage, db: AsyncSession = Depends(get_db)):
    service = ChatbotService()
    result = await service.handle_user_message(
        db, chat_msg.user_id, chat_msg.room_id, chat_msg.message, chat_msg.current_plan
    )
    return result


# @router.post("/verify-green", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
# async def verify_green_transportation(
#     data: Dict[str, Any],
#     db: AsyncSession = Depends(get_db)
# ):
#     """
#     Verify green transportation method usage.

#     Request body:
#     {
#         "user_id": 1,
#         "transportation_type": "bicycle",  // bicycle, walking, electric_vehicle, public_transport
#         "image_url": "https://...",        // optional proof image
#         "location": {                       // optional GPS verification
#             "lat": 10.762622,
#             "lng": 106.660172
#         },
#         "timestamp": "2025-11-28T10:30:00"
#     }
#     """
#     return await ChatbotService.verify_green_transportation(db, data)
