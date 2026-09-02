"""Aplikasi Konfigurasi menggunakan Pydantic Settings."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent
DATA_DIR: Final[Path] = BASE_DIR / "data"


class Settings(BaseModel):
    """Konfigurasi global aplikasi."""

    # Credentials
    email: str = Field(default_factory=lambda: os.getenv("DEEPSEEK_EMAIL", ""))
    password: str = Field(default_factory=lambda: os.getenv("DEEPSEEK_PASSWORD", ""))

    # Paths
    session_file: Path = DATA_DIR / "state" / "deepseek_state.json"
    log_txt_file: Path = DATA_DIR / "log" / "chat_logs.txt"
    log_json_file: Path = DATA_DIR / "json" / "chat_logs.json"
    raw_data_file: Path = DATA_DIR / "raw" / "raw_dataset.json"

    # Playwright Options
    headless: bool = Field(
        default_factory=lambda: os.getenv("HEADLESS", "false").lower() == "true"
    )
    captcha_timeout_sec: int = Field(default=120)

    def ensure_directories(self) -> None:
        """Memastikan semua direktori penyimpan data telah siap."""
        for path in (
            self.session_file,
            self.log_txt_file,
            self.log_json_file,
            self.raw_data_file,
        ):
            path.parent.mkdir(parents=True, exist_ok=True)


settings = Settings()