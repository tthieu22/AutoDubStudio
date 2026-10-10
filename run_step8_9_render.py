import time
import json
import os
import sys
import imageio_ffmpeg
import subprocess

sys.stdout.reconfigure(encoding='utf-8')

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
            
            # parse start & end timestamp seconds
            start_str, end_str = timestamp.split(' --> ')
            
            def str_to_sec(s):
                h, m, sec_ms = s.split(':')
                sec, ms = sec_ms.split(',')
                return int(h)*3600 + int(m)*60 + int(sec) + int(ms)/1000.0
                
            start_sec = str_to_sec(start_str)
            end_sec = str_to_sec(end_str)
            duration = end_sec - start_sec
            
            parsed.append({
                "index": idx,
                "start_sec": start_sec,
                "end_sec": end_sec,
                "duration": duration,
                "text": text
            })
    return parsed

def run_sync_and_render_30min():
    video_path = r"D:\AutoDubStudio\test-data\test_30min.mp4"
    srt_path = r"D:\AutoDubStudio\test-data\translated_vi.srt"
    tts_dir = r"D:\AutoDubStudio\test-data\tts"
    concat_audio_path = r"D:\AutoDubStudio\test-data\vietnamese_dubbed.mp3"
    output_video = r"D:\AutoDubStudio\test-data\test_30min_vi.mp4"
    benchmark_file = r"D:\AutoDubStudio\test-data\rendering_benchmark.json"
    
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    print("=== Starting Audio Synchronization & FFmpeg Video Render ===")
    subtitles = parse_srt(srt_path)
    total_count = len(subtitles)
    
    # Generate concat file list for FFmpeg
    concat_txt_path = r"D:\AutoDubStudio\test-data\concat_list.txt"
    with open(concat_txt_path, "w", encoding="utf-8") as f:
        for item in subtitles:
            idx_num = int(item["index"])
            audio_file = os.path.join(tts_dir, f"{idx_num:06d}.mp3").replace('\\', '/')
            f.write(f"file '{audio_file}'\n")
            
    print("Merging 673 TTS audio files into full dubbed audio track...")
    cmd_concat = [
        ffmpeg_exe, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_txt_path,
        "-c", "copy",
        concat_audio_path
    ]
    subprocess.run(cmd_concat, check=True)
    
    print("Rendering final dubbed video with FFmpeg...")
    start_render = time.time()
    
    # FFmpeg mux video + new vietnamese dubbed audio
    cmd_render = [
        ffmpeg_exe, "-y",
        "-i", video_path,
        "-i", concat_audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_video
    ]
    
    proc = subprocess.Popen(cmd_render, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    
    elapsed_render = time.time() - start_render
    
    file_size_mb = os.path.getsize(output_video) / (1024 * 1024)
    
    benchmark_data = {
        "output_file": "test_30min_vi.mp4",
        "output_size_mb": round(file_size_mb, 2),
        "rendering_time_sec": round(elapsed_render, 2),
        "speedup_factor": round(2115.11 / elapsed_render, 2) if elapsed_render > 0 else 0
    }
    
    with open(benchmark_file, "w", encoding="utf-8") as f:
        json.dump(benchmark_data, f, indent=2, ensure_ascii=False)
        
    print(f"Rendering completed in {elapsed_render:.2f}s! Output: test_30min_vi.mp4 ({file_size_mb:.2f} MB)")

if __name__ == "__main__":
    run_sync_and_render_30min()
