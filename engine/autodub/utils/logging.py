import logging
from pathlib import Path
from typing import Optional, Dict

def setup_logger(log_file: Optional[Path] = None) -> logging.Logger:
    if log_file is None:
        log_file = Path.cwd() / "logs" / "pipeline.log"
    log_file = Path(log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logger_name = f"autodub_{log_file.resolve()}"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    
    # File Handler
    fh = logging.FileHandler(log_file, encoding="utf-8")
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    fh.setFormatter(formatter)
    
    if not logger.handlers:
        logger.addHandler(fh)
        
    return logger

class StructuredFormatter(logging.Formatter):
    def __init__(self):
        super().__init__("[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

class ProjectLogger:
    LOG_CATEGORIES = ["pipeline", "llm", "image", "tts", "ffmpeg", "error"]

    def __init__(self, project_dir: Path, project_id: Optional[str] = None):
        self.project_dir = Path(project_dir)
        self.logs_dir = self.project_dir / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.project_id = project_id or self.project_dir.name
        self.loggers: Dict[str, logging.Logger] = {}
        self._init_loggers()

    def _init_loggers(self):
        formatter = StructuredFormatter()
        for cat in self.LOG_CATEGORIES:
            log_file = self.logs_dir / f"{cat}.log"
            logger_name = f"autodub_{self.project_id}_{cat}"
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.DEBUG)

            if not logger.handlers:
                fh = logging.FileHandler(log_file, encoding="utf-8")
                fh.setFormatter(formatter)
                if cat == "error":
                    fh.setLevel(logging.WARNING)
                else:
                    fh.setLevel(logging.DEBUG)
                logger.addHandler(fh)
            self.loggers[cat] = logger

    def format_meta_message(self, message: str, scene_id: Optional[str] = None, task_id: Optional[str] = None, duration: Optional[float] = None) -> str:
        parts = [f"[{self.project_id}]"]
        if scene_id:
            parts.append(f"[{scene_id}]")
        if task_id:
            parts.append(f"[{task_id}]")
        parts.append(message)
        if duration is not None:
            parts.append(f"(duration={duration:.2f}s)")
        return " ".join(parts)

    def log(self, category: str, level: int, message: str, scene_id: Optional[str] = None, task_id: Optional[str] = None, duration: Optional[float] = None):
        cat = category.lower() if category.lower() in self.LOG_CATEGORIES else "pipeline"
        formatted_msg = self.format_meta_message(message, scene_id=scene_id, task_id=task_id, duration=duration)
        
        target_logger = self.loggers.get(cat, self.loggers["pipeline"])
        target_logger.log(level, formatted_msg)

        # Mirror warnings and errors to error.log
        if level >= logging.WARNING and cat != "error":
            error_logger = self.loggers["error"]
            error_logger.log(level, f"[{cat.upper()}] {formatted_msg}")

    def info(self, category: str, message: str, scene_id: Optional[str] = None, task_id: Optional[str] = None, duration: Optional[float] = None):
        self.log(category, logging.INFO, message, scene_id=scene_id, task_id=task_id, duration=duration)

    def warning(self, category: str, message: str, scene_id: Optional[str] = None, task_id: Optional[str] = None, duration: Optional[float] = None):
        self.log(category, logging.WARNING, message, scene_id=scene_id, task_id=task_id, duration=duration)

    def error(self, category: str, message: str, scene_id: Optional[str] = None, task_id: Optional[str] = None, duration: Optional[float] = None):
        self.log(category, logging.ERROR, message, scene_id=scene_id, task_id=task_id, duration=duration)

    def debug(self, category: str, message: str, scene_id: Optional[str] = None, task_id: Optional[str] = None, duration: Optional[float] = None):
        self.log(category, logging.DEBUG, message, scene_id=scene_id, task_id=task_id, duration=duration)

