import json
import logging
from typing import Dict, Any, List, Optional, Callable, Tuple
from autodub.novel.novel_models import StoryIdea

logger = logging.getLogger(__name__)

FORBIDDEN_GENRE_TERMS = [
    b"ti\xc3\xaan gi\xe1\xbb\x9bi".decode("utf-8"),
    b"tr\xc3\xbac c\xc6\xa1".decode("utf-8"),
    b"luy\xe1\xbb\x87n kh\xc3\xad".decode("utf-8"),
    b"t\xc3\xb4ng m\xc3\xb4n".decode("utf-8"),
    b"thanh v\xc3\xa2n t\xc3\xb4ng".decode("utf-8"),
    b"l\xc3\xa2m ph\xc3\xa0m".decode("utf-8")
]


def log_gpu_hardware_status(callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> None:
    def _out(msg: str):
        logger.info(msg)
        print(f"[INFO] {msg}", flush=True)
        if callback:
            callback({"event": "novel_sub_stage", "step": "HARDWARE", "message": msg})

    _out("=== [HARDWARE ACCELERATION CHECK] ===")
    try:
        import torch
        if torch.cuda.is_available():
            dev_name = torch.cuda.get_device_name(0)
            vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            _out(f"[HARDWARE] GPU Device Detected: {dev_name} ({vram_gb:.1f} GB VRAM)")
            _out("[HARDWARE] PyTorch CUDA Acceleration: ACTIVE (Device 0)")
            _out("[HARDWARE] Local LLM Offload: -ngl 99 (100% GPU VRAM Accelerated)")
        else:
            _out("[HARDWARE] CUDA not detected in PyTorch environment. Running CPU Fallback Mode.")
    except Exception as e:
        _out(f"[HARDWARE] GPU status check: {e}")


def validate_protagonist_integrity(res: Any, idea: StoryIdea) -> Tuple[bool, str]:
    """Validates that generated characters or story bible contains the requested protagonist."""
    expected_p = idea.protagonist.get("name", "").strip() if isinstance(idea.protagonist, dict) else ""
    if not expected_p or expected_p.lower() in ("nhân vật chính", "chưa đặt tên"):
        return True, ""

    if isinstance(res, dict) and "characters" not in res:
        return True, ""

    chars = []
    if isinstance(res, dict):
        chars = res.get("characters", [])
    elif isinstance(res, list):
        chars = res

    char_names = [c.get("name", "").strip().lower() for c in chars if isinstance(c, dict)]
    forbidden_p = FORBIDDEN_GENRE_TERMS[-1]
    if any(expected_p.lower() in cn or cn in expected_p.lower() for cn in char_names):
        if expected_p.lower() != forbidden_p and any(cn == forbidden_p for cn in char_names):
            return False, f"Protagonist integrity error: injected '{forbidden_p}' instead of requested '{expected_p}'"
        return True, ""

    return False, f"Protagonist integrity error: requested protagonist '{expected_p}' not found in generated character list {char_names}"


def validate_genre_integrity(res: Any, idea: StoryIdea) -> Tuple[bool, str]:
    """Validates that non-Xianxia genres do not contain forbidden Xianxia terms."""
    genre_lower = (idea.genre or "").lower()
    xianxia_genres = [
        "tiên hiệp", "huyền huyễn", "tu tiên", "tiên đế", "xuyên không",
        "cổ đại", "kiếm hiệp", "võ lâm", "hệ thống", "trùng sinh", "dị thế", "dị năng"
    ]
    is_xianxia = any(xg in genre_lower for xg in xianxia_genres)

    if is_xianxia:
        return True, ""

    res_str = json.dumps(res, ensure_ascii=False).lower()
    found = [ft for ft in FORBIDDEN_GENRE_TERMS if ft in res_str]

    if found:
        return False, f"Genre integrity error for '{idea.genre}': found forbidden Xianxia terms {found}"

    return True, ""
