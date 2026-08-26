"""
HachimiTranslator is deprecated and removed.
AutoDubStudio now exclusively uses Qwen2.5-3B-Instruct via llama.cpp CUDA for all translation tasks.
"""
import logging

logger = logging.getLogger("autodub")

class HachimiTranslator:
    """Deprecated stub. Redirects to LlamaCppClient."""
    def __init__(self, *args, **kwargs):
        logger.warning("HachimiTranslator is deprecated. Please use LlamaCppClient for Qwen2.5-3B-Instruct.")

    def load(self) -> bool:
        return True

    def unload(self):
        pass

    def translate_single(self, text: str) -> str:
        raise NotImplementedError("HachimiTranslator is removed. Use LlamaCppClient with Qwen2.5-3B.")

    def translate_batch(self, texts, max_length=128):
        raise NotImplementedError("HachimiTranslator is removed. Use LlamaCppClient with Qwen2.5-3B.")
