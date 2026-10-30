"""JSON-lines logging, so harness runs can be searched and fed into evals."""

from __future__ import annotations

import json
import logging
import sys

_STANDARD = set(logging.makeLogRecord({}).__dict__) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    """One JSON object per line. Fields passed with `extra={...}` become top-level keys."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        entry.update({k: v for k, v in record.__dict__.items() if k not in _STANDARD})
        return json.dumps(entry, default=str)


def setup_logging(level: int = logging.INFO) -> None:
    """Send all logs to stderr as JSON lines. Stdout stays free for CLI output."""
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=level, handlers=[handler], force=True)
