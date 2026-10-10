import time
import os
import psutil
import sys
from gtts import gTTS

sys.stdout.reconfigure(encoding='utf-8')

def get_ram_usage_mb():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def run_tts_benchmark(text_input, output_audio_path):
    print("=== Starting TTS Benchmark (gTTS Free Engine) ===")
    print("Input Text:", text_input)
    
    ram_before = get_ram_usage_mb()
    start_time = time.time()
    
    tts = gTTS(text=text_input, lang='vi')
    tts.save(output_audio_path)
    
    elapsed_time = time.time() - start_time
    ram_after = get_ram_usage_mb()
    
    file_size_kb = os.path.getsize(output_audio_path) / 1024
    
    print("\n--- Benchmark Results ---")
    print(f"Audio Output File: {output_audio_path}")
    print(f"File Size: {file_size_kb:.2f} KB")
    print(f"Generation Time: {elapsed_time:.4f} seconds")
    print(f"RAM Used: {ram_after - ram_before:.2f} MB")
    print(f"License: FREE / Open API Engine")

if __name__ == "__main__":
    text = "Xin chào mọi người, hôm nay chúng ta sẽ cùng tìm hiểu về công nghệ."
    output_path = "d:\\FullStack\\AutoDubStudio\\test_vi.mp3"
    run_tts_benchmark(text, output_path)
