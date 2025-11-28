import numpy as np
import json
from sqlalchemy.orm import Session
from typing import List, Tuple, Dict, Any
from models.destination import DestinationEmbedding

try:
    import faiss
    FAISS_AVAILABLE = True
    print("✓ FAISS library loaded successfully")
except ImportError:
    FAISS_AVAILABLE = False
    print("⚠ FAISS not available. Install with: pip install faiss-cpu")

class FAISSIndex:
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = None
        self.destination_ids = []
        
    def build_index(self, vectors: np.ndarray, ids: List[str], use_ivf: bool = None) -> bool:
        if not FAISS_AVAILABLE:
            print("FAISS not available")
            return False
            
        try:
            n_vectors = len(vectors)

            if use_ivf is None:
                use_ivf = n_vectors >= 10000
            
            if use_ivf:
                nlist = min(100, int(np.sqrt(n_vectors)))
                quantizer = faiss.IndexFlatL2(self.dimension)
                self.index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist)
                self.index.train(vectors)
            else:
                self.index = faiss.IndexFlatL2(self.dimension)
            
            self.index.add(vectors)
            self.destination_ids = ids
            
            index_type = "IVF" if use_ivf else "Flat"
            print(f"✓ Built FAISS {index_type} index with {n_vectors} vectors")
            return True
            
        except Exception as e:
            print(f"Error building FAISS index: {e}")
            return False
    
    def search(self, query_vector: np.ndarray, k: int = 10) -> List[Tuple[str, float]]:
        if self.index is None:
            print("Index not built")
            return []
        
        try:
            if query_vector.ndim == 1:
                query_vector = query_vector.reshape(1, -1)
            
            distances, indices = self.index.search(query_vector, k)
            
            results = []
            for idx, dist in zip(indices[0], distances[0]):
                if idx < len(self.destination_ids):
                    similarity = max(0, 100 - (dist * 10))
                    results.append((self.destination_ids[idx], round(similarity, 2)))
            
            return results
            
        except Exception as e:
            print(f"Error searching FAISS index: {e}")
            return []
    
    def is_built(self) -> bool:
        return self.index is not None and len(self.destination_ids) > 0

_faiss_index = FAISSIndex()

def normalize_vectors(vectors: np.ndarray) -> np.ndarray:
    try:
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1  # Avoid division by zero
        return vectors / norms
    except Exception as e:
        print(f"Error normalizing vectors: {e}")
        return vectors

def load_destination_vectors(session: Session) -> Tuple[np.ndarray, List[str]]:
    records = session.query(DestinationEmbedding).all()
    vectors, ids = [], []
    for r in records:
        vectors.append(np.array(json.loads(r.embedding_vector), dtype=np.float32))
        ids.append(r.destination_id)
    
    if vectors:
        return np.stack(vectors), ids
    return np.array([]), ids

def build_index(session: Session, normalize: bool = False) -> bool:
    try:
        vectors, ids = load_destination_vectors(session)
        if len(vectors) == 0:
            print("No destination vectors found")
            return False
        
        if normalize:
            vectors = normalize_vectors(vectors)
        
        return _faiss_index.build_index(vectors, ids)
        
    except Exception as e:
        print(f"Error building FAISS index: {e}")
        return False

def search_index(query_vector: List[float], k: int = 10, normalize: bool = False) -> List[Dict[str, Any]]:
    try:
        query_arr = np.array(query_vector, dtype=np.float32)
        
        if normalize:
            query_arr = normalize_vectors(query_arr.reshape(1, -1)).flatten()
        
        results = _faiss_index.search(query_arr, k)
        
        return [
            {'destination_id': dest_id, 'similarity_score': score}
            for dest_id, score in results
        ]
        
    except Exception as e:
        print(f"Error searching index: {e}")
        return []

def is_index_ready() -> bool:
    return _faiss_index.is_built()

def rebuild_index(session: Session, normalize: bool = False) -> bool:
    print("Rebuilding FAISS index...")
    return build_index(session, normalize)