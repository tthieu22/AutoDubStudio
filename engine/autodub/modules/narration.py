import hashlib
import json
import re
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("autodub")

# Natural pause durations based on punctuation (in milliseconds)
DEFAULT_PAUSE_MAP = {
    ",": 180,
    ";": 250,
    ":": 250,
    ".": 350,
    "?": 400,
    "!": 350,
    "…": 450,
    "\n": 500,
}

@dataclass
class NarrationSegment:
    id: int
    text: str
    original_segment_ids: List[int]
    target_start_time: float
    target_end_time: float
    target_duration: float
    audio_path: Optional[str] = None
    natural_duration: float = 0.0
    final_duration: float = 0.0
    applied_speed: float = 1.0
    pause_after_ms: int = 0
    processing_mode: str = "natural"  # "natural", "natural_with_silence", "slight_speed_adjustment", "time_stretch"
    status: str = "pending"  # "pending", "generating", "generated", "validated", "failed"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TextNormalizer:
    """Normalizes raw input/subtitle text for TTS prosody and clean reading."""

    @staticmethod
    def normalize(text: str) -> str:
        if not text:
            return ""
        
        # 1. Clean HTML/XML tags if any
        clean = re.sub(r"<[^>]+>", "", text)
        
        # 2. Clean speaker labels (e.g. "Nam: Hello", "[Music]")
        clean = re.sub(r"\[[^\]]*\]", "", clean)
        clean = re.sub(r"\([^\)]*\)", "", clean)
        clean = re.sub(r"^[A-Z0-9_a-z\s]+:\s*", "", clean)

        # 3. Normalize multiple whitespace and line breaks
        clean = re.sub(r"[\r\n]+", " ", clean)
        clean = re.sub(r"\s+", " ", clean)

        # 4. Fix spaced punctuation (e.g. "xin chào !" -> "xin chào!")
        clean = re.sub(r"\s+([,\.\?!:;])", r"\1", clean)

        return clean.strip()


class SentenceGrouper:
    """
    SRT-First Narration Grouper.
    Respects SRT START timestamps as the primary anchor for narration start times.
    Only merges consecutive subtitle fragments if they form part of a single continuous sentence 
    without significant time gaps between them.
    """

    def __init__(self, max_chars_per_chunk: int = 250, max_gap_seconds: float = 0.8):
        self.max_chars_per_chunk = max_chars_per_chunk
        self.max_gap_seconds = max_gap_seconds

    def group_segments(self, raw_segments: List[Dict[str, Any]]) -> List[NarrationSegment]:
        if not raw_segments:
            return []

        grouped_narration: List[NarrationSegment] = []
        
        current_text_parts = []
        current_seg_ids = []
        current_start = None
        current_end = 0.0

        for idx, seg in enumerate(raw_segments):
            seg_id = seg.get("id", idx + 1)
            raw_text = seg.get("translation") or seg.get("text") or ""
            clean_text = TextNormalizer.normalize(raw_text)
            
            start_t = float(seg.get("effective_start", seg.get("start", 0.0)))
            end_t = float(seg.get("effective_end", seg.get("end", 0.0)))

            # If there is a significant gap to the next segment, forceflush current group
            has_gap = (current_end > 0.0) and ((start_t - current_end) > self.max_gap_seconds)

            if current_text_parts and has_gap:
                combined_text = " ".join(current_text_parts).strip()
                target_dur = round(current_end - (current_start or 0.0), 3)
                grouped_narration.append(NarrationSegment(
                    id=len(grouped_narration) + 1,
                    text=combined_text,
                    original_segment_ids=list(current_seg_ids),
                    target_start_time=current_start or 0.0,
                    target_end_time=current_end,
                    target_duration=target_dur
                ))
                current_text_parts = []
                current_seg_ids = []
                current_start = None
                current_end = 0.0

            if current_start is None:
                current_start = start_t
            
            current_end = max(current_end, end_t)

            if clean_text:
                current_text_parts.append(clean_text)
                current_seg_ids.append(seg_id)

            combined_text = " ".join(current_text_parts).strip()

            is_sentence_end = bool(re.search(r"[\.\?!]\s*$", clean_text)) or (idx == len(raw_segments) - 1)
            is_too_long = len(combined_text) >= self.max_chars_per_chunk

            if combined_text and (is_sentence_end or is_too_long):
                target_dur = round(current_end - current_start, 3)
                grouped_narration.append(NarrationSegment(
                    id=len(grouped_narration) + 1,
                    text=combined_text,
                    original_segment_ids=list(current_seg_ids),
                    target_start_time=current_start,
                    target_end_time=current_end,
                    target_duration=target_dur
                ))

                current_text_parts = []
                current_seg_ids = []
                current_start = None
                current_end = 0.0

        if current_text_parts:
            combined_text = " ".join(current_text_parts).strip()
            target_dur = round(current_end - (current_start or 0.0), 3)
            grouped_narration.append(NarrationSegment(
                id=len(grouped_narration) + 1,
                text=combined_text,
                original_segment_ids=list(current_seg_ids),
                target_start_time=current_start or 0.0,
                target_end_time=current_end,
                target_duration=target_dur
            ))

        logger.info(f"[SRT-NARRATION] Grouped {len(raw_segments)} SRT entries into {len(grouped_narration)} SRT-aligned narration units.")
        return grouped_narration


class NaturalPacingEngine:
    """
    Pacing Engine prioritizing Sentence-Start Alignment and Natural Speech Speed (0.95x - 1.05x).
    Fills timeline gaps with natural silence instead of aggressive time-stretching.
    """

    def __init__(
        self,
        min_speed: float = 0.95,
        max_speed: float = 1.05,
        pause_map: Optional[Dict[str, int]] = None
    ):
        self.min_speed = min_speed
        self.max_speed = max_speed
        self.pause_map = pause_map or DEFAULT_PAUSE_MAP

    def calculate_pause_duration(self, text: str) -> int:
        """Calculate natural pause in milliseconds based on ending punctuation of sentence."""
        if not text:
            return self.pause_map.get(".", 350)
        
        last_char = text.strip()[-1]
        return self.pause_map.get(last_char, self.pause_map.get(".", 350))

    def evaluate_pacing(
        self,
        natural_audio_duration: float,
        target_available_duration: float,
        text: str
    ) -> Tuple[float, float, int, str]:
        """
        Decision algorithm:
        Returns (applied_speed, final_duration, trailing_silence_ms, processing_mode)
        """
        if target_available_duration <= 0.0 or natural_audio_duration <= 0.0:
            return 1.0, natural_audio_duration, 0, "natural"

        raw_speed_ratio = natural_audio_duration / target_available_duration
        pause_ms = self.calculate_pause_duration(text)

        # Case 1: Audio fits within target duration naturally or ends early
        if natural_audio_duration <= target_available_duration:
            applied_speed = 1.0
            final_dur = natural_audio_duration
            remaining_dur = target_available_duration - natural_audio_duration
            trailing_silence_ms = max(pause_ms, int(remaining_dur * 1000))
            return applied_speed, final_dur, trailing_silence_ms, "natural_with_silence"

        # Case 2: Audio is longer than target duration - attempt slight speed adjustment (0.95x - 1.05x)
        if raw_speed_ratio <= self.max_speed:
            applied_speed = round(raw_speed_ratio, 4)
            final_dur = target_available_duration
            return applied_speed, final_dur, pause_ms, "slight_speed_adjustment"

        # Case 3: Audio is significantly longer - clamp speed to max_speed (1.05x) and allow flexible end duration
        applied_speed = self.max_speed
        final_dur = round(natural_audio_duration / self.max_speed, 3)
        return applied_speed, final_dur, pause_ms, "time_stretch"
