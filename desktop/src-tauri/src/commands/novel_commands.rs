use std::fs;
use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::thread;
use std::time::Duration;
use tauri::{State, Window};

use crate::{find_python_path, find_workspace_root, send_sigint, ProcessState};

pub fn append_novel_log(p_path: &Path, line: &str) {
    let log_file = p_path.join("novel_execution.log");
    if let Ok(mut f) = fs::OpenOptions::new().create(true).append(true).open(log_file) {
        let _ = writeln!(f, "{}", line);
    }
}

#[tauri::command]
pub async fn discover_story_url(window: Window, url: String, project_dir: Option<String>) -> Result<serde_json::Value, String> {
    let ws_root = find_workspace_root().ok_or("Workspace root not found")?;
    let python_path = find_python_path();

    let mut cmd = Command::new(&python_path);
    cmd.current_dir(ws_root.join("engine"));
    cmd.args(&["-m", "autodub.cli", "discover-story", "--url", &url]);
    if let Some(ref p) = project_dir {
        cmd.args(&["--project-dir", p]);
    }

    cmd.stdout(Stdio::piped());
    cmd.stderr(Stdio::piped());

    let mut child = cmd.spawn().map_err(|e| format!("Failed to spawn Python process: {}", e))?;
    let stdout = child.stdout.take().ok_or("Failed to open stdout")?;
    let stderr = child.stderr.take().ok_or("Failed to open stderr")?;

    let final_result = std::sync::Arc::new(std::sync::Mutex::new(None));
    let result_clone = final_result.clone();
    let window_clone = window.clone();

    thread::spawn(move || {
        let reader = BufReader::new(stdout);
        for line in reader.lines() {
            if let Ok(line_str) = line {
                let trimmed = line_str.trim();
                if trimmed.starts_with('{') && trimmed.ends_with('}') {
                    if let Ok(json) = serde_json::from_str::<serde_json::Value>(trimmed) {
                        if json.get("event").and_then(|v| v.as_str()) == Some("discovery_complete") {
                            if let Some(res_val) = json.get("result") {
                                let mut lock = result_clone.lock().unwrap();
                                *lock = Some(res_val.clone());
                            }
                        }
                        let _ = window_clone.emit("discovery://progress", json);
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

    let status = child.wait().map_err(|e| e.to_string())?;
    if status.success() {
        let lock = final_result.lock().unwrap();
        if let Some(ref res) = *lock {
            Ok(res.clone())
        } else {
            Ok(serde_json::json!({ "status": "SUCCESS" }))
        }
    } else {
        Err("Story discovery failed".to_string())
    }
}

#[tauri::command]
pub async fn start_story_import(window: Window, project_dir: String, chapters_json: String) -> Result<serde_json::Value, String> {
    let ws_root = find_workspace_root().ok_or("Workspace root not found")?;
    let python_path = find_python_path();

    let mut cmd = Command::new(&python_path);
    cmd.current_dir(ws_root.join("engine"));
    cmd.args(&["-m", "autodub.cli", "import-story-chapters", "--project-dir", &project_dir, "--chapters-json", &chapters_json]);

    cmd.stdout(Stdio::piped());
    cmd.stderr(Stdio::piped());

    let mut child = cmd.spawn().map_err(|e| format!("Failed to spawn Python process: {}", e))?;
    let stdout = child.stdout.take().ok_or("Failed to open stdout")?;
    let stderr = child.stderr.take().ok_or("Failed to open stderr")?;

    let window_clone = window.clone();
    thread::spawn(move || {
        let reader = BufReader::new(stdout);
        for line in reader.lines() {
            if let Ok(line_str) = line {
                let trimmed = line_str.trim();
                if trimmed.starts_with('{') && trimmed.ends_with('}') {
                    if let Ok(json) = serde_json::from_str::<serde_json::Value>(trimmed) {
                        let _ = window_clone.emit("chapter://import_progress", json);
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

    let status = child.wait().map_err(|e| e.to_string())?;
    if status.success() {
        Ok(serde_json::json!({ "status": "SUCCESS" }))
    } else {
        Err("Story import failed".to_string())
    }
}

#[tauri::command]
pub async fn initialize_novel(window: Window, project_dir: String, idea: serde_json::Value) -> Result<serde_json::Value, String> {
    let ws_root = find_workspace_root().ok_or("Workspace root not found")?;
    let python_path = find_python_path();
    let p_path = PathBuf::from(&project_dir);

    let title_str = idea.get("title").and_then(|v| v.as_str()).unwrap_or("Hành Trình Mới").to_string();
    let genre_str = idea.get("genre").and_then(|v| v.as_str()).unwrap_or("Hành động viễn tưởng").to_string();
    let style_str = idea.get("style").and_then(|v| v.as_str()).unwrap_or("Dễ đọc, tiết tấu nhanh").to_string();
    let chapters_str = idea.get("total_chapters").and_then(|v| v.as_i64()).unwrap_or(1000).to_string();

    let p_name = idea.get("protagonist").and_then(|p| p.get("name")).and_then(|v| v.as_str()).unwrap_or("Nhân vật chính").to_string();
    let p_bg = idea.get("protagonist").and_then(|p| p.get("background")).and_then(|v| v.as_str()).unwrap_or("Bối cảnh ban đầu").to_string();

    let mut cmd = Command::new(&python_path);
    cmd.current_dir(ws_root.join("engine"))
        .args(&[
            "-m", "autodub.cli", "novel", "init",
            "--project", &p_path.to_string_lossy(),
            "--title", &title_str,
            "--genre", &genre_str,
            "--style", &style_str,
            "--protagonist-name", &p_name,
            "--protagonist-bg", &p_bg,
            "--chapters", &chapters_str,
        ])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());

    let mut child = cmd.spawn().map_err(|e| format!("Failed to spawn novel init: {}", e))?;
    let stdout = child.stdout.take().ok_or("Failed to open stdout")?;
    let stderr = child.stderr.take().ok_or("Failed to open stderr")?;

    let win1 = window.clone();
    let p_path1 = p_path.clone();
    let t1 = thread::spawn(move || {
        let reader = BufReader::new(stdout);
        for line in reader.lines() {
            if let Ok(line_str) = line {
                let _ = win1.emit("pipeline://log", &line_str);
                append_novel_log(&p_path1, &line_str);
            }
        }
    });

    let win2 = window.clone();
    let p_path2 = p_path.clone();
    let t2 = thread::spawn(move || {
        let reader = BufReader::new(stderr);
        for line in reader.lines() {
            if let Ok(line_str) = line {
                let _ = win2.emit("pipeline://log", &line_str);
                append_novel_log(&p_path2, &line_str);
            }
        }
    });

    let status = child.wait().map_err(|e| format!("Wait failed: {}", e))?;
    let _ = t1.join();
    let _ = t2.join();

    if status.success() {
        let bible_path = p_path.join("story_bible.json");
        if bible_path.exists() {
            if let Ok(content) = fs::read_to_string(&bible_path) {
                if let Ok(val) = serde_json::from_str::<serde_json::Value>(&content) {
                    return Ok(val);
                }
            }
        }
        Ok(serde_json::json!({ "status": "SUCCESS" }))
    } else {
        let log_file = p_path.join("novel_execution.log");
        let detail = if log_file.exists() {
            fs::read_to_string(&log_file).ok().and_then(|content| {
                content.lines().rev().find(|line| {
                    line.contains("[ERROR]") || line.contains("GenerationError") || line.contains("failed") || line.contains("FAIL")
                }).map(|l| l.to_string())
            })
        } else {
            None
        };
        Err(detail.unwrap_or_else(|| "Failed to initialize novel story bible".to_string()))
    }
}

#[tauri::command]
pub async fn generate_novel_master_plan(window: Window, project_dir: String) -> Result<serde_json::Value, String> {
    let ws_root = find_workspace_root().ok_or("Workspace root not found")?;
    let python_path = find_python_path();
    let p_path = PathBuf::from(&project_dir);

    let mut cmd = Command::new(&python_path);
    cmd.current_dir(ws_root.join("engine"))
        .args(&[
            "-m", "autodub.cli", "novel", "plan",
            "--project", &p_path.to_string_lossy(),
        ])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());

    let mut child = cmd.spawn().map_err(|e| format!("Failed to spawn novel plan: {}", e))?;
    let stdout = child.stdout.take().ok_or("Failed to open stdout")?;
    let stderr = child.stderr.take().ok_or("Failed to open stderr")?;

    let win1 = window.clone();
    let p_path1 = p_path.clone();
    let t1 = thread::spawn(move || {
        let reader = BufReader::new(stdout);
        for line in reader.lines() {
            if let Ok(line_str) = line {
                let _ = win1.emit("pipeline://log", &line_str);
                append_novel_log(&p_path1, &line_str);
            }
        }
    });

    let win2 = window.clone();
    let p_path2 = p_path.clone();
    let t2 = thread::spawn(move || {
        let reader = BufReader::new(stderr);
        for line in reader.lines() {
            if let Ok(line_str) = line {
                let _ = win2.emit("pipeline://log", &line_str);
                append_novel_log(&p_path2, &line_str);
            }
        }
    });

    let status = child.wait().map_err(|e| format!("Wait failed: {}", e))?;
    let _ = t1.join();
    let _ = t2.join();

    if status.success() {
        let p_json = p_path.join("project.json");
        if p_json.exists() {
            if let Ok(content) = fs::read_to_string(&p_json) {
                if let Ok(val) = serde_json::from_str::<serde_json::Value>(&content) {
                    if let Some(arcs) = val.get("arc_plans") {
                        return Ok(arcs.clone());
                    }
                }
            }
        }
        Err("Master plan generation output not found in project.json".to_string())
    } else {
        Err("Failed to generate novel master plan. LLM generation failed or was stopped.".to_string())
    }
}

#[tauri::command]
pub fn start_novel_auto_write(
    window: Window,
    active_proc: State<'_, ProcessState>,
    project_dir: String,
    start_chapter: i64,
    end_chapter: i64,
) -> Result<(), String> {
    let ws_root = find_workspace_root().ok_or("Workspace root not found")?;
    let python_path = find_python_path();
    let p_path = PathBuf::from(&project_dir);

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
    cmd.args(&[
        "-m", "autodub.cli", "novel", "write",
        "--project", &p_path.to_string_lossy(),
        "--start", &start_chapter.to_string(),
        "--end", &end_chapter.to_string(),
    ]);

    cmd.stdout(Stdio::piped());
    cmd.stderr(Stdio::piped());

    let mut child = cmd.spawn().map_err(|e| format!("Failed to spawn Novel Engine process: {}", e))?;
    let stdout = child.stdout.take().ok_or("Failed to open stdout")?;
    let stderr = child.stderr.take().ok_or("Failed to open stderr")?;

    lock.child = Some(child);
    lock.project_id = Some(project_dir.clone());

    let window_clone = window.clone();
    let p_path_w1 = p_path.clone();
    thread::spawn(move || {
        let reader = BufReader::new(stdout);
        for line in reader.lines() {
            if let Ok(line_str) = line {
                let trimmed = line_str.trim();
                if !trimmed.is_empty() {
                    let _ = window_clone.emit("pipeline://log", trimmed);
                    append_novel_log(&p_path_w1, trimmed);
                }
                if trimmed.starts_with('{') && trimmed.ends_with('}') {
                    if let Ok(json) = serde_json::from_str::<serde_json::Value>(trimmed) {
                        let _ = window_clone.emit("novel://progress", json);
                    }
                }
            }
        }
    });

    let window_clone2 = window.clone();
    let p_path_w2 = p_path.clone();
    thread::spawn(move || {
        let reader = BufReader::new(stderr);
        for line in reader.lines() {
            if let Ok(line_str) = line {
                let _ = window_clone2.emit("pipeline://log", &line_str);
                append_novel_log(&p_path_w2, &line_str);
            }
        }
    });

    Ok(())
}

#[tauri::command]
pub fn stop_novel_auto_write(
    active_proc: State<'_, ProcessState>,
) -> Result<(), String> {
    let mut lock = active_proc.lock().unwrap();
    if let Some(ref mut child) = lock.child {
        let pid = child.id();
        send_sigint(pid);
        thread::sleep(Duration::from_millis(150));
        let _ = child.kill();
        lock.child = None;
        lock.project_id = None;
    }
    Ok(())
}

#[tauri::command]
pub fn is_novel_writing_active(
    active_proc: State<'_, ProcessState>,
) -> bool {
    let mut lock = active_proc.lock().unwrap();
    if let Some(ref mut child) = lock.child {
        match child.try_wait() {
            Ok(Some(_)) => {
                lock.child = None;
                lock.project_id = None;
                false
            }
            Ok(None) => true,
            Err(_) => {
                lock.child = None;
                lock.project_id = None;
                false
            }
        }
    } else {
        false
    }
}

#[tauri::command]
pub async fn get_novel_canon_facts(project_dir: String, _limit: Option<i64>) -> Result<serde_json::Value, String> {
    let ws_root = find_workspace_root().ok_or("Workspace root not found")?;
    let python_path = find_python_path();
    let p_path = PathBuf::from(&project_dir);

    let mut cmd = Command::new(&python_path);
    cmd.current_dir(ws_root.join("engine"))
        .args(&[
            "-m", "autodub.cli", "novel", "status",
            "--project", &p_path.to_string_lossy(),
        ])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());

    if let Ok(output) = cmd.output() {
        if output.status.success() {
            let stdout_str = String::from_utf8_lossy(&output.stdout);
            if let Ok(val) = serde_json::from_str::<serde_json::Value>(&stdout_str) {
                if let Some(facts) = val.get("canonFacts") {
                    return Ok(facts.clone());
                }
            }
        }
    }

    let p_json = p_path.join("project.json");
    if p_json.exists() {
        if let Ok(content) = fs::read_to_string(&p_json) {
            if let Ok(val) = serde_json::from_str::<serde_json::Value>(&content) {
                if let Some(facts) = val.get("canon_facts") {
                    return Ok(facts.clone());
                }
            }
        }
    }

    Ok(serde_json::json!([]))
}

#[tauri::command]
pub async fn get_novel_plot_threads(project_dir: String) -> Result<serde_json::Value, String> {
    let ws_root = find_workspace_root().ok_or("Workspace root not found")?;
    let python_path = find_python_path();
    let p_path = PathBuf::from(&project_dir);

    let mut cmd = Command::new(&python_path);
    cmd.current_dir(ws_root.join("engine"))
        .args(&[
            "-m", "autodub.cli", "novel", "status",
            "--project", &p_path.to_string_lossy(),
        ])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());

    if let Ok(output) = cmd.output() {
        if output.status.success() {
            let stdout_str = String::from_utf8_lossy(&output.stdout);
            if let Ok(val) = serde_json::from_str::<serde_json::Value>(&stdout_str) {
                if let Some(threads) = val.get("openThreads") {
                    return Ok(threads.clone());
                }
            }
        }
    }

    let p_json = p_path.join("project.json");
    if p_json.exists() {
        if let Ok(content) = fs::read_to_string(&p_json) {
            if let Ok(val) = serde_json::from_str::<serde_json::Value>(&content) {
                if let Some(threads) = val.get("open_threads") {
                    return Ok(threads.clone());
                }
            }
        }
    }

    Ok(serde_json::json!([]))
}
