"""Local diagnostics only; never upload or record raw CSV or process lists."""
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG = logging.getLogger("pc_monitor")
LOG.addHandler(logging.NullHandler())


def configure_logging():
    """Start a bounded per-user log; monitoring still works if storage fails."""
    if any(isinstance(handler, RotatingFileHandler) for handler in LOG.handlers):
        return
    base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / ".local" / "state")
    try:
        folder = base / "PC Monitor" / "logs"
        folder.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(folder / "diagnostics.log", maxBytes=512 * 1024,
                                      backupCount=2, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        LOG.addHandler(handler)
        LOG.setLevel(logging.INFO)
    except OSError:
        pass
