import numpy as np
import logging
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Tuple
from models.user import User, UserActivity, Activity
from models.destination_embedding import DestinationEmbedding       

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Patch PyTorch / Transformers compatibility (với sentence-transformers)
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
            return np.random.randn(384)  # fallback vector
    model = DummyModel()
    logger.warning("⚠ Using dummy model for embeddings")

# ----------------------------------------------------------------------
# FAISS Index Management
# ----------------------------------------------------------------------
try:
    import faiss #not install yet
    FAISS_AVAILABLE = True
    logger.info("✓ FAISS library loaded successfully")
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("⚠ FAISS not available. Install with: pip install faiss-cpu")

class FAISSIndex:
    """Manages FAISS index for fast similarity search."""
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = None
        self.destination_ids = []
        
    def build_index(self, vectors: np.ndarray, ids: List[str], use_gpu: bool = False):
        """Build FAISS index from vectors."""
        if not FAISS_AVAILABLE:
            logger.error("FAISS not available")
            return False
            
        try:
            n_vectors = len(vectors)
            
            # Choose index type based on dataset size
            if n_vectors < 10000:
                # Flat index for small datasets (exact search)
                self.index = faiss.IndexFlatL2(self.dimension)
            else:
                # IVF index for larger datasets (approximate search)
                nlist = min(100, int(np.sqrt(n_vectors)))
                quantizer = faiss.IndexFlatL2(self.dimension)
                self.index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist)
                self.index.train(vectors)
            
            # Add vectors to index
            self.index.add(vectors)
            self.destination_ids = ids
            
            logger.info(f"✓ Built FAISS index with {n_vectors} vectors")
            return True
            
        except Exception as e:
            logger.error(f"Error building FAISS index: {e}")
            return False
    
    def search(self, query_vector: np.ndarray, k: int = 10) -> List[Tuple[str, float]]:
        """Search for k nearest neighbors."""
        if self.index is None:
            logger.error("Index not built")
            return []
        
        try:
            # Ensure query is 2D array
            if query_vector.ndim == 1:
                query_vector = query_vector.reshape(1, -1)
            
            # Search
            distances, indices = self.index.search(query_vector, k)
            
            # Return destination IDs and similarity scores
            results = []
            for idx, dist in zip(indices[0], distances[0]):
                if idx < len(self.destination_ids):
                    # Convert L2 distance to similarity score (0-100)
                    similarity = max(0, 100 - (dist * 10))
                    results.append((self.destination_ids[idx], round(similarity, 2)))
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching FAISS index: {e}")
            return []

# Global FAISS index instance
_faiss_index = FAISSIndex()

# ----------------------------------------------------------------------
# Async Batch Embedding
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

async def batch_embed_destinations(destinations: List[Dict[str, Any]], session: Session, model_version="v1"):
    """Generate and save embeddings for multiple destinations in parallel."""
    try:
        # Generate embeddings in parallel
        tasks = [embed_destination_async(dest) for dest in destinations]
        embeddings = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Save to database
        success_count = 0
        for dest, embedding in zip(destinations, embeddings):
            if isinstance(embedding, Exception):
                logger.error(f"Error embedding destination {dest.get('id')}: {embedding}")
                continue
                
            dest_id = dest.get('id')
            if dest_id:
                save_destination_embedding(session, dest_id, embedding, model_version)
                success_count += 1
        
        logger.info(f"✓ Batch embedded and saved {success_count}/{len(destinations)} destinations")
        return success_count
        
    except Exception as e:
        logger.error(f"Error in batch_embed_destinations: {e}")
        return 0

# ----------------------------------------------------------------------
# User embedding
# ----------------------------------------------------------------------
def embed_user(user_id: int, session: Session) -> Optional[List[float]]:
    """
    Generate embedding for a user based on preferences and activity.
    """
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
    """
    Generate embedding for a destination.
    """
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

def save_destination_embedding(session: Session, destination_id: str, vector: list[float], model_version="v1"):
    """
    Save or update destination embedding in the database.
    """
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

def build_all_destination_embeddings(session: Session, destinations: List[Dict[str, Any]], model_version="v1"):
    """
    Build and save embeddings for a list of destinations.
    """
    for dest in destinations:
        dest_id = dest.get('id')
        if not dest_id:
            logger.warning("Destination missing 'id', skipping")
            continue
        vector = embed_destination(dest)
        save_destination_embedding(session, dest_id, vector, model_version)

def load_destination_vectors(session: Session) -> Tuple[np.ndarray, List[str]]:
    """
    Load all destination vectors from DB to numpy array for FAISS/ANN.
    """
    records = session.query(DestinationEmbedding).all()
    vectors, ids = [], []
    for r in records:
        vectors.append(np.array(json.loads(r.embedding_vector), dtype=np.float32))
        ids.append(r.destination_id)
    return np.stack(vectors) if vectors else np.array([]), ids

def build_faiss_index(session: Session) -> bool:
    """Build FAISS index from all destination embeddings."""
    try:
        vectors, ids = load_destination_vectors(session)
        if len(vectors) == 0:
            logger.warning("No destination vectors found")
            return False
        
        return _faiss_index.build_index(vectors, ids)
        
    except Exception as e:
        logger.error(f"Error building FAISS index: {e}")
        return False

def find_similar_destinations(user_vector: List[float], k: int = 10) -> List[Dict[str, Any]]:
    """Find k most similar destinations using FAISS."""
    try:
        query_vector = np.array(user_vector, dtype=np.float32)
        results = _faiss_index.search(query_vector, k)
        
        return [
            {'destination_id': dest_id, 'similarity_score': score}
            for dest_id, score in results
        ]
        
    except Exception as e:
        logger.error(f"Error finding similar destinations: {e}")
        return []

# ----------------------------------------------------------------------
# Cluster embedding
# ----------------------------------------------------------------------
def compute_cluster_embedding(cluster_id: int, session: Session) -> Optional[np.ndarray]:
    """
    Compute average embedding for a cluster from all user embeddings.
    """
    try:
        from models.cluster import UserClusterAssociation

        cluster_users = session.query(UserClusterAssociation).filter(
            UserClusterAssociation.cluster_id == cluster_id
        ).all()
        user_ids = [assoc.user_id for assoc in cluster_users]

        if not user_ids:
            logger.warning(f"No users found in cluster {cluster_id}")
            return None

        # Generate embeddings for all users
        user_embeddings = []
        for user_id in user_ids:
            embedding = embed_user(user_id, session)
            if embedding:
                user_embeddings.append(np.array(embedding))

        if not user_embeddings:
            logger.warning(f"No valid embeddings for cluster {cluster_id}")
            return None

        # Compute centroid (average)
        cluster_vector = np.mean(user_embeddings, axis=0)
        logger.info(f"Computed cluster embedding for cluster {cluster_id} from {len(user_embeddings)} users")
        
        return cluster_vector

    except Exception as e:
        logger.error(f"Error computing cluster embedding for cluster {cluster_id}: {e}")
        return None

def recommend_for_cluster_hybrid(
    cluster_id: int, 
    session: Session, 
    k: int = 20,
    similarity_weight: float = 0.7,
    popularity_weight: float = 0.3
) -> List[Dict[str, Any]]:
    """
    Hybrid recommendation combining semantic similarity and popularity.
    """
    try:
        # Get cluster embedding
        cluster_vector = compute_cluster_embedding(cluster_id, session)
        if cluster_vector is None:
            return []

        # Get similarity-based recommendations
        similar_destinations = find_similar_destinations(cluster_vector.tolist(), k=k*2)
        
        # Get popularity scores
        popular_destinations = compute_top_destinations_for_cluster(cluster_id, session, limit=k*2)
        
        # Merge and re-rank
        destination_scores = {}
        
        # Add similarity scores
        for item in similar_destinations:
            dest_id = item['destination_id']
            destination_scores[dest_id] = {
                'similarity': item['similarity_score'],
                'popularity': 0.0
            }
        
        # Add popularity scores
        for item in popular_destinations:
            dest_id = item['destination_id']
            if dest_id not in destination_scores:
                destination_scores[dest_id] = {'similarity': 0.0, 'popularity': 0.0}
            destination_scores[dest_id]['popularity'] = item['popularity_score']
        
        # Compute hybrid score
        results = []
        for dest_id, scores in destination_scores.items():
            hybrid_score = (
                scores['similarity'] * similarity_weight +
                scores['popularity'] * popularity_weight
            )
            results.append({
                'destination_id': dest_id,
                'hybrid_score': round(hybrid_score, 2),
                'similarity_score': round(scores['similarity'], 2),
                'popularity_score': round(scores['popularity'], 2)
            })
        
        # Sort by hybrid score
        results.sort(key=lambda x: x['hybrid_score'], reverse=True)
        
        logger.info(f"Generated {len(results[:k])} hybrid recommendations for cluster {cluster_id}")
        return results[:k]

    except Exception as e:
        logger.error(f"Error in hybrid recommendation for cluster {cluster_id}: {e}")
        return []

# ----------------------------------------------------------------------
# Cluster scoring (top destinations per cluster)
# ----------------------------------------------------------------------
def compute_top_destinations_for_cluster(cluster_id: int, session: Session, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Compute top destinations for a cluster based on user activities.
    """
    try:
        from models.cluster import UserClusterAssociation

        cluster_users = session.query(UserClusterAssociation).filter(
            UserClusterAssociation.cluster_id == cluster_id
        ).all()
        user_ids = [assoc.user_id for assoc in cluster_users]

        if not user_ids:
            logger.warning(f"No users found in cluster {cluster_id}")
            return []

        activities = session.query(UserActivity).filter(
            UserActivity.user_id.in_(user_ids),
            UserActivity.destination_id.isnot(None)
        ).all()

        destination_scores = {}
        for activity in activities:
            dest_id = activity.destination_id
            if dest_id not in destination_scores:
                destination_scores[dest_id] = {'save_count':0, 'search_count':0, 'review_count':0}
            if activity.activity == Activity.save_destination:
                destination_scores[dest_id]['save_count'] += 1
            elif activity.activity == Activity.search_destination:
                destination_scores[dest_id]['search_count'] += 1
            elif activity.activity == Activity.review_destination:
                destination_scores[dest_id]['review_count'] += 1

        top_destinations = []
        for dest_id, scores in destination_scores.items():
            popularity_score = scores['save_count']*3 + scores['review_count']*2 + scores['search_count']*1
            normalized_score = min(100.0, (popularity_score / len(user_ids)) * 20)
            top_destinations.append({'destination_id': dest_id, 'popularity_score': round(normalized_score,2)})

        top_destinations.sort(key=lambda x: x['popularity_score'], reverse=True)
        result = top_destinations[:limit]
        logger.info(f"Computed {len(result)} top destinations for cluster {cluster_id}")
        return result

    except Exception as e:
        logger.error(f"Error computing top destinations for cluster {cluster_id}: {e}")
        return []
