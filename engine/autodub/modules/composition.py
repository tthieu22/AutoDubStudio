import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any


@dataclass
class Layer:
    id: str
    type: str  # 'video', 'audio', 'subtitle', 'text', 'title', 'image', 'logo'
    source: Optional[str] = None  # file path or image path
    text: Optional[str] = None  # for text/title layers
    start: float = 0.0  # seconds
    duration: float = 0.0  # seconds (0.0 = entire video)
    x: int = 0
    y: int = 0
    width: Optional[int] = None
    height: Optional[int] = None
    scale: float = 1.0
    opacity: float = 1.0
    rotation: float = 0.0  # degrees
    z_index: int = 0
    style: Dict[str, Any] = field(default_factory=dict)
    fade_in_sec: float = 0.0
    fade_out_sec: float = 0.0
    visible: bool = True
    locked: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Layer":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Composition:
    version: int = 1
    width: int = 1920
    height: int = 1080
    fps: float = 30.0
    duration: float = 0.0
    layers: List[Layer] = field(default_factory=list)

    @classmethod
    def load(cls, filepath: Path) -> "Composition":
        if not filepath.exists():
            return cls()
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        layers_data = data.pop("layers", [])
        comp = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        comp.layers = [Layer.from_dict(ld) for ld in layers_data]
        return comp

    def save(self, filepath: Path) -> None:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": self.version,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "duration": self.duration,
            "layers": [l.to_dict() for l in self.layers]
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_sorted_layers(self) -> List[Layer]:
        return sorted([l for l in self.layers if l.visible], key=lambda l: l.z_index)

    def build_ffmpeg_filtergraph(self, base_video_stream: str = "[0:v]") -> tuple[str, List[str]]:
        """
        Generates complex filter string for FFmpeg overlays and returns (filtergraph_str, extra_input_files)
        """
        extra_inputs: List[str] = []
        filter_chains: List[str] = []

        visible_layers = self.get_sorted_layers()
        last_stream = base_video_stream
        input_idx = 1  # 0 is base video

        for layer in visible_layers:
            if layer.type in ["image", "logo"] and layer.source:
                img_path = Path(layer.source)
                if img_path.exists():
                    extra_inputs.append(str(img_path.resolve()))
                    in_label = f"[{input_idx}:v]"
                    scaled_label = f"[scaled_{input_idx}]"
                    out_label = f"[v_out_{input_idx}]"

                    # Build scale/opacity filters
                    filters = []
                    if layer.scale != 1.0 or layer.width or layer.height:
                        if layer.width and layer.height:
                            filters.append(f"scale={layer.width}:{layer.height}")
                        else:
                            filters.append(f"scale=iw*{layer.scale}:ih*{layer.scale}")
                    
                    if layer.opacity < 1.0:
                        filters.append(f"format=rgba,colorchannelmixer=aa={layer.opacity}")

                    if filters:
                        filter_chains.append(f"{in_label}{','.join(filters)}{scaled_label}")
                        overlay_input = scaled_label
                    else:
                        overlay_input = in_label

                    enable_expr = ""
                    if layer.duration > 0:
                        enable_expr = f":enable='between(t,{layer.start},{layer.start + layer.duration})'"

                    filter_chains.append(
                        f"{last_stream}{overlay_input}overlay=x={layer.x}:y={layer.y}{enable_expr}{out_label}"
                    )
                    last_stream = out_label
                    input_idx += 1

            elif layer.type in ["text", "title", "logo"] and layer.text:
                out_label = f"[v_out_txt_{layer.id}]"
                font_size = layer.style.get("font_size", 48)
                font_color = layer.style.get("color", "white")
                border_w = layer.style.get("border_width", 2)
                border_color = layer.style.get("border_color", "black")
                clean_text = layer.text.replace("'", "'\\''").replace(":", "\\:")

                drawtext_cmd = (
                    f"drawtext=text='{clean_text}':x={layer.x}:y={layer.y}:fontsize={font_size}:"
                    f"fontcolor={font_color}:borderw={border_w}:bordercolor={border_color}"
                )
                if layer.duration > 0:
                    drawtext_cmd += f":enable='between(t,{layer.start},{layer.start + layer.duration})'"

                filter_chains.append(f"{last_stream}{drawtext_cmd}{out_label}")
                last_stream = out_label

        filtergraph = ";".join(filter_chains)
        return filtergraph, extra_inputs
