import json
import sys
from typing import Optional

def emit_event(
    event_type: str,
    stage: str,
    current: Optional[int] = None,
    total: Optional[int] = None,
    percent: Optional[float] = None,
    message: Optional[str] = None,
    error: Optional[str] = None,
    chunk: Optional[int] = None,
    total_chunks: Optional[int] = None,
    segment_id: Optional[int] = None,
    elapsed: Optional[float] = None,
    **kwargs
) -> None:
    """Emit machine-readable JSON progress events to stdout for Tauri IPC integration."""
    payload = {
        "event": event_type,
        "stage": stage.upper()
    }
    if chunk is not None:
        payload["chunk"] = chunk
    if total_chunks is not None:
        payload["total_chunks"] = total_chunks
    if segment_id is not None:
        payload["segment_id"] = segment_id
    if elapsed is not None:
        payload["elapsed"] = elapsed
    if current is not None:
        payload["current"] = current
    if total is not None:
        payload["total"] = total
    if percent is not None:
        payload["percent"] = round(percent, 2)
    elif current is not None and total is not None and total > 0:
        payload["percent"] = round((current / total) * 100, 2)
    if message is not None:
        payload["message"] = message
    if error is not None:
        payload["error"] = error
    for k, v in kwargs.items():
        payload[k] = v
        
    print(json.dumps(payload), flush=True)
