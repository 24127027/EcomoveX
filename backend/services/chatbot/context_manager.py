from backend.repository.chatbot_message_repository import ChatbotMessageRepository
from services.embedding_service import embed_user, compute_cluster_embedding
from services.recommendation_service import recommend_for_cluster_hybrid

class ContextManager:
    def __init__(self, db):
        self.db = db

    async def load_context(self, user_id: int, chat_session_id: int):
        # 1. Short-term memory
        history = await ChatbotMessageRepository.get_history(self.db, chat_session_id)

        # 2. Long-term memory
        stored = await self.db.get_stored_context(user_id)

        # 3. User embedding + cluster (long-term user model)
        embedding = await embed_user(user_id)
        cluster_info = await compute_cluster_embedding(user_id)

        # 4. Recommendation for context-aware answers
        recommendations = await recommend_for_cluster_hybrid(user_id)

        # 5. Active planning session
        active_trip = await self.db.get_active_trip(user_id)
        activities = []
        if active_trip:
            activities = await self.db.get_trip_activities(active_trip.id)

        return {
            "history": [h.content for h in history],
            "stored_context": stored,

            # USER CONTEXT
            "embedding": embedding,
            "cluster_info": cluster_info,
            "recommendations": recommendations,

            # PLANNING CONTEXT
            "active_trip": active_trip,
            "activities": activities
        }

    async def update_context(self, context, user_msg, bot_msg):
        # keep last 20 messages
        history = context.get("history", [])
        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": bot_msg})
        context["history"] = history[-20:]
        return context

    async def save(self, user_id, chat_session_id, context):
        await self.db.save_chat_history(chat_session_id, context["history"])
        await self.db.save_stored_context(user_id, context["stored_context"])
