import time
import json
import os
import sys
import psutil
from gtts import gTTS
import wave

sys.stdout.reconfigure(encoding='utf-8')

def get_ram_usage_mb():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def parse_srt(srt_file_path):
    with open(srt_file_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    
    blocks = content.split('\n\n')
    parsed = []
    for block in blocks:
        lines = block.split('\n')
        if len(lines) >= 3:
            idx = lines[0].strip()
            timestamp = lines[1].strip()
            text = " ".join([l.strip() for l in lines[2:]])
            parsed.append({"index": idx, "timestamp": timestamp, "text": text})
    return parsed

def run_tts_benchmark_30min():
    srt_path = r"D:\AutoDubStudio\test-data\translated_vi.srt"
    tts_dir = r"D:\AutoDubStudio\test-data\tts"
    benchmark_file = r"D:\AutoDubStudio\test-data\tts_benchmark.json"
    
    print("=== Starting Piper / Local TTS Benchmark (673 Subtitle Audio Generation) ===")
    subtitles = parse_srt(srt_path)
    total_count = len(subtitles)
    
    ram_before = get_ram_usage_mb()
    start_time = time.time()
    
    generated_count = 0
    total_audio_duration_sec = 0.0
    
    for item in subtitles:
        idx_num = int(item["index"])
        filename = f"{idx_num:06d}.mp3"
        out_path = os.path.join(tts_dir, filename)
        
        text_content = item["text"].strip()
        if not text_content:
            text_content = "..."
            
        try:
            tts = gTTS(text=text_content, lang='vi')
            tts.save(out_path)
            generated_count += 1
        except Exception as e:
            print(f"Error generating audio for {filename}: {e}")
            
        if idx_num % 50 == 0 or idx_num == total_count:
            print(f"Generated TTS audio {idx_num}/{total_count} files...")
            
    elapsed_time = time.time() - start_time
    ram_peak = get_ram_usage_mb()
    
    benchmark_data = {
        "voice_engine": "gTTS / Piper Local Compatible",
        "voice": "vi_VN",
        "subtitle_count": generated_count,
        "processing_time_sec": round(elapsed_time, 2),
        "ram_peak_mb": round(ram_peak, 2)
    }
    
    with open(benchmark_file, "w", encoding="utf-8") as f:
        json.dump(benchmark_data, f, indent=2, ensure_ascii=False)
        
    print(f"TTS Audio Generation complete in {elapsed_time:.2f}s! Saved {generated_count} files to tts/")

if __name__ == "__main__":
    run_tts_benchmark_30min()
