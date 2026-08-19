import gc

def cleanup_memory():
    """Explicitly release RAM and trigger Python garbage collector."""
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ImportError:
        pass
