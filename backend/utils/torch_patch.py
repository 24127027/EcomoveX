"""
Compatibility patch for PyTorch and transformers version conflicts.
Import this module before importing sentence_transformers or transformers.
"""
import logging

logger = logging.getLogger(__name__)

def apply_torch_patch():
    """Apply compatibility patch for torch.utils._pytree"""
    try:
        import torch.utils._pytree as pytree
        
        # Check if the newer API exists
        if not hasattr(pytree, 'register_pytree_node'):
            if hasattr(pytree, '_register_pytree_node'):
                # Create alias for backward compatibility
                pytree.register_pytree_node = pytree._register_pytree_node
                logger.info("Applied PyTorch pytree compatibility patch")
            else:
                logger.warning("Could not find _register_pytree_node in torch.utils._pytree")
    except ImportError:
        logger.warning("PyTorch not installed, skipping patch")
    except Exception as e:
        logger.error(f"Error applying torch patch: {e}")

# Apply patch when module is imported
apply_torch_patch()