import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional
from autodub.exceptions import RenderValidationError

VALID_AUDIO_MODES = {"DUB_ONLY", "ORIGINAL_ONLY", "MIX", "DUCK_ORIGINAL"}
VALID_VIDEO_CODECS = {"H264", "H265"}
VALID_ENCODERS = {"AUTO", "CPU", "NVENC"}
VALID_QUALITIES = {"FAST", "MEDIUM", "HIGH"}
VALID_SUBTITLE_MODES = {"NONE", "COPY", "BURN_IN"}


@dataclass
class RenderConfig:
    audio_mode: str = "DUCK_ORIGINAL"
    tts_volume: float = 1.0
    original_volume: float = 0.15
    ducking: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,
        "threshold": 0.02,
        "ratio": 8.0,
        "attack": 20,
        "release": 300
    })
    video_codec: str = "H264"
    encoder: str = "AUTO"
    quality: str = "MEDIUM"
    fps_mode: str = "PRESERVE"
    resolution_mode: str = "PRESERVE"
    subtitle_mode: str = "BURN_IN"
    subtitle_path: str = "transcript/translated.srt"

    def validate(self) -> None:
        """Validate render configuration values."""
        if self.audio_mode not in VALID_AUDIO_MODES:
            raise RenderValidationError(f"Invalid audio mode '{self.audio_mode}'. Allowed: {VALID_AUDIO_MODES}")

        if not (0.0 <= self.tts_volume <= 2.0):
            raise RenderValidationError(f"tts_volume must be between 0.0 and 2.0, got {self.tts_volume}")

        if not (0.0 <= self.original_volume <= 2.0):
            raise RenderValidationError(f"original_volume must be between 0.0 and 2.0, got {self.original_volume}")

        if self.video_codec not in VALID_VIDEO_CODECS:
            raise RenderValidationError(f"Invalid video codec '{self.video_codec}'. Allowed: {VALID_VIDEO_CODECS}")

        if self.encoder not in VALID_ENCODERS:
            raise RenderValidationError(f"Invalid encoder setting '{self.encoder}'. Allowed: {VALID_ENCODERS}")

        if self.quality not in VALID_QUALITIES:
            raise RenderValidationError(f"Invalid quality '{self.quality}'. Allowed: {VALID_QUALITIES}")

        if self.subtitle_mode not in VALID_SUBTITLE_MODES:
            raise RenderValidationError(f"Invalid subtitle mode '{self.subtitle_mode}'. Allowed: {VALID_SUBTITLE_MODES}")

    def compute_hash(self, input_metadata: Optional[Dict[str, Any]] = None) -> str:
        """Compute a deterministic hash for checking render configuration changes."""
        self.validate()
        payload = {
            "config": asdict(self),
            "input_metadata": input_metadata or {}
        }
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RenderConfig":
        """Construct RenderConfig from dictionary with safe defaults."""
        data = data or {}
        cfg = cls(
            audio_mode=data.get("audio_mode", "DUCK_ORIGINAL"),
            tts_volume=float(data.get("tts_volume", 1.0)),
            original_volume=float(data.get("original_volume", 0.15)),
            ducking=data.get("ducking", {
                "enabled": True,
                "threshold": 0.02,
                "ratio": 8.0,
                "attack": 20,
                "release": 300
            }),
            video_codec=data.get("video_codec", "H264"),
            encoder=data.get("encoder", "AUTO"),
            quality=data.get("quality", "MEDIUM"),
            fps_mode=data.get("fps_mode", "PRESERVE"),
            resolution_mode=data.get("resolution_mode", "PRESERVE"),
            subtitle_mode=data.get("subtitle_mode", "BURN_IN"),
            subtitle_path=data.get("subtitle_path", "transcript/translated.srt")
        )
        cfg.validate()
        return cfg
