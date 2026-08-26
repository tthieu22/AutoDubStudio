"""
Compatibility module: OllamaModelManager is deprecated.
Re-exports LlamaCppModelManager as OllamaModelManager for backward compatibility.
"""
from autodub.modules.llamacpp_model_manager import LlamaCppModelManager as OllamaModelManager

__all__ = ["OllamaModelManager"]
