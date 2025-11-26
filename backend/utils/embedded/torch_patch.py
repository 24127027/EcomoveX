def apply_torch_patch():
    try:
        import torch.utils._pytree as pytree
        
        if not hasattr(pytree, 'register_pytree_node'):
            if hasattr(pytree, '_register_pytree_node'):
                pytree.register_pytree_node = pytree._register_pytree_node
                print("Applied PyTorch pytree compatibility patch")
            else:
                print("Could not find _register_pytree_node in torch.utils._pytree")
    except ImportError:
        print("PyTorch not installed, skipping patch")
    except Exception as e:
        print(f"Error applying torch patch: {e}")

apply_torch_patch()