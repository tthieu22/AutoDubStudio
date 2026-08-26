# -*- coding: utf-8 -*-
"""
Test suite for LLM Translation Engine Configuration & Qwen2.5-3B-Instruct via llama.cpp.
"""

import os
import sys
from pathlib import Path

# Ensure engine path is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.stdout.reconfigure(encoding='utf-8')

from autodub.config import DEFAULT_TRANSLATION_MODEL, TRANSLATION_MODELS
from autodub.modules.llamacpp_model_manager import LlamaCppModelManager
from autodub.modules.llamacpp_client import LlamaCppClient

def test_llamacpp_engine_config():
    print("=" * 70)
    print("AUTODUBSTUDIO - QWEN2.5-3B LLAMA.CPP CONFIG VERIFICATION")
    print("=" * 70)

    # 1. Test Config Integrity
    assert DEFAULT_TRANSLATION_MODEL == "qwen2.5-3b-instruct", f"Expected default qwen2.5-3b-instruct, got {DEFAULT_TRANSLATION_MODEL}"
    assert "qwen2.5-3b-instruct" in TRANSLATION_MODELS, "qwen2.5-3b-instruct missing from TRANSLATION_MODELS"
    assert TRANSLATION_MODELS["qwen2.5-3b-instruct"]["type"] == "llama_cpp", "Model type should be llama_cpp"
    assert "hachimi-60m" not in TRANSLATION_MODELS, "hachimi-60m should be removed from TRANSLATION_MODELS"
    print("[PASS] Config integrity and Qwen2.5-3B exclusive llama.cpp restriction verified.")

    # 2. Test Client Initialization
    client = LlamaCppClient()
    manager = LlamaCppModelManager()
    assert client.base_url.startswith("http"), "Base URL should be valid HTTP endpoint"
    assert manager.base_url.startswith("http"), "Base URL should be valid HTTP endpoint"
    print("[PASS] LlamaCppClient & Manager initialized cleanly.")

    print("\n" + "=" * 70)
    print("ALL QWEN2.5-3B LLAMA.CPP ENGINE CONFIG TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    test_llamacpp_engine_config()
