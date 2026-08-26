import logging
from typing import Dict, Any

logger = logging.getLogger("autodub")

class GPUMonitor:
    @staticmethod
    def get_vram_info() -> Dict[str, Any]:
        info = {
            "available": False,
            "total_mb": 0,
            "allocated_mb": 0,
            "free_mb": 0
        }
        try:
            import torch
            if torch.cuda.is_available():
                info["available"] = True
                total = torch.cuda.get_device_properties(0).total_memory
                allocated = torch.cuda.memory_allocated(0)
                reserved = torch.cuda.memory_reserved(0)
                info["total_mb"] = int(total / (1024 * 1024))
                info["allocated_mb"] = int(allocated / (1024 * 1024))
                info["free_mb"] = info["total_mb"] - int(reserved / (1024 * 1024))
        except Exception:
            pass
        return info

    @staticmethod
    def check_vram_safety(min_free_mb: int = 1200) -> bool:
        vram = GPUMonitor.get_vram_info()
        if not vram["available"]:
            return True
        if vram["free_mb"] < min_free_mb:
            logger.warning(f"VRAM Safety Warning: Available free VRAM ({vram['free_mb']}MB) is lower than threshold ({min_free_mb}MB).")
            return False
        return True
