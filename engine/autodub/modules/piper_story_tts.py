import os
import wave
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from autodub.models.project import Project
from autodub.modules.tts import RealTTS
from autodub.exceptions import AutoDubError

class StoryTTSEngine:
    def __init__(self, project: Project):
        self.project = project
        self.project_dir = project.project_dir
        self.audio_dir = self.project_dir / "assets" / "audio"
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.tts_runner = RealTTS()

    def _create_synthetic_wav(self, text: str, output_path: Path, duration_sec: float = 3.0):
        """Creates a silent 16-bit 22.5kHz WAV file for testing when Piper ONNX binary is absent."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        sample_rate = 22050
        num_samples = int(sample_rate * duration_sec)
        with wave.open(str(output_path), 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(b'\x00\x00' * num_samples)

    def generate_audio_for_scene(self, scene: Dict[str, Any], force: bool = False) -> Path:
        scene_id = scene.get("id", "scene_001")
        output_wav = self.audio_dir / f"{scene_id}.wav"
        text = scene.get("narration") or "Cảnh phim tự động."
        speaker = scene.get("speaker", "NARRATOR")

        # Determine Piper Voice model based on Character Bible
        voice_model = "vi_VN-viss-low.onnx"
        characters = self.project.data.get("characters", [])
        for c in characters:
            if c.get("name") == speaker or c.get("gender") == speaker:
                voice_model = c.get("assigned_voice", voice_model)
                break

        # Generate Audio using RealTTS Piper fallback
        generated = False
        try:
            exe = self.tts_runner.client.find_executable()
            if exe and exe.exists():
                self.tts_runner.client.synthesize(text, output_wav, voice=voice_model)
                generated = True
        except Exception:
            pass

        if not generated:
            est_dur = max(2.0, len(text.split()) * 0.4)
            self._create_synthetic_wav(text, output_wav, duration_sec=est_dur)

        # Get exact audio duration
        duration = 3.0
        try:
            with wave.open(str(output_wav), 'rb') as w:
                frames = w.getnframes()
                rate = w.getframerate()
                duration = round(frames / float(rate), 2)
        except Exception:
            pass

        # Update scene metadata
        scene["audio_path"] = f"assets/audio/{scene_id}.wav"
        scene["audio_duration"] = duration
        scene["duration"] = duration

        scene_file = self.project_dir / "scenes" / f"{scene_id}.json"
        if scene_file.exists():
            with open(scene_file, "w", encoding="utf-8") as f:
                json.dump(scene, f, indent=2, ensure_ascii=False)

        self.project.save()
        return output_wav
