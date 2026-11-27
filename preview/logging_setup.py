"""Logging configuration for Preview macOS."""

from __future__ import annotations

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional, Union


def get_log_dir() -> Path:
    """Return the platform-appropriate user log directory for Preview."""
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "previewmacos" / "Logs"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Logs" / "previewmacos"
    base = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return base / "previewmacos" / "logs"


def setup_logging(
    log_dir: Optional[Union[str, Path]] = None,
    level: int = logging.INFO,
) -> Path:
    """Configure a rotating file logger and install sys.excepthook."""
    target_dir = Path(log_dir) if log_dir is not None else get_log_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    log_file = target_dir / "preview.log"

    root_logger = logging.getLogger()
    root_logger.setLevel(min(root_logger.level, level) if root_logger.level else level)

    for existing in list(root_logger.handlers):
        if getattr(existing, "_preview_rotating_handler", False):
            root_logger.removeHandler(existing)
            existing.close()

    handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    setattr(handler, "_preview_rotating_handler", True)
    root_logger.addHandler(handler)

    def _excepthook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        logging.getLogger("preview.unhandled").critical(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_tb),
        )
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = _excepthook
    return log_file
