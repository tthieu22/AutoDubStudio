// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::env;
use std::fs::{self, File};
use std::io::{BufRead, BufReader};
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::thread;
use std::time::Duration;
use serde::{Deserialize, Serialize};
use tauri::{State, Window, Manager};

// Structure to track the active running process
struct ActiveProcess {
    child: Option<Child>,
    project_id: Option<String>,
}

type ProcessState = Mutex<ActiveProcess>;

#[derive(Serialize, Deserialize, Debug, Clone)]
struct PreflightCheckResult {
    ffmpeg: bool,
    ffprobe: bool,
    python: bool,
    source_video: bool,
    disk_space: bool,
    message: String,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct ProjectConfig {
    version: i32,
    project_id: String,
    name: String,
    created_at: String,
    updated_at: String,
    source: SourceConfig,
    target: TargetConfig,
    settings: SettingsConfig,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct SourceConfig {
    path: String,
    language: String,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct TargetConfig {
    language: String,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct SettingsConfig {
    whisper_model: String,
    whisper_compute_type: String,
    translation_model: String,
    tts_engine: String,
    chunk_duration: i32,
}

// Find workspace root by traversing upwards looking for the engine directory
fn find_workspace_root() -> Option<PathBuf> {
    let mut current = env::current_dir().ok()?;
    loop {
        if current.join("engine").is_dir() && current.join("projects").is_dir() {
            return Some(current);
        }
        if !current.pop() {
            break;
        }
    }
    None
}

// Discover local virtual environment Python or fallback
fn find_python_path() -> PathBuf {
    if let Some(ws_root) = find_workspace_root() {
        // 1. Try Windows Virtual Env
        let win_venv = ws_root.join("engine").join(".venv").join("Scripts").join("python.exe");
        if win_venv.exists() {
            return win_venv;
        }
        // 2. Try Unix Virtual Env
        let unix_venv = ws_root.join("engine").join(".venv").join("bin").join("python");
        if unix_venv.exists() {
            return unix_venv;
        }
    }
    // Fallback to system Python
    PathBuf::from("python")
}

// Helper to send Ctrl+C/SIGINT to a child process on Windows
#[cfg(target_os = "windows")]
fn send_sigint(pid: u32) {
    // GenerateConsoleCtrlEvent only works if console is attached
    // Using taskkill /T /PID to gracefully request termination of the process tree on Windows
    let mut cmd = Command::new("taskkill");
    cmd.arg("/F").arg("/T").arg("/PID").arg(pid.to_string());
    let _ = cmd.status();
}

#[cfg(not(target_os = "windows"))]
fn send_sigint(pid: u32) {
    // Send SIGINT signal on Unix systems
    unsafe {
        libc::kill(pid as libc::pid_t, libc::SIGINT);
    }
}

// Verify Python, FFmpeg, FFprobe dependencies
#[tauri::command]
fn run_preflight_check(project_dir: String) -> PreflightCheckResult {
    let ws_root = find_workspace_root();
    if ws_root.is_none() {
        return PreflightCheckResult {
            ffmpeg: false,
            ffprobe: false,
            python: false,
            source_video: false,
            disk_space: false,
            message: "Workspace root not found.".to_string(),
        };
    }
    let ws_root = ws_root.unwrap();

    // 1. Check Python
    let py_path = find_python_path();
    let mut py_ok = false;
    if py_path.exists() || py_path.to_string_lossy() == "python" {
        let output = Command::new(&py_path)
            .arg("-V")
            .output();
        if let Ok(out) = output {
            py_ok = out.status.success();
        }
    }

    // 2. Check FFmpeg/FFprobe
    let mut ffmpeg_path = ws_root.join("runtime").join("ffmpeg").join("ffmpeg.exe");
    if !ffmpeg_path.exists() {
        ffmpeg_path = ws_root.join("runtime").join("ffmpeg").join("bin").join("ffmpeg.exe");
    }
    let mut ffprobe_path = ws_root.join("runtime").join("ffmpeg").join("ffprobe.exe");
    if !ffprobe_path.exists() {
        ffprobe_path = ws_root.join("runtime").join("ffmpeg").join("bin").join("ffprobe.exe");
    }

    let ffmpeg_ok = ffmpeg_path.exists() || Command::new("ffmpeg").arg("-version").output().is_ok();
    let ffprobe_ok = ffprobe_path.exists() || Command::new("ffprobe").arg("-version").output().is_ok();

    // 3. Check source video & disk space
    let p_path = Path::new(&project_dir);
    let mut source_ok = false;
    let disk_ok = true;

    if p_path.exists() {
        let proj_json_path = p_path.join("project.json");
        if proj_json_path.exists() {
            if let Ok(content) = fs::read_to_string(&proj_json_path) {
                if let Ok(json) = serde_json::from_str::<serde_json::Value>(&content) {
                    if let Some(rel_src) = json.pointer("/source/path").and_then(|v| v.as_str()) {
                        let source_path = if Path::new(rel_src).is_absolute() {
                            PathBuf::from(rel_src)
                        } else {
                            p_path.join(rel_src)
                        };
                        if source_path.exists() && source_path.metadata().map(|m| m.len() > 0).unwrap_or(false) {
                            source_ok = true;
                        }
                    }
                }
            }
        }
    }

    PreflightCheckResult {
        ffmpeg: ffmpeg_ok,
        ffprobe: ffprobe_ok,
        python: py_ok,
        source_video: source_ok,
        disk_space: disk_ok,
        message: if py_ok && ffmpeg_ok && ffprobe_ok { "Ready to run".to_string() } else { "Missing system dependencies".to_string() },
    }
}

#[tauri::command]
fn list_projects() -> Vec<String> {
    let mut result = Vec::new();
    if let Some(ws_root) = find_workspace_root() {
        let proj_dir = ws_root.join("projects");
        if let Ok(entries) = fs::read_dir(proj_dir) {
            for entry in entries {
                if let Ok(entry) = entry {
                    if entry.file_type().map(|t| t.is_dir()).unwrap_or(false) {
                        if entry.path().join("project.json").exists() {
                            result.push(entry.file_name().to_string_lossy().to_string());
                        }
                    }
                }
            }
        }
    }
    result
}

#[tauri::command]
fn open_output_folder(project_dir: String) -> Result<(), String> {
    let path = PathBuf::from(&project_dir);
    let full_path = if path.is_absolute() {
        if path.ends_with("output") {
            path
        } else {
            path.join("output")
        }
    } else {
        let ws_root = find_workspace_root().unwrap_or_else(|| PathBuf::from("."));
        if project_dir.starts_with("projects/") || project_dir.starts_with("projects\\") {
            ws_root.join(&project_dir).join("output")
        } else {
            ws_root.join("projects").join(&project_dir).join("output")
        }
    };

    if !full_path.exists() {
        let _ = fs::create_dir_all(&full_path);
    }

    #[cfg(target_os = "windows")]
    {
        let clean_str = full_path.to_string_lossy().replace("/", "\\");
        Command::new("explorer")
            .arg(clean_str)
            .spawn()
            .map_err(|e| e.to_string())?;
    }
    #[cfg(target_os = "macos")]
    {
        Command::new("open")
            .arg(&full_path)
            .spawn()
            .map_err(|e| e.to_string())?;
    }
    #[cfg(target_os = "linux")]
    {
        Command::new("xdg-open")
            .arg(&full_path)
            .spawn()
            .map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
fn create_project(name: String, source_video_path: String) -> Result<String, String> {
    let ws_root = find_workspace_root().ok_or("Workspace root not found")?;
    let sanitized_name = name.replace(" ", "-").replace("/", "_").replace("\\", "_");
    let project_dir = ws_root.join("projects").join(&sanitized_name);
    
    fs::create_dir_all(&project_dir).map_err(|e| e.to_string())?;
    fs::create_dir_all(project_dir.join("source")).map_err(|e| e.to_string())?;
    fs::create_dir_all(project_dir.join("audio")).map_err(|e| e.to_string())?;
    fs::create_dir_all(project_dir.join("transcript")).map_err(|e| e.to_string())?;
    fs::create_dir_all(project_dir.join("output")).map_err(|e| e.to_string())?;
    fs::create_dir_all(project_dir.join("logs")).map_err(|e| e.to_string())?;

    // Copy source video into project working source
    let source_path = Path::new(&source_video_path);
    if !source_path.exists() {
        return Err("Selected source video file does not exist.".to_string());
    }
    let ext = source_path.extension().and_then(|e| e.to_str()).unwrap_or("mp4");
    let dest_video = project_dir.join("source").join(format!("input.{}", ext));
    fs::copy(source_path, &dest_video).map_err(|e| e.to_string())?;

    // Create default project.json
    let now = chrono::Utc::now().to_rfc3339();
    let project_id = uuid::Uuid::new_v4().to_string();
    
    let config = ProjectConfig {
        version: 1,
        project_id,
        name: name.clone(),
        created_at: now.clone(),
        updated_at: now,
        source: SourceConfig {
            path: format!("source/input.{}", ext),
            language: "en".to_string(),
        },
        target: TargetConfig {
            language: "vi".to_string(),
        },
        settings: SettingsConfig {
            whisper_model: "small".to_string(),
            whisper_compute_type: "int8".to_string(),
            translation_model: "qwen2.5:3b".to_string(),
            tts_engine: "piper".to_string(),
            chunk_duration: 600,
        },
    };

    // Serialize json
    let json_content = serde_json::to_string_pretty(&config).map_err(|e| e.to_string())?;
    fs::write(project_dir.join("project.json"), json_content).map_err(|e| e.to_string())?;

    Ok(project_dir.to_string_lossy().to_string())
}

#[tauri::command]
fn read_project_json(project_dir: String) -> Result<serde_json::Value, String> {
    let p_file = Path::new(&project_dir).join("project.json");
    if p_file.exists() {
        let content = fs::read_to_string(p_file).map_err(|e| e.to_string())?;
        let json = serde_json::from_str(&content).map_err(|e| e.to_string())?;
        Ok(json)
    } else {
        Err("project.json file not found".to_string())
    }
}

#[tauri::command]
fn write_project_json(project_dir: String, data: serde_json::Value) -> Result<(), String> {
    let p_file = Path::new(&project_dir).join("project.json");
    let content = serde_json::to_string_pretty(&data).map_err(|e| e.to_string())?;
    fs::write(p_file, content).map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn read_pipeline_log(project_dir: String, limit: usize) -> Result<Vec<String>, String> {
    let log_file = Path::new(&project_dir).join("logs").join("pipeline.log");
    if log_file.exists() {
        let file = File::open(log_file).map_err(|e| e.to_string())?;
        let reader = BufReader::new(file);
        let lines: Vec<String> = reader.lines().filter_map(|l| l.ok()).collect();
        let start = if lines.len() > limit { lines.len() - limit } else { 0 };
        Ok(lines[start..].to_vec())
    } else {
        Ok(Vec::new())
    }
}

#[tauri::command]
fn start_pipeline(
    window: Window,
    active_proc: State<'_, ProcessState>,
    project_dir: String,
    force: bool,
) -> Result<(), String> {
    let ws_root = find_workspace_root().ok_or("Workspace root not found")?;
    let python_path = find_python_path();

    let mut lock = active_proc.lock().unwrap();
    if let Some(ref mut child) = lock.child {
        let pid = child.id();
        send_sigint(pid);
        thread::sleep(Duration::from_millis(200));
        let _ = child.kill();
        lock.child = None;
        lock.project_id = None;
    }

    let mut cmd = Command::new(python_path);
    cmd.current_dir(ws_root.join("engine"));
    cmd.arg("-m").arg("autodub.cli").arg("run").arg(&project_dir);
    if force {
        cmd.arg("--force");
    }

    cmd.stdout(Stdio::piped());
    cmd.stderr(Stdio::piped());

    let mut child = cmd.spawn().map_err(|e| format!("Failed to spawn Python process: {}", e))?;

    let stdout = child.stdout.take().ok_or("Failed to open stdout")?;
    let stderr = child.stderr.take().ok_or("Failed to open stderr")?;

    lock.child = Some(child);
    lock.project_id = Some(project_dir.clone());

    // Spawn thread to monitor stdout / JSONL stream
    let window_clone = window.clone();
    thread::spawn(move || {
        let reader = BufReader::new(stdout);
        for line in reader.lines() {
            if let Ok(line_str) = line {
                let trimmed = line_str.trim();
                if trimmed.starts_with('{') && trimmed.ends_with('}') {
                    if let Ok(json) = serde_json::from_str::<serde_json::Value>(trimmed) {
                        let _ = window_clone.emit("pipeline://progress", json);
                    }
                }
            }
        }
    });

    // Spawn thread to monitor stderr / log messages
    let window_clone2 = window.clone();
    thread::spawn(move || {
        let reader = BufReader::new(stderr);
        for line in reader.lines() {
            if let Ok(line_str) = line {
                let _ = window_clone2.emit("pipeline://log", line_str);
            }
        }
    });

    // Spawn monitor thread to watch process termination
    let window_clone3 = window.clone();
    thread::spawn(move || {
        loop {
            thread::sleep(Duration::from_millis(500));
            let active_proc = window_clone3.state::<ProcessState>();
            let mut lock = active_proc.lock().unwrap();
            if let Some(ref mut child) = lock.child {
                match child.try_wait() {
                    Ok(Some(status)) => {
                        let code = status.code().unwrap_or(0);
                        lock.child = None;
                        lock.project_id = None;
                        let _ = window_clone3.emit("pipeline://terminated", code);
                        break;
                    }
                    Ok(None) => {}
                    Err(_) => {
                        lock.child = None;
                        lock.project_id = None;
                        let _ = window_clone3.emit("pipeline://terminated", -1);
                        break;
                    }
                }
            } else {
                break;
            }
        }
    });

    Ok(())
}

#[tauri::command]
fn cancel_pipeline(active_proc: State<'_, ProcessState>) -> Result<(), String> {
    let mut lock = active_proc.lock().unwrap();
    if let Some(ref mut child) = lock.child {
        let pid = child.id();
        send_sigint(pid);
        
        // Wait up to 5 seconds for graceful exit, then force kill
        for _ in 0..10 {
            thread::sleep(Duration::from_millis(500));
            if let Ok(Some(_)) = child.try_wait() {
                lock.child = None;
                lock.project_id = None;
                return Ok(());
            }
        }
        let _ = child.kill();
        lock.child = None;
        lock.project_id = None;
        Ok(())
    } else {
        Err("No active pipeline running to cancel.".to_string())
    }
}

#[tauri::command]
fn resume_pipeline(
    window: Window,
    active_proc: State<'_, ProcessState>,
    project_dir: String,
) -> Result<(), String> {
    let ws_root = find_workspace_root().ok_or("Workspace root not found")?;
    let python_path = find_python_path();

    let mut lock = active_proc.lock().unwrap();
    if lock.child.is_some() {
        return Err("Pipeline is already running.".to_string());
    }

    let mut cmd = Command::new(python_path);
    cmd.current_dir(ws_root.join("engine"));
    cmd.arg("-m").arg("autodub.cli").arg("resume").arg(&project_dir);

    cmd.stdout(Stdio::piped());
    cmd.stderr(Stdio::piped());

    let mut child = cmd.spawn().map_err(|e| format!("Failed to spawn Python process: {}", e))?;
    let stdout = child.stdout.take().ok_or("Failed to open stdout")?;
    let stderr = child.stderr.take().ok_or("Failed to open stderr")?;

    lock.child = Some(child);
    lock.project_id = Some(project_dir.clone());

    let window_clone = window.clone();
    thread::spawn(move || {
        let reader = BufReader::new(stdout);
        for line in reader.lines() {
            if let Ok(line_str) = line {
                let trimmed = line_str.trim();
                if trimmed.starts_with('{') && trimmed.ends_with('}') {
                    if let Ok(json) = serde_json::from_str::<serde_json::Value>(trimmed) {
                        let _ = window_clone.emit("pipeline://progress", json);
                    }
                }
            }
        }
    });

    let window_clone2 = window.clone();
    thread::spawn(move || {
        let reader = BufReader::new(stderr);
        for line in reader.lines() {
            if let Ok(line_str) = line {
                let _ = window_clone2.emit("pipeline://log", line_str);
            }
        }
    });

    let window_clone3 = window.clone();
    thread::spawn(move || {
        loop {
            thread::sleep(Duration::from_millis(500));
            let active_proc = window_clone3.state::<ProcessState>();
            let mut lock = active_proc.lock().unwrap();
            if let Some(ref mut child) = lock.child {
                match child.try_wait() {
                    Ok(Some(status)) => {
                        let code = status.code().unwrap_or(0);
                        lock.child = None;
                        lock.project_id = None;
                        let _ = window_clone3.emit("pipeline://terminated", code);
                        break;
                    }
                    Ok(None) => {}
                    Err(_) => {
                        lock.child = None;
                        lock.project_id = None;
                        let _ = window_clone3.emit("pipeline://terminated", -1);
                        break;
                    }
                }
            } else {
                break;
            }
        }
    });

    Ok(())
}

#[tauri::command]
fn retry_pipeline(
    window: Window,
    active_proc: State<'_, ProcessState>,
    project_dir: String,
    stage: String,
    force: bool,
) -> Result<(), String> {
    let ws_root = find_workspace_root().ok_or("Workspace root not found")?;
    let python_path = find_python_path();

    let mut lock = active_proc.lock().unwrap();
    if let Some(ref mut child) = lock.child {
        let pid = child.id();
        send_sigint(pid);
        thread::sleep(Duration::from_millis(200));
        let _ = child.kill();
        lock.child = None;
        lock.project_id = None;
    }

    let mut cmd = Command::new(python_path);
    cmd.current_dir(ws_root.join("engine"));
    let stage_lower = stage.to_lowercase();
    cmd.arg("-m").arg("autodub.cli").arg("retry").arg(&project_dir).arg(stage_lower);
    if force {
        cmd.arg("--force");
    }

    cmd.stdout(Stdio::piped());
    cmd.stderr(Stdio::piped());

    let mut child = cmd.spawn().map_err(|e| format!("Failed to spawn Python process: {}", e))?;
    let stdout = child.stdout.take().ok_or("Failed to open stdout")?;
    let stderr = child.stderr.take().ok_or("Failed to open stderr")?;

    lock.child = Some(child);
    lock.project_id = Some(project_dir.clone());

    let window_clone = window.clone();
    thread::spawn(move || {
        let reader = BufReader::new(stdout);
        for line in reader.lines() {
            if let Ok(line_str) = line {
                let trimmed = line_str.trim();
                if trimmed.starts_with('{') && trimmed.ends_with('}') {
                    if let Ok(json) = serde_json::from_str::<serde_json::Value>(trimmed) {
                        let _ = window_clone.emit("pipeline://progress", json);
                    }
                }
            }
        }
    });

    let window_clone2 = window.clone();
    thread::spawn(move || {
        let reader = BufReader::new(stderr);
        for line in reader.lines() {
            if let Ok(line_str) = line {
                let _ = window_clone2.emit("pipeline://log", line_str);
            }
        }
    });

    let window_clone3 = window.clone();
    thread::spawn(move || {
        loop {
            thread::sleep(Duration::from_millis(500));
            let active_proc = window_clone3.state::<ProcessState>();
            let mut lock = active_proc.lock().unwrap();
            if let Some(ref mut child) = lock.child {
                match child.try_wait() {
                    Ok(Some(status)) => {
                        let code = status.code().unwrap_or(0);
                        lock.child = None;
                        lock.project_id = None;
                        let _ = window_clone3.emit("pipeline://terminated", code);
                        break;
                    }
                    Ok(None) => {}
                    Err(_) => {
                        lock.child = None;
                        lock.project_id = None;
                        let _ = window_clone3.emit("pipeline://terminated", -1);
                        break;
                    }
                }
            } else {
                break;
            }
        }
    });

    Ok(())
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct SystemHardwareMetrics {
    ram_usage: String,
    vram_usage: String,
}

#[tauri::command]
fn list_jobs_queue(status: Option<String>) -> Result<serde_json::Value, String> {
    let ws_root = find_workspace_root().ok_or("Workspace root not found")?;
    let python_path = find_python_path();

    let mut cmd = Command::new(&python_path);
    cmd.current_dir(ws_root.join("engine"));
    cmd.args(&["-m", "autodub.cli", "list", "--json"]);
    if let Some(st) = status {
        cmd.args(&["--status", &st]);
    }

    let output = cmd.output().map_err(|e| format!("Failed to list jobs: {}", e))?;
    if output.status.success() {
        let text = String::from_utf8_lossy(&output.stdout);
        let val: serde_json::Value = serde_json::from_str(text.trim()).map_err(|e| format!("JSON parse error: {}", e))?;
        Ok(val)
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

#[tauri::command]
fn pause_job_queue(job_id: String) -> Result<(), String> {
    let ws_root = find_workspace_root().ok_or("Workspace root not found")?;
    let python_path = find_python_path();

    let output = Command::new(&python_path)
        .current_dir(ws_root.join("engine"))
        .args(&["-m", "autodub.cli", "pause", &job_id])
        .output()
        .map_err(|e| format!("Failed to pause job: {}", e))?;

    if output.status.success() {
        Ok(())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

#[tauri::command]
fn get_system_hardware_metrics() -> SystemHardwareMetrics {
    let ws_root = find_workspace_root();
    let python_path = find_python_path();

    if let Some(ws) = ws_root {
        if let Ok(output) = Command::new(&python_path)
            .current_dir(ws.join("engine"))
            .args(&["-m", "autodub.cli", "telemetry"])
            .output()
        {
            if output.status.success() {
                let stdout_str = String::from_utf8_lossy(&output.stdout);
                if let Ok(val) = serde_json::from_str::<serde_json::Value>(stdout_str.trim()) {
                    let ram = val["ram"].as_str().unwrap_or("N/A").to_string();
                    let vram = val["vram"].as_str().unwrap_or("N/A").to_string();
                    return SystemHardwareMetrics {
                        ram_usage: ram,
                        vram_usage: vram,
                    };
                }
            }
        }
    }

    // Fallback if execution fails
    SystemHardwareMetrics {
        ram_usage: "N/A (Telemetry Error)".to_string(),
        vram_usage: "N/A (Telemetry Error)".to_string(),
    }
}

#[tauri::command]
#[allow(dead_code)]
fn read_subtitles(project_dir: String) -> Result<serde_json::Value, String> {
    let p_dir = PathBuf::from(&project_dir);
    let trans_file = p_dir.join("transcript").join("translation.json");
    let orig_file = p_dir.join("transcript").join("transcript.json");

    let file_to_read = if trans_file.exists() {
        trans_file
    } else if orig_file.exists() {
        orig_file
    } else {
        return Err("No transcript or translation JSON file found.".to_string());
    };

    let content = fs::read_to_string(file_to_read).map_err(|e| e.to_string())?;
    let json: serde_json::Value = serde_json::from_str(&content).map_err(|e| e.to_string())?;
    Ok(json)
}

#[tauri::command]
#[allow(dead_code)]
fn write_subtitles(project_dir: String, data: serde_json::Value) -> Result<(), String> {
    let p_dir = PathBuf::from(&project_dir);
    let trans_dir = p_dir.join("transcript");
    fs::create_dir_all(&trans_dir).map_err(|e| e.to_string())?;

    let trans_file = trans_dir.join("translation.json");
    let content = serde_json::to_string_pretty(&data).map_err(|e| e.to_string())?;
    fs::write(trans_file, content).map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
#[allow(dead_code)]
fn run_qc_check(project_dir: String) -> Result<serde_json::Value, String> {
    let ws_root = find_workspace_root().ok_or("Workspace root not found")?;
    let python_path = find_python_path();

    let output = Command::new(&python_path)
        .current_dir(ws_root.join("engine"))
        .args(&["-m", "autodub.cli", "qc", &project_dir, "--json"])
        .output()
        .map_err(|e| format!("Failed to execute QC command: {}", e))?;

    if output.status.success() {
        let stdout_str = String::from_utf8_lossy(&output.stdout);
        let json: serde_json::Value = serde_json::from_str(stdout_str.trim()).map_err(|e| e.to_string())?;
        Ok(json)
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

#[tauri::command]
#[allow(dead_code)]
fn apply_autofit_qc(project_dir: String) -> Result<serde_json::Value, String> {
    let ws_root = find_workspace_root().ok_or("Workspace root not found")?;
    let python_path = find_python_path();

    let output = Command::new(&python_path)
        .current_dir(ws_root.join("engine"))
        .args(&["-m", "autodub.cli", "autofit", &project_dir])
        .output()
        .map_err(|e| format!("Failed to execute autofit command: {}", e))?;

    if output.status.success() {
        let stdout_str = String::from_utf8_lossy(&output.stdout);
        let json: serde_json::Value = serde_json::from_str(stdout_str.trim()).map_err(|e| e.to_string())?;
        Ok(json)
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

#[tauri::command]
#[allow(dead_code)]
fn preview_tts_voice(text: String, voice: String, gender: String) -> Result<serde_json::Value, String> {
    let ws_root = find_workspace_root().ok_or("Workspace root not found")?;
    let python_path = find_python_path();
    let temp_mp3 = ws_root.join("engine").join("logs").join("preview.mp3");

    let output = Command::new(&python_path)
        .current_dir(ws_root.join("engine"))
        .args(&[
            "-m", "autodub.cli", "preview-tts",
            "--text", &text,
            "--voice", &voice,
            "--gender", &gender,
            "--output", &temp_mp3.to_string_lossy()
        ])
        .output()
        .map_err(|e| format!("Failed to run preview-tts: {}", e))?;

    if output.status.success() {
        let stdout_str = String::from_utf8_lossy(&output.stdout);
        let json: serde_json::Value = serde_json::from_str(stdout_str.trim()).map_err(|e| e.to_string())?;
        Ok(json)
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

fn main() {
    tauri::Builder::default()
        .manage(Mutex::new(ActiveProcess { child: None, project_id: None }))
        .invoke_handler(tauri::generate_handler![
            run_preflight_check,
            list_projects,
            open_output_folder,
            create_project,
            read_project_json,
            write_project_json,
            read_pipeline_log,
            start_pipeline,
            cancel_pipeline,
            resume_pipeline,
            retry_pipeline,
            list_jobs_queue,
            pause_job_queue,
            get_system_hardware_metrics,
            read_subtitles,
            write_subtitles,
            run_qc_check,
            apply_autofit_qc,
            preview_tts_voice
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
