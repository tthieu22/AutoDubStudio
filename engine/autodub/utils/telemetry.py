import psutil
import json
import sys

def get_telemetry():
    # RAM Telemetry
    mem = psutil.virtual_memory()
    ram_used_gb = mem.used / (1024 ** 3)
    ram_total_gb = mem.total / (1024 ** 3)
    ram_percent = mem.percent
    
    ram_str = f"{ram_used_gb:.1f} GB / {ram_total_gb:.1f} GB ({ram_percent:.0f}%)"
    
    # VRAM Telemetry (attempt nvidia-smi / pynvml if available)
    vram_str = "N/A (GPU Telemetry Unavailable)"
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        gpu_name = pynvml.nvmlDeviceGetName(handle)
        if isinstance(gpu_name, bytes):
            gpu_name = gpu_name.decode("utf-8")
        info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        vram_used_gb = info.used / (1024 ** 3)
        vram_total_gb = info.total / (1024 ** 3)
        vram_str = f"{vram_used_gb:.2f} GB / {vram_total_gb:.2f} GB ({gpu_name})"
    except Exception:
        # Fallback using subprocess nvidia-smi
        try:
            import subprocess
            res = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.used,memory.total,name", "--format=csv,nounits,noheader"],
                capture_output=True,
                text=True,
                check=True
            )
            out = res.stdout.strip().split(",")
            if len(out) >= 3:
                used_mb = float(out[0].strip())
                total_mb = float(out[1].strip())
                gname = out[2].strip()
                vram_str = f"{used_mb/1024:.2f} GB / {total_mb/1024:.2f} GB ({gname})"
        except Exception:
            pass

    return {
        "ram": ram_str,
        "vram": vram_str,
        "ram_used_gb": round(ram_used_gb, 2),
        "ram_total_gb": round(ram_total_gb, 2),
        "ram_percent": ram_percent
    }

def get_vram_info():
    """Get exact free & total VRAM in MB."""
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        return {
            "free_mb": info.free / (1024 ** 2),
            "total_mb": info.total / (1024 ** 2),
            "used_mb": info.used / (1024 ** 2)
        }
    except Exception:
        try:
            import subprocess
            res = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.free,memory.total,memory.used", "--format=csv,nounits,noheader"],
                capture_output=True,
                text=True,
                check=True
            )
            out = res.stdout.strip().split(",")
            if len(out) >= 3:
                return {
                    "free_mb": float(out[0].strip()),
                    "total_mb": float(out[1].strip()),
                    "used_mb": float(out[2].strip())
                }
        except Exception:
            pass
    return {"free_mb": 4096.0, "total_mb": 4096.0, "used_mb": 0.0}

if __name__ == "__main__":
    print(json.dumps(get_telemetry()))
