import numpy as np
import logging
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from models.user import User, UserActivity, Activity
from models.destination_embedding import DestinationEmbedding

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Patch PyTorch / Transformers compatibility
# ----------------------------------------------------------------------
def patch_torch_compatibility():
    """Patch torch.utils._pytree for compatibility with older transformers versions."""
    try:
        import torch.utils._pytree as pytree
        import sys

        if not hasattr(pytree, 'register_pytree_node') and hasattr(pytree, '_register_pytree_node'):
            pytree.register_pytree_node = pytree._register_pytree_node
            logger.info("✓ Applied PyTorch pytree compatibility patch")

        if 'transformers' not in sys.modules:
            import importlib.util
            spec = importlib.util.find_spec('transformers')
            if spec:
                logger.info("✓ Pre-patching transformers namespace")
    except Exception as e:
        logger.warning(f"⚠ Could not apply torch patch: {e}")

patch_torch_compatibility()

# ----------------------------------------------------------------------
# Load sentence-transformers model
# ----------------------------------------------------------------------
try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    logger.info("✓ SentenceTransformer model loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load SentenceTransformer: {e}")
    class DummyModel:
        def encode(self, text):
            return np.random.randn(384)
    model = DummyModel()
    logger.warning("⚠ Using dummy model for embeddings")

# ----------------------------------------------------------------------
# User embedding
# ----------------------------------------------------------------------
def embed_user(user_id: int, session: Session) -> Optional[List[float]]:
    """Generate embedding for a user based on preferences and activity."""
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User {user_id} not found")
            return None

        user_text_data = []

        # Preferences
        if user.temp_min is not None and user.temp_max is not None:
            user_text_data.append(f"prefers temperature between {user.temp_min} and {user.temp_max} degrees")
        if user.budget_min is not None and user.budget_max is not None:
            user_text_data.append(f"budget range {user.budget_min} to {user.budget_max}")

        # Activities
        activities = session.query(UserActivity).filter(UserActivity.user_id == user_id).all()
        activity_counts = {}
        for activity in activities:
            activity_type = activity.activity.value
            activity_counts[activity_type] = activity_counts.get(activity_type, 0) + 1
        for act, count in activity_counts.items():
            user_text_data.append(f"{act} {count} times")

        # Eco / rank
        if user.eco_point and user.eco_point > 0:
            user_text_data.append(f"eco-conscious with {user.eco_point} eco points")
        if user.rank:
            user_text_data.append(f"travel experience level {user.rank.value}")

        if not user_text_data:
            user_text_data.append(f"user {user.username}")

        # Encode
        user_text = " ".join(user_text_data)
        embedding = model.encode(user_text).tolist()
        logger.info(f"Generated embedding for user {user_id} with {len(user_text_data)} features")
        return embedding

    except Exception as e:
        logger.error(f"Error generating embedding for user {user_id}: {e}")
        return None

# ----------------------------------------------------------------------
# Destination embedding
# ----------------------------------------------------------------------
def embed_destination(destination_data: Dict[str, Any]) -> List[float]:
    """Generate embedding for a destination."""
    text_parts = []
    if 'name' in destination_data:
        text_parts.append(destination_data['name'])
    if 'tags' in destination_data:
        if isinstance(destination_data['tags'], list):
            text_parts.extend(destination_data['tags'])
        else:
            text_parts.append(str(destination_data['tags']))
    if 'description' in destination_data:
        text_parts.append(destination_data['description'])

    text = " ".join(text_parts) if text_parts else "destination"
    return model.encode(text).tolist()

# ----------------------------------------------------------------------
# Save/Load embeddings
# ----------------------------------------------------------------------
def save_embedding(session: Session, destination_id: str, vector: List[float], model_version: str = "v1"):
    """Save or update destination embedding in the database."""
    try:
        record = session.query(DestinationEmbedding).filter(
            DestinationEmbedding.destination_id == destination_id
        ).first()
        
        if record:
            record.set_vector(vector)
            record.model_version = model_version
            logger.info(f"Updated embedding for destination {destination_id}")
        else:
            new_record = DestinationEmbedding(destination_id=destination_id, model_version=model_version)
            new_record.set_vector(vector)
            session.add(new_record)
            logger.info(f"Created new embedding for destination {destination_id}")

        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving embedding for destination {destination_id}: {e}")

def load_embedding(session: Session, destination_id: str) -> Optional[List[float]]:
    """Load embedding for a specific destination."""
    try:
        record = session.query(DestinationEmbedding).filter(
            DestinationEmbedding.destination_id == destination_id
        ).first()
        
        if record:
            return json.loads(record.embedding_vector)
        return None
    except Exception as e:
        logger.error(f"Error loading embedding for destination {destination_id}: {e}")
        return None

def load_all_embeddings(session: Session) -> Dict[str, List[float]]:
    """Load all destination embeddings as dictionary."""
    try:
        records = session.query(DestinationEmbedding).all()
        embeddings = {}
        for record in records:
            embeddings[record.destination_id] = json.loads(record.embedding_vector)
        logger.info(f"Loaded {len(embeddings)} destination embeddings")
        return embeddings
    except Exception as e:
        logger.error(f"Error loading all embeddings: {e}")
        return {}

# ----------------------------------------------------------------------
# Batch operations
# ----------------------------------------------------------------------
async def embed_user_async(user_id: int, session: Session) -> Optional[List[float]]:
    """Async wrapper for embed_user."""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        return await loop.run_in_executor(executor, embed_user, user_id, session)

async def embed_destination_async(destination_data: Dict[str, Any]) -> List[float]:
    """Async wrapper for embed_destination."""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        return await loop.run_in_executor(executor, embed_destination, destination_data)

async def batch_embed_users(user_ids: List[int], session: Session) -> Dict[int, Optional[List[float]]]:
    """Generate embeddings for multiple users in parallel."""
    try:
        tasks = [embed_user_async(user_id, session) for user_id in user_ids]
        embeddings = await asyncio.gather(*tasks, return_exceptions=True)
        
        results = {}
        for user_id, embedding in zip(user_ids, embeddings):
            if isinstance(embedding, Exception):
                logger.error(f"Error embedding user {user_id}: {embedding}")
                results[user_id] = None
            else:
                results[user_id] = embedding
        
        logger.info(f"✓ Batch embedded {len(results)} users")
        return results
        
    except Exception as e:
        logger.error(f"Error in batch_embed_users: {e}")
        return {}

async def batch_embed_destinations(destinations: List[Dict[str, Any]], session: Session, model_version: str = "v1") -> int:
    """Generate and save embeddings for multiple destinations in parallel."""
    try:
        tasks = [embed_destination_async(dest) for dest in destinations]
        embeddings = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = 0
        for dest, embedding in zip(destinations, embeddings):
            if isinstance(embedding, Exception):
                logger.error(f"Error embedding destination {dest.get('id')}: {embedding}")
                continue
                
            dest_id = dest.get('id')
            if dest_id:
                save_embedding(session, dest_id, embedding, model_version)
                success_count += 1
        
        logger.info(f"✓ Batch embedded and saved {success_count}/{len(destinations)} destinations")
        return success_count
        
    except Exception as e:
        logger.error(f"Error in batch_embed_destinations: {e}")
        return 0

def build_all_destination_embeddings(session: Session, destinations: List[Dict[str, Any]], model_version: str = "v1"):
    """Build and save embeddings for a list of destinations."""
    for dest in destinations:
        dest_id = dest.get('id')
        if not dest_id:
            logger.warning("Destination missing 'id', skipping")
            continue
        vector = embed_destination(dest)
        save_embedding(session, dest_id, vector, model_version)
