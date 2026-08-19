import subprocess
import time
import os
import imageio_ffmpeg
import psutil
import sys

sys.stdout.reconfigure(encoding='utf-8')

def get_ram_usage_mb():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def run_ffmpeg_benchmark():
    print("=== Starting FFmpeg Video Muxing & Editing Benchmark ===")
    
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    audio_path = "d:\\FullStack\\AutoDubStudio\\test_vi.mp3"
    subtitle_path = "d:\\FullStack\\AutoDubStudio\\subtitle.srt"
    output_video = "d:\\FullStack\\AutoDubStudio\\output_vi.mp4"
    
    ram_before = get_ram_usage_mb()
    start_time = time.time()
    
    # 1. Tạo video canvas 10s bằng FFmpeg color generator và lồng tiếng mp3 + muxing srt
    cmd = [
        ffmpeg_exe,
        "-y", # overwrite
        "-f", "lavfi",
        "-i", "color=c=black:s=1280x720:r=30:d=10",
        "-i", audio_path,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        output_video
    ]
    
    print("Executing FFmpeg render command...")
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    
    elapsed_time = time.time() - start_time
    ram_after = get_ram_usage_mb()
    
    if process.returncode != 0:
        print("FFmpeg Error:", stderr.decode('utf-8', errors='ignore'))
        return
        
    file_size_mb = os.path.getsize(output_video) / (1024 * 1024)
    
    print("\n--- Benchmark Results ---")
    print(f"Output Video File: {output_video}")
    print(f"Video Size: {file_size_mb:.2f} MB")
    print(f"Rendering Time: {elapsed_time:.4f} seconds")
    print(f"RAM Used: {ram_after - ram_before:.2f} MB")
    print(f"Speed: {10 / elapsed_time:.2f}x real-time rendering speed!")

if __name__ == "__main__":
    run_ffmpeg_benchmark()
