from typing import List

import numpy as np


def patch_torch_compatibility():
    try:
        import sys

        import torch.utils._pytree as pytree

        if not hasattr(pytree, "register_pytree_node") and hasattr(
            pytree, "_register_pytree_node"
        ):
            pytree.register_pytree_node = pytree._register_pytree_node

        if "transformers" not in sys.modules:
            import importlib.util

            spec = importlib.util.find_spec("transformers")
            if spec:
                pass
    except Exception:
        pass


patch_torch_compatibility()

try:
    from sentence_transformers import SentenceTransformer

    _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
except Exception:

    class DummyModel:
        def encode(self, text):
            return np.random.randn(384)

    _embedding_model = DummyModel()


def get_embedding_model():
    return _embedding_model


def encode_text(text: str) -> List[float]:
    return _embedding_model.encode(text).tolist()
