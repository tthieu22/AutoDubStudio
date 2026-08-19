import logging
from pathlib import Path
from typing import Optional
import datetime

def setup_logger(log_file: Optional[Path] = None) -> logging.Logger:
    if log_file is None:
        log_file = Path.cwd() / "logs" / "pipeline.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("autodub")
    logger.setLevel(logging.INFO)
    
    # File Handler
    fh = logging.FileHandler(log_file, encoding="utf-8")
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s %(message)s", datefmt="%H:%M:%S")
    fh.setFormatter(formatter)
    
    if not logger.handlers:
        logger.addHandler(fh)
        
    return logger
