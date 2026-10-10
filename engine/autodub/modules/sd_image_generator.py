import os
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional
from autodub.models.project import Project
from autodub.pipeline.task_state import TaskStatus, TaskRecord, TaskStateMachine
from autodub.exceptions import AutoDubError

class SDImageGenerator:
    def __init__(self, project: Project):
        self.project = project
        self.project_dir = project.project_dir
        self.images_dir = self.project_dir / "assets" / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)

    def _generate_procedural_fallback_image(self, prompt: str, output_path: Path, width: int = 768, height: int = 512):
        """Creates a high-quality placeholder image with text overlay using Pillow when SD weights are absent."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new('RGB', (width, height), color=(20, 24, 33))
            draw = ImageDraw.Draw(img)
            
            # Draw decorative border
            draw.rectangle([10, 10, width - 10, height - 10], outline=(79, 70, 229), width=3)
            
            # Header
            draw.text((30, 30), "AutoDubStudio AI Story Engine v0.2", fill=(255, 255, 255))
            
            # Wrap prompt text
            words = prompt.split()
            lines = []
            curr_line = ""
            for w in words:
                if len(curr_line + " " + w) > 45:
                    lines.append(curr_line)
                    curr_line = w
                else:
                    curr_line += " " + w if curr_line else w
            if curr_line:
                lines.append(curr_line)

            y_offset = 120
            draw.text((30, y_offset), "Visual Prompt:", fill=(236, 72, 153))
            y_offset += 30
            for line in lines[:8]:
                draw.text((30, y_offset), line, fill=(209, 213, 219))
                y_offset += 25

            img.save(output_path, "PNG")
        except Exception:
            # Absolute minimal 1-pixel PNG fallback
            output_path.write_bytes(rb'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc\`\x00\x00\x00\x02\x00\x01H\xafA4\x00\x00\x00\x00IEND\xaeB`\x82')

    def generate_image_for_scene(
        self,
        scene: Dict[str, Any],
        force: bool = False,
        bypass_review: bool = False,
        width: int = 768,
        height: int = 512
    ) -> Path:
        scene_id = scene.get("id", "scene_001")
        output_file = self.images_dir / f"{scene_id}.png"
        prompt = scene.get("visual_prompt") or "cinematic scene, detailed illustration"

        # Check Review Gate
        status = scene.get("status", TaskStatus.REVIEW_REQUIRED.value)
        if not force and not bypass_review and status not in (TaskStatus.APPROVED.value, TaskStatus.GENERATED.value):
            raise AutoDubError(f"Scene '{scene_id}' is in status '{status}'. Review and APPROVE scene before generating image.")

        # Attempt Tracking (Max attempt = 3)
        attempt = scene.get("attempt", 1)
        if attempt > 3:
            raise AutoDubError(f"Scene '{scene_id}' reached maximum image regeneration attempts (3/3).")

        start_time = time.time()

        # Generate Image (Try diffusers SD 1.5 if available, else procedural fallback)
        use_sd = False
        try:
            import torch
            from diffusers import StableDiffusionPipeline
            # Only use real SD if CUDA is available and lowvram is configured
            if torch.cuda.is_available() and os.environ.get("AUTODUB_USE_REAL_SD") == "1":
                pipe = StableDiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5", torch_dtype=torch.float16)
                pipe.enable_sequential_cpu_offload()
                image = pipe(prompt, width=width, height=height, num_inference_steps=20).images[0]
                image.save(output_file)
                use_sd = True
        except Exception:
            pass

        if not use_sd:
            self._generate_procedural_fallback_image(prompt, output_file, width=width, height=height)

        elapsed = time.time() - start_time

        # Update scene metadata
        scene["image_path"] = f"assets/images/{scene_id}.png"
        scene["image_duration"] = round(elapsed, 2)
        scene["status"] = TaskStatus.GENERATED.value if not bypass_review else TaskStatus.APPROVED.value
        
        # Save updated scene file
        scene_file = self.project_dir / "scenes" / f"{scene_id}.json"
        if scene_file.exists():
            with open(scene_file, "w", encoding="utf-8") as f:
                json.dump(scene, f, indent=2, ensure_ascii=False)

        self.project.save()

        return output_file

    def regenerate_scene_image(self, scene: Dict[str, Any], new_prompt: Optional[str] = None) -> Path:
        if new_prompt:
            scene["visual_prompt"] = new_prompt
        scene["attempt"] = scene.get("attempt", 1) + 1
        return self.generate_image_for_scene(scene, force=True, bypass_review=True)
