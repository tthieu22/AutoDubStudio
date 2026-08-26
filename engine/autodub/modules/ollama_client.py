"""
Compatibility module: OllamaClient is deprecated.
Re-exports LlamaCppClient as OllamaClient for backward compatibility.
"""
from autodub.modules.llamacpp_client import LlamaCppClient as OllamaClient, strip_think_tags

__all__ = ["OllamaClient", "strip_think_tags"]
