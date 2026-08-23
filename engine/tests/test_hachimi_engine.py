# -*- coding: utf-8 -*-
"""
Test suite for HachimiTranslator Engine & Single-Model GPU Exclusivity.
Tests speed, pronoun accuracy, memory footprint, and complete VRAM unloading.
"""

import os
import sys
import time
from pathlib import Path

# Ensure engine path is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.stdout.reconfigure(encoding='utf-8')

import torch
from autodub.modules.hachimi_translator import HachimiTranslator
from autodub.config import DEFAULT_TRANSLATION_MODEL, TRANSLATION_MODELS

def test_hachimi_engine():
    print("=" * 70)
    print("AUTODUBSTUDIO - HACHIMIMT-60 GPU ENGINE VERIFICATION")
    print(f"CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU Device:     {torch.cuda.get_device_name(0)}")
        print(f"Initial VRAM:   {torch.cuda.memory_allocated() / (1024**2):.1f} MB")
    print("=" * 70)

    # 1. Test Config Integrity
    assert DEFAULT_TRANSLATION_MODEL == "hachimi-60m", f"Expected default hachimi-60m, got {DEFAULT_TRANSLATION_MODEL}"
    assert "hachimi-60m" in TRANSLATION_MODELS, "hachimi-60m missing from TRANSLATION_MODELS"
    assert "qwen2.5:3b" in TRANSLATION_MODELS, "qwen2.5:3b missing from TRANSLATION_MODELS"
    assert "qwen3:4b" not in TRANSLATION_MODELS, "qwen3:4b should be removed from TRANSLATION_MODELS"
    print("[PASS] Config integrity and 2-model restriction verified.")

    # 2. Test Model Loading & VRAM Footprint
    hachimi = HachimiTranslator.get_instance()
    t0 = time.time()
    hachimi.load()
    load_time = time.time() - t0
    
    if torch.cuda.is_available():
        vram_loaded = torch.cuda.memory_allocated() / (1024**2)
        print(f"[PASS] HachimiMT loaded in {load_time:.2f}s on GPU | VRAM Allocated: {vram_loaded:.1f} MB")
        assert vram_loaded < 1000, f"VRAM usage too high: {vram_loaded} MB"
    else:
        print(f"[PASS] HachimiMT loaded in {load_time:.2f}s on CPU")

    # 3. Test Translation Accuracy on Standard & Ancient Sentences
    test_cases = [
        ("爸爸和妈妈去买菜。", "Ba và mẹ"),
        ("你吃饭了吗？", "cơm chưa"),
        ("朕统领天下数十载，何曾受过这等屈辱？", "Trẫm"),
        ("臣妾参见陛下，愿陛下万岁万岁万万岁。", "Thần thiếp"),
        ("奴婢罪该万死，还请王爷恕罪！", "Nô tỳ"),
        ("为师教你的武功，不是让你用来同门相残的。", "Vi sư"),
        ("在下初来乍到，多谢公子出手相助。", "Tại hạ"),
        ("老夫纵横江湖数十年，尔等黄口小儿休得猖狂！", "Lão phu"),
        ("少爷，老爷吩咐过，今夜绝不可踏出府门半步。", "Thiếu gia"),
    ]

    print("\n--- Testing Translation Quality & Pronouns ---")
    inputs = [src for src, _ in test_cases]
    
    t_start = time.time()
    translations = hachimi.translate_batch(inputs)
    t_batch = time.time() - t_start

    print(f"Batch {len(inputs)} sentences completed in {t_batch*1000:.1f} ms ({len(inputs)/max(t_batch, 0.001):.1f} subs/sec)")
    
    for (src, key_term), trans in zip(test_cases, translations):
        print(f"SRC: {src}")
        print(f"OUT: {trans}")
        assert key_term.lower() in trans.lower(), f"Failed key term '{key_term}' in '{trans}'"
        print("  -> [PASS]\n")

    # 4. Test Single-Model Memory Unload Exclusivity
    print("--- Testing Memory Unloading & Single-Model Exclusivity ---")
    hachimi.unload()
    assert not hachimi.is_loaded, "Engine should be marked as not loaded after unload()"
    assert hachimi.model is None, "Model reference should be None after unload()"
    
    if torch.cuda.is_available():
        vram_after = torch.cuda.memory_allocated() / (1024**2)
        print(f"VRAM after unload: {vram_after:.1f} MB (Fully released)")
        assert vram_after < 50, f"VRAM was not cleanly released: {vram_after} MB remaining"

    print("\n" + "=" * 70)
    print("ALL HACHIMI TRANSLATOR ENGINE TESTS PASSED SUCCESSFULLY (100% READY)!")
    print("=" * 70)

if __name__ == "__main__":
    test_hachimi_engine()
