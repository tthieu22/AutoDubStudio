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
    videoProps: Optional[Dict[str, Any]] = None

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

        # 1. PROCESS BASE VIDEO LAYER PROPERTIES
        video_layers = [l for l in visible_layers if l.type == "video"]
        if video_layers:
            video_layer = video_layers[0]
            vprops = video_layer.videoProps or {}
            
            transform = vprops.get("transform", {})
            color = vprops.get("color", {})
            filter_preset = vprops.get("filter", {}).get("preset", "none")
            playback = vprops.get("playback", {})
            opacity = vprops.get("opacity", 1.0)
            
            v_filters = []
            
            # Flips
            if transform.get("flipX"):
                v_filters.append("hflip")
            if transform.get("flipY"):
                v_filters.append("vflip")
                
            # Scale
            scale_val = transform.get("scale", 1.0)
            if scale_val != 1.0:
                v_filters.append(f"scale=iw*{scale_val}:ih*{scale_val}")
                
            # Rotation
            rot_val = transform.get("rotation", 0.0)
            if rot_val != 0.0:
                v_filters.append(f"rotate={rot_val}*PI/180")
                
            # Position offsets (pad to target dimension with black background)
            pos_x = transform.get("x", 0.0)
            pos_y = transform.get("y", 0.0)
            if pos_x != 0.0 or pos_y != 0.0:
                target_w = self.width
                target_h = self.height
                v_filters.append(f"pad={target_w}:{target_h}:({target_w}-iw)/2+{pos_x}:({target_h}-ih)/2+{pos_y}:color=black")
                
            # Color adjustments
            brightness = color.get("brightness", 0.0)
            exposure = color.get("exposure", 0.0)
            contrast = color.get("contrast", 0.0)
            saturation = color.get("saturation", 0.0)
            gamma = color.get("gamma", 1.0)
            
            eq_brightness = (brightness + exposure) / 100.0
            eq_contrast = 1.0 + (contrast / 100.0)
            eq_saturation = 1.0 + (saturation / 100.0)
            
            if eq_brightness != 0.0 or eq_contrast != 1.0 or eq_saturation != 1.0 or gamma != 1.0:
                v_filters.append(f"eq=brightness={eq_brightness}:contrast={eq_contrast}:saturation={eq_saturation}:gamma={gamma}")
                
            # Hue
            hue_val = color.get("hue", 0.0)
            if hue_val != 0.0:
                v_filters.append(f"hue=h={hue_val}")
                
            # Temperature & Tint
            temp = color.get("temperature", 0.0)
            tint = color.get("tint", 0.0)
            if temp != 0.0 or tint != 0.0:
                rm = temp / 500.0
                bm = -temp / 500.0
                gm = tint / 500.0
                v_filters.append(f"colorbalance=rm={rm}:bm={bm}:gm={gm}")
                
            # Presets
            if filter_preset == "warm":
                v_filters.append("colorbalance=rm=0.15:bm=-0.1:gm=-0.05,eq=saturation=1.1")
            elif filter_preset == "cool":
                v_filters.append("colorbalance=rm=-0.1:bm=0.15,eq=saturation=0.9")
            elif filter_preset == "cinematic":
                v_filters.append("eq=contrast=1.25:saturation=0.85:brightness=-0.05")
            elif filter_preset == "grayscale":
                v_filters.append("eq=saturation=0")
            elif filter_preset == "vintage":
                v_filters.append("colorbalance=rm=0.1:gm=0.05:bm=-0.15,eq=contrast=0.95:saturation=0.85")
            elif filter_preset == "high-contrast":
                v_filters.append("eq=contrast=1.3")
            elif filter_preset == "low-contrast":
                v_filters.append("eq=contrast=0.7:brightness=0.05")
                
            # Opacity
            if opacity < 1.0:
                v_filters.append(f"format=rgba,colorchannelmixer=aa={opacity}")
                
            # Playback speed
            speed = playback.get("speed", 1.0)
            if speed != 1.0 and speed > 0:
                v_filters.append(f"setpts=PTS/{speed}")
                
            if v_filters:
                out_label = "[v_video_processed]"
                filter_chains.append(f"{last_stream}{','.join(v_filters)}{out_label}")
                last_stream = out_label

        for layer in visible_layers:
            if layer.type == "video":
                continue # Already processed

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
        return filtergraph, extra_inputs, last_stream
