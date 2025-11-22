import sys
from pathlib import Path
from sqlalchemy import text as sql_text  # Rename to avoid conflict

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import asyncio
from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

async def run_tests():
    """Simple manual test runner."""
    print("\n" + "="*60)
    print("🧪 TESTING ECOMOVEX CHATBOT SYSTEM")
    print("="*60 + "\n")
    
    # Test 1: Imports
    print("📋 Test 1: Module Imports")
    try:
        from database.db import Base
        from models.user import User, Role
        from models.chatbot.chat_session import ChatSession
        from models.chatbot.planning import TravelPlan, PlanItem
        from services.chatbot.rule_engine import RuleEngine, Intent
        print("  ✅ All imports successful\n")
    except Exception as e:
        print(f"  ❌ Import failed: {e}\n")
        return
    
    # Test 2: Database Connection
    print("📋 Test 2: Database Connection")
    try:
        from utils.config import settings
        engine = create_async_engine(
            f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}",
            echo=False
        )
        
        async with engine.connect() as conn:
            result = await conn.execute(sql_text("SELECT 1"))  # Use sql_text
            print("  ✅ Database connection successful\n")
        
        await engine.dispose()
    except Exception as e:
        print(f"  ❌ Database connection failed: {e}\n")
        return
    
    # Test 3: Rule Engine
    print("📋 Test 3: Rule Engine Classification")
    try:
        from services.chatbot.rule_engine import RuleEngine, Intent
        rule_engine = RuleEngine()  # Rename to avoid conflict
        
        test_cases = [
            ("Thêm nhà hàng chay ngày 2 lúc 19:00", Intent.ADD),
            ("Xóa activity id=5", Intent.REMOVE),
            ("Xem kế hoạch hiện tại", Intent.VIEW_PLAN),
            ("Đổi giờ ngày 1 thành 10:00", Intent.MODIFY_TIME),
            ("Gợi ý địa điểm thay thế", Intent.SUGGEST)
        ]
        
        passed = 0
        for text_input, expected_intent in test_cases:  # Rename text to text_input
            result = rule_engine.classify(text_input)
            status = "✅" if result.intent == expected_intent else "❌"
            print(f"  {status} '{text_input}'")
            print(f"     Intent: {result.intent}, Entities: {result.entities}")
            if result.intent == expected_intent:
                passed += 1
        
        print(f"\n  Passed: {passed}/{len(test_cases)}\n")
    except Exception as e:
        print(f"  ❌ Rule engine test failed: {e}\n")
    
    # Test 4: Database CRUD
    print("📋 Test 4: Database CRUD Operations")
    try:
        from utils.config import settings
        from models.user import User, Role
        from models.chatbot.chat_session import ChatSession
        from models.chatbot.planning import TravelPlan, PlanItem
        
        db_engine = create_async_engine(  # Rename to avoid conflict
            f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}",
            echo=False
        )
        
        async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Create test user
            user = User(
                username="Test User",
                email=f"test_{asyncio.get_event_loop().time()}@example.com",
                password="hashed_password",
                role=Role.user,
                eco_point=0
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            print(f"  ✅ User created with ID: {user.id}")
            
            # Create chat session
            chat_session = ChatSession(
                user_id=user.id,
                session_token="test_token_123",
                status="active"
            )
            session.add(chat_session)
            await session.commit()
            await session.refresh(chat_session)
            print(f"  ✅ Chat session created with ID: {chat_session.id}")
            
            # Create travel plan
            plan = TravelPlan(
                user_id=user.id,
                title="Test Trip",
                destination="Da Nang",
                start_date=date(2025, 12, 1),
                end_date=date(2025, 12, 5),
                meta={"budget": 5000000}
            )
            session.add(plan)
            await session.commit()
            await session.refresh(plan)
            print(f"  ✅ Travel plan created with ID: {plan.id}")
            
            # Create plan item
            item = PlanItem(
                plan_id=plan.id,
                day_index=1,
                time="09:00",
                title="Visit Beach",
                type="activity",
                meta={"location": "My Khe Beach"}
            )
            session.add(item)
            await session.commit()
            await session.refresh(item)
            print(f"  ✅ Plan item created with ID: {item.id}")
            
            # Cleanup
            await session.delete(item)
            await session.delete(plan)
            await session.delete(chat_session)
            await session.delete(user)
            await session.commit()
            print(f"  ✅ Test data cleaned up\n")
        
        await db_engine.dispose()
    except Exception as e:
        print(f"  ❌ Database CRUD test failed: {e}\n")
        import traceback
        traceback.print_exc()
    
    # Test 5: Planner Handler
    print("📋 Test 5: Planner Handler")
    try:
        from services.chatbot.planner_handle import PlannerHandler
        from repository.planning_repository import PlanningRepository
        from utils.config import settings
        from models.user import User, Role
        from models.chatbot.planning import TravelPlan
        
        planner_engine = create_async_engine(
            f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}",
            echo=False
        )
        
        async_session = sessionmaker(planner_engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Create test user and plan
            user = User(
                username="Planner Test",
                email=f"planner_{asyncio.get_event_loop().time()}@example.com",
                password="hashed",
                role=Role.user
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            plan = TravelPlan(
                user_id=user.id,
                title="Handler Test Trip",
                destination="Hoi An",
                start_date=date(2025, 7, 1),
                end_date=date(2025, 7, 5),
                meta={"budget": 3000000}
            )
            session.add(plan)
            await session.commit()
            await session.refresh(plan)
            
            # Test planner handler
            handler = PlannerHandler(session)
            
            # Test VIEW_PLAN
            result = await handler.handle(user.id, 1, "Xem kế hoạch")
            if result["ok"]:
                print(f"  ✅ VIEW_PLAN works: {result['action']}")
            else:
                print(f"  ⚠️  VIEW_PLAN: {result.get('message', 'Unknown error')}")
            
            # Test ADD
            result = await handler.handle(user.id, 1, "Thêm tham quan bảo tàng ngày 1 lúc 10:00")
            if result["ok"]:
                print(f"  ✅ ADD works: Added item {result['item']}")
            else:
                print(f"  ⚠️  ADD: {result.get('message', 'Unknown error')}")
            
            # Cleanup
            await session.delete(plan)
            await session.delete(user)
            await session.commit()
        
        await planner_engine.dispose()
        print()
    except Exception as e:
        print(f"  ❌ Planner handler test failed: {e}\n")
        import traceback
        traceback.print_exc()
    
    print("="*60)
    print("✅ ALL TESTS COMPLETED")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(run_tests())