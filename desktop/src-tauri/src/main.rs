// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;

use std::env;
use std::path::PathBuf;
use std::process::Command;
use std::sync::Mutex;
use serde::{Deserialize, Serialize};
use tauri::Manager;

use commands::dub_commands::*;
use commands::novel_commands::*;
use commands::system_commands::*;

// Structure to track the active running process
pub struct ActiveProcess {
    pub child: Option<std::process::Child>,
    pub project_id: Option<String>,
}

pub type ProcessState = Mutex<ActiveProcess>;

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct PreflightCheckResult {
    pub ffmpeg: bool,
    pub ffprobe: bool,
    pub python: bool,
    pub source_video: bool,
    pub disk_space: bool,
    pub message: String,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ProjectConfig {
    pub version: i32,
    pub project_id: String,
    pub name: String,
    pub created_at: String,
    pub updated_at: String,
    pub source: SourceConfig,
    pub target: TargetConfig,
    pub settings: SettingsConfig,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct SourceConfig {
    pub path: String,
    pub language: String,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct TargetConfig {
    pub language: String,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct SettingsConfig {
    pub whisper_model: String,
    pub whisper_compute_type: String,
    pub translation_model: String,
    pub tts_engine: String,
    pub chunk_duration: i32,
    #[serde(default = "default_translation_style")]
    pub translation_style: String,
    #[serde(default)]
    pub custom_translation_style: Option<String>,
}

fn default_translation_style() -> String {
    "general".to_string()
}

// Find workspace root by traversing upwards looking for the engine directory
pub fn find_workspace_root() -> Option<PathBuf> {
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
pub fn find_python_path() -> PathBuf {
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
pub fn send_sigint(pid: u32) {
    let mut cmd = Command::new("taskkill");
    cmd.arg("/F").arg("/T").arg("/PID").arg(pid.to_string());
    let _ = cmd.status();
}

#[cfg(not(target_os = "windows"))]
pub fn send_sigint(pid: u32) {
    unsafe {
        libc::kill(pid as libc::pid_t, libc::SIGINT);
    }
}

fn main() {
    spawn_ollama_gpu_server_on_startup();

    let app = tauri::Builder::default()
        .manage(Mutex::new(ActiveProcess { child: None, project_id: None }))
        .invoke_handler(tauri::generate_handler![
            run_preflight_check,
            list_projects,
            open_output_folder,
            create_project,
            delete_project,
            read_project_json,
            write_project_json,
            read_pipeline_log,
            read_text_file,
            write_text_file,
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
            preview_tts_voice,
            read_composition,
            write_composition,
            discover_story_url,
            start_story_import,
            list_local_llm_models,
            ensure_local_llm_server,
            initialize_novel,
            generate_novel_master_plan,
            regenerate_novel_characters,
            regenerate_novel_world,
            regenerate_novel_rules,
            start_novel_auto_write,
            stop_novel_auto_write,
            is_novel_writing_active,
            get_novel_canon_facts,
            get_novel_plot_threads
        ])
        .build(tauri::generate_context!())
        .expect("error while building tauri application");

    app.run(|app_handle, event| match event {
        tauri::RunEvent::Exit | tauri::RunEvent::ExitRequested { .. } => {
            let active_proc = app_handle.state::<Mutex<ActiveProcess>>();
            if let Ok(mut lock) = active_proc.lock() {
                if let Some(ref mut child) = lock.child {
                    let pid = child.id();
                    send_sigint(pid);
                    let _ = child.kill();
                    lock.child = None;
                    lock.project_id = None;
                }
            };
            #[cfg(target_os = "windows")]
            {
                use std::os::windows::process::CommandExt;
                const CREATE_NO_WINDOW: u32 = 0x08000000;

                let targets = [
                    "llama-server.exe",
                    "llama-cli.exe",
                    "llama.exe",
                    "ollama.exe",
                    "ollama_llama_server.exe",
                    "ollama_app.exe",
                ];

                for target in targets {
                    let _ = Command::new("taskkill")
                        .args(&["/F", "/IM", target, "/T"])
                        .creation_flags(CREATE_NO_WINDOW)
                        .status();
                }
            }
        }
        _ => {}
    });
}
