import asyncio
from chatbot_service_demo import ChatbotServiceDemo
from integration.text_generator_api import TextGeneratorAPI
from datetime import date
from sub_agents.opening_hours_agent import OpeningHoursAgent
from sub_agents.budget_check_agent import BudgetCheckAgent
from sub_agents.daily_calculation_agent import DailyCalculationAgent
from sub_agents.plan_validator_agent import PlanValidatorAgent
from services.chatbot_service_demo import ChatbotServiceDemo
from integration.text_generator_api import TextGeneratorAPI

# ================================
# 1. Fake plan JSON để test
# ================================
FAKE_PLAN = {
    "place_name": "TP HCM Trip",
    "start_date": date(2025, 12, 20),
    "end_date": date(2025, 12, 20),
    "budget_limit": 2000000,
    "destinations": [
        {
            "id": 1,
            "destination_id": "Bảo tàng Mỹ Thuật",
            "destination_type": "activity",
            "order_in_day": 1,
            "visit_date": date(2025, 12, 20),
            "estimated_cost": 50000,
            "note": "Sáng tham quan"
        },
        {
            "id": 2,
            "destination_id": "Ăn trưa tại Hum",
            "destination_type": "restaurant",
            "order_in_day": 2,
            "visit_date": date(2025, 12, 20),
            "estimated_cost": 150000,
            "note": "Ăn trưa"
        }
    ]
}

# ================================
# 2. Fake TextGeneratorAPI 
# (cho test, không gọi OpenRouter thật)
# ================================
class FakeTextAPI(TextGeneratorAPI):
    async def generate_reply(self, messages):
        print("\n=== LLM Input Messages ===")
        for m in messages:
            print(m)
        print("\n=== END Messages ===\n")

        return "Đây là câu trả lời test từ FakeTextAPI."


# ================================
# 3. MAIN TEST
# ================================
async def main():

    api = FakeTextAPI()
    chatbot = ChatbotServiceDemo(text_api=api)

    user_msg = "Ngày 20 có chỗ nào mở cửa buổi tối không?"

    response = await chatbot.handle_user_message(user_msg, FAKE_PLAN)

    print("\n============================")
    print("Kết quả cuối cùng:")
    print(response)
    print("============================\n")


if __name__ == "__main__":
    asyncio.run(main())
