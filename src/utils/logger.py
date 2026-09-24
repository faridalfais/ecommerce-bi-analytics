import logging
import sys
from pathlib import Path

# Resolve log directory relative to repository root (2 levels up from src/utils/)
# This ensures logging works regardless of the current working directory,
# including when launched from dashboard/ or by Streamlit Cloud.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_LOG_DIR = _REPO_ROOT / "logs"


def get_logger(name: str = "bi_analytics") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Console Handler — always available
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File Handler — optional; silently skipped on read-only environments
        # (e.g. Streamlit Cloud ephemeral filesystem edge cases)
        try:
            _LOG_DIR.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(_LOG_DIR / "pipeline.log", encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except OSError:
            pass  # Console-only logging when file system is unavailable

    return logger
