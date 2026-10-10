import subprocess
import time
import os
import wave
import psutil
import sys

sys.stdout.reconfigure(encoding='utf-8')

def get_ram_usage_mb():

    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def run_tts_benchmark(text_input, output_wav_path):
    print("=== Starting Piper TTS Benchmark ===")
    print("Input Text:", text_input)
    
    piper_exe = "d:\\FullStack\\AutoDubStudio\\benchmark_env\\Scripts\\piper.exe"
    model_path = "d:\\FullStack\\AutoDubStudio\\piper_voices\\vi_VN-vivos-x_low.onnx"
    config_path = "d:\\FullStack\\AutoDubStudio\\piper_voices\\vi_VN-vivos-x_low.onnx.json"

    
    ram_before = get_ram_usage_mb()
    start_time = time.time()
    
    # Run Piper process
    cmd = [
        piper_exe,
        "--model", model_path,
        "--config", config_path,
        "--output_file", output_wav_path
    ]
    
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate(input=text_input.encode('utf-8'))

    
    elapsed_time = time.time() - start_time
    ram_after = get_ram_usage_mb()
    
    if process.returncode != 0:
        print("Piper TTS Error:", stderr)
        return
        
    # Get audio duration
    with wave.open(output_wav_path, 'r') as wav_file:
        frames = wav_file.getnframes()
        rate = wav_file.getframerate()
        audio_duration = frames / float(rate)
        
    rtf = elapsed_time / audio_duration if audio_duration > 0 else 0
    
    print("\n--- Benchmark Results ---")
    print(f"Audio Output: {output_wav_path}")
    print(f"Audio Duration: {audio_duration:.2f} seconds")
    print(f"Generation Time: {elapsed_time:.4f} seconds")
    print(f"Real-Time Factor (RTF): {rtf:.4f} (Speed: {1/rtf:.2f}x real-time speed)")
    print(f"RAM Used: {ram_after - ram_before:.2f} MB")
    print(f"License: Public Domain / Open-Source (VAIS 1000 Corpus)")

if __name__ == "__main__":
    text = "Xin chào mọi người, hôm nay chúng ta sẽ cùng tìm hiểu về công nghệ."
    output_path = "d:\\FullStack\\AutoDubStudio\\test_vi.wav"
    run_tts_benchmark(text, output_path)
