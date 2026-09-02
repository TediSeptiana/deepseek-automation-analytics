"""Service untuk mencatat log dan menyimpan dataset mentah analisis."""

from __future__ import annotations

import json
from typing import Any
from app.config import settings
from app.models import RawInteractionData


class ExporterService:
    """Async/Sync Compatible Exporter Service."""

    @staticmethod
    def export(prompt: str, response: str, session_id: str, seq_idx: int) -> None:
        """Menyimpan data interaksi ke file Log dan Raw Dataset."""
        settings.ensure_directories()

        raw_entry = RawInteractionData(
            session_id=session_id,
            sequence_index=seq_idx,
            prompt=prompt,
            raw_response=response,
            prompt_length=len(prompt),
            response_length=len(response),
        )

        ExporterService._append_raw_dataset(raw_entry)
        ExporterService._append_txt_log(prompt, response, raw_entry.created_at_utc)
        ExporterService._append_json_log(prompt, response, raw_entry.created_at_utc)

    @staticmethod
    def _append_raw_dataset(entry: RawInteractionData) -> None:
        records: list[dict[str, Any]] = []
        if (
            settings.raw_data_file.exists()
            and settings.raw_data_file.stat().st_size > 0
        ):
            try:
                with settings.raw_data_file.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        records = data
            except json.JSONDecodeError:
                pass

        records.append(entry.model_dump())
        with settings.raw_data_file.open("w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

    @staticmethod
    def _append_json_log(prompt: str, response: str, timestamp: str) -> None:
        logs: list[dict[str, str]] = []
        if (
            settings.log_json_file.exists()
            and settings.log_json_file.stat().st_size > 0
        ):
            try:
                with settings.log_json_file.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        logs = data
            except json.JSONDecodeError:
                pass

        logs.append(
            {"timestamp": timestamp, "prompt": prompt, "response": response}
        )
        with settings.log_json_file.open("w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)

    @staticmethod
    def _append_txt_log(prompt: str, response: str, timestamp: str) -> None:
        formatted_entry = (
            f"{'=' * 60}\n"
            f"TIMESTAMP : {timestamp}\n"
            f"PROMPT    : {prompt}\n"
            f"RESPONSE  :\n{response}\n"
            f"{'=' * 60}\n\n"
        )
        with settings.log_txt_file.open("a", encoding="utf-8") as f:
            f.write(formatted_entry)