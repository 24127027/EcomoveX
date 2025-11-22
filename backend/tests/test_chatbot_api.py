import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

# Assuming you have a FastAPI app instance
from main import app  # Adjust import based on your main file
from database.db import get_db
from models.user import User
from models.chatbot.planning import TravelPlan, ChatSessionContext

@pytest.mark.asyncio
async def test_send_message_to_chatbot():
    """Test sending a message to chatbot API"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Mock user authentication (adjust based on your auth system)
        headers = {"Authorization": "Bearer test_token"}
        
        payload = {
            "user_id": 1,
            "session_id": 1,
            "message": "Thêm nhà hàng chay ngày 2 lúc 19:00"
        }
        
        response = await client.post(
            "/api/chatbot/message",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "ok" in data
        assert "message" in data or "action" in data

@pytest.mark.asyncio
async def test_chatbot_add_activity():
    """Test adding activity through chatbot"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        headers = {"Authorization": "Bearer test_token"}
        
        payload = {
            "user_id": 1,
            "session_id": 1,
            "message": "Thêm tham quan Phố cổ Hội An ngày 1 lúc 09:00"
        }
        
        response = await client.post("/api/chatbot/message", json=payload, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["action"] == "add"
        assert "item" in data

@pytest.mark.asyncio
async def test_chatbot_view_plan():
    """Test viewing plan through chatbot"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        headers = {"Authorization": "Bearer test_token"}
        
        payload = {
            "user_id": 1,
            "session_id": 1,
            "message": "Xem kế hoạch hiện tại"
        }
        
        response = await client.post("/api/chatbot/message", json=payload, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["action"] == "view_plan"
        assert "plan" in data