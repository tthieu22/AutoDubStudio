use std::fs;
use std::path::Path;
use std::process::{Command, Stdio};
use std::thread;
use std::time::Duration;
use serde::{Deserialize, Serialize};

use crate::{find_python_path, find_workspace_root};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct SystemHardwareMetrics {
    pub ram_usage: String,
    pub vram_usage: String,
}

#[tauri::command]
pub fn get_system_hardware_metrics() -> SystemHardwareMetrics {
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

    SystemHardwareMetrics {
        ram_usage: "N/A (Telemetry Error)".to_string(),
        vram_usage: "N/A (Telemetry Error)".to_string(),
    }
}

#[tauri::command]
pub fn list_local_llm_models() -> Result<Vec<String>, String> {
    let ws_root = find_workspace_root().ok_or("Workspace root not found")?;
    let llm_dir = ws_root.join("models").join("llm");
    if !llm_dir.exists() {
        return Ok(vec![]);
    }
    let mut models = Vec::new();
    if let Ok(entries) = fs::read_dir(&llm_dir) {
        for entry in entries.flatten() {
            let path = entry.path();
            let name = entry.file_name().to_string_lossy().to_string();
            if name.starts_with('.') {
                continue;
            }
            if path.is_file() || path.is_dir() {
                models.push(name);
            }
        }
    }
    models.sort();
    Ok(models)
}

#[tauri::command]
pub async fn ensure_local_llm_server() -> Result<serde_json::Value, String> {
    use std::net::TcpStream;
    let ports = [11434, 8080, 1234];
    for port in ports {
        if let Ok(addr) = format!("127.0.0.1:{}", port).parse() {
            if TcpStream::connect_timeout(&addr, Duration::from_millis(300)).is_ok() {
                let server_type = if port == 11434 { "Ollama GPU CUDA" } else { "llama.cpp" };
                return Ok(serde_json::json!({
                    "active": true,
                    "port": port,
                    "url": format!("http://localhost:{}", port),
                    "server": server_type,
                    "model": "qwen2.5:3b"
                }));
            }
        }
    }

    let ollama_path = r"C:\Users\hieut\AppData\Local\Programs\Ollama\ollama.exe";
    let bin = if Path::new(ollama_path).exists() {
        ollama_path.to_string()
    } else {
        "ollama".to_string()
    };

    let _ = Command::new(&bin)
        .arg("serve")
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn();

    thread::sleep(Duration::from_millis(1500));

    Ok(serde_json::json!({
        "active": true,
        "port": 11434,
        "url": "http://localhost:11434",
        "server": "Ollama GPU CUDA (Auto-Launched)",
        "model": "qwen2.5:3b"
    }))
}

pub fn spawn_ollama_gpu_server_on_startup() {
    use std::net::TcpStream;
    let ports = [11434, 8080];
    let mut active = false;
    for port in ports {
        if let Ok(addr) = format!("127.0.0.1:{}", port).parse() {
            if TcpStream::connect_timeout(&addr, Duration::from_millis(300)).is_ok() {
                println!("[HARDWARE] Local LLM Server port {} is active.", port);
                active = true;
                break;
            }
        }
    }

    let ollama_path = r"C:\Users\hieut\AppData\Local\Programs\Ollama\ollama.exe";
    let bin = if Path::new(ollama_path).exists() {
        ollama_path.to_string()
    } else {
        "ollama".to_string()
    };

    if !active {
        println!("[HARDWARE] Auto-spawning Ollama GPU CUDA server on app startup ({})", bin);
        let _ = Command::new(&bin)
            .arg("serve")
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn();
        thread::sleep(Duration::from_millis(1000));
    }

    let bin_clone = bin.clone();
    thread::spawn(move || {
        println!("[HARDWARE] Pre-loading Qwen2.5-3B model into NVIDIA GTX 1650 Ti GPU VRAM...");
        let _ = Command::new(&bin_clone)
            .args(&["run", "qwen2.5:3b", "Sẵn sàng sáng tạo"])
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn();
    });
}
