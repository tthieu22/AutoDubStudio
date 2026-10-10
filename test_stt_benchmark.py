import time
import json
import os
import sys
import psutil
from faster_whisper import WhisperModel

def get_ram_usage_mb():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def run_benchmark(audio_file_path, model_size="small", device="cpu", compute_type="int8"):
    print(f"=== Starting STT Benchmark for model: {model_size} ({device}/{compute_type}) ===")
    
    ram_before = get_ram_usage_mb()
    load_start = time.time()
    
    # Load model
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    load_time = time.time() - load_start
    ram_after_load = get_ram_usage_mb()
    
    print(f"Model loaded in {load_time:.2f}s. RAM used: {ram_after_load - ram_before:.2f} MB")
    
    # Process transcription
    process_start = time.time()
    segments, info = model.transcribe(audio_file_path, beam_size=5)
    
    transcript_text = []
    srt_lines = []
    
    segment_count = 0
    for i, segment in enumerate(segments, start=1):
        segment_count += 1
        transcript_text.append(segment.text.strip())
        
        start_str = format_timestamp(segment.start)
        end_str = format_timestamp(segment.end)
        
        srt_lines.append(f"{i}\n{start_str} --> {end_str}\n{segment.text.strip()}\n")
    
    process_time = time.time() - process_start
    ram_peak = get_ram_usage_mb()
    
    audio_duration = info.duration
    rtf = process_time / audio_duration if audio_duration > 0 else 0
    
    print(f"\n--- Benchmark Results ---")
    print(f"Audio duration: {audio_duration:.2f}s")
    print(f"Processing time: {process_time:.2f}s")
    print(f"Real-Time Factor (RTF): {rtf:.4f} (Speed: {1/rtf:.2f}x real-time)")
    print(f"Language detected: {info.language} (Probability: {info.language_probability:.2f})")
    
    # Export files
    output_dir = "d:\\FullStack\\AutoDubStudio"
    
    with open(os.path.join(output_dir, "transcript.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(transcript_text))
        
    with open(os.path.join(output_dir, "subtitle.srt"), "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines))
        
    benchmark_data = {
        "model": model_size,
        "device": device,
        "compute_type": compute_type,
        "audio_duration_sec": round(audio_duration, 2),
        "load_time_sec": round(load_time, 2),
        "processing_time_sec": round(process_time, 2),
        "rtf": round(rtf, 4),
        "ram_load_mb": round(ram_after_load - ram_before, 2),
        "ram_peak_mb": round(ram_peak, 2),
        "language": info.language,
        "segment_count": segment_count
    }
    
    with open(os.path.join(output_dir, "benchmark_stt.json"), "w", encoding="utf-8") as f:
        json.dump(benchmark_data, f, indent=2, ensure_ascii=False)
        
    print(f"\nSaved outputs to:\n - transcript.txt\n - subtitle.srt\n - benchmark_stt.json")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        audio_path = sys.argv[1]
    else:
        audio_path = os.path.join("d:\\FullStack\\AutoDubStudio", "sample.wav")
        
    run_benchmark(audio_path, model_size="small", device="cpu", compute_type="int8")
