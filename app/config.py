"""Settings from environment variables (see .env.example)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY")
    model: str = os.getenv("HARNESS_MODEL", "claude-sonnet-5-5")
    judge_model: str = os.getenv("HARNESS_JUDGE_MODEL", "claude-haiku-5-5")
    max_revisions: int = int(os.getenv("HARNESS_MAX_REVISIONS", "2"))
    use_judge: bool = os.getenv("HARNESS_USE_JUDGE", "true").lower() == "true"

    canvas_base_url: str | None = os.getenv("CANVAS_BASE_URL")  # e.g. https://<school>.instructure.com
    canvas_token: str | None = os.getenv("CANVAS_TOKEN")

    data_dir: Path = Path(os.getenv("HARNESS_DATA_DIR", "data"))

    @property
    def db_path(self) -> Path:
        return self.data_dir / "harness.db"

    @property
    def files_dir(self) -> Path:
        return self.data_dir / "files"


settings = Settings()
