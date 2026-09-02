"""Otomatisasi DeepSeek Chat menggunakan Playwright (Sync API).

Mendukung manajemen sesi (cookies), penanganan CAPTCHA manual, logging operasional,
serta ekstraksi data mentah (Raw Data Exporter) untuk kebutuhan analisis data.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final

from dotenv import load_dotenv
from playwright.sync_api import (
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)
from pydantic import BaseModel, Field

# --- Load Environment Variables ---
load_dotenv()

# --- Pengaturan Direktori & Path File ---
BASE_DIR: Final[Path] = Path(__file__).parent
DATA_DIR: Final[Path] = BASE_DIR / "data"

SESSION_FILE: Final[Path] = DATA_DIR / "state" / "deepseek_state.json"
LOG_TXT_FILE: Final[Path] = DATA_DIR / "log" / "chat_logs.txt"
LOG_JSON_FILE: Final[Path] = DATA_DIR / "json" / "chat_logs.json"
RAW_DATA_FILE: Final[Path] = DATA_DIR / "raw" / "raw_dataset.json"


def ensure_directories_exist() -> None:
    """Memastikan semua direktori penyimpan data sudah dibuat."""
    for file_path in (SESSION_FILE, LOG_TXT_FILE, LOG_JSON_FILE, RAW_DATA_FILE):
        file_path.parent.mkdir(parents=True, exist_ok=True)


class Credentials(BaseModel):
    """Model data kredensial akun dari environment variable."""

    email: str = Field(default_factory=lambda: os.getenv("DEEPSEEK_EMAIL", ""))
    password: str = Field(default_factory=lambda: os.getenv("DEEPSEEK_PASSWORD", ""))


class RawInteractionData(BaseModel):
    """Model data mentah untuk kebutuhan analisis (Analytical Dataset)."""

    session_id: str
    sequence_index: int
    prompt: str
    raw_response: str
    prompt_length: int
    response_length: int
    created_at_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class LoggerService:
    """Service untuk menangani logging operasional dan penyimpanan data mentah."""

    @staticmethod
    def log_and_export(
        prompt: str,
        response: str,
        session_id: str,
        seq_idx: int,
    ) -> None:
        """Menyimpan log operasional dan merekam data mentah ke file JSON khusus analisis."""
        ensure_directories_exist()

        # Build raw dataset model
        raw_entry = RawInteractionData(
            session_id=session_id,
            sequence_index=seq_idx,
            prompt=prompt,
            raw_response=response,
            prompt_length=len(prompt),
            response_length=len(response),
        )

        LoggerService._append_to_raw_dataset(raw_entry)
        LoggerService._append_to_txt_log(prompt, response, raw_entry.created_at_utc)
        LoggerService._append_to_json_log(prompt, response, raw_entry.created_at_utc)

    @staticmethod
    def _append_to_raw_dataset(entry: RawInteractionData) -> None:
        """Menyimpan data mentah ke `data/raw/raw_dataset.json`."""
        records: list[dict[str, Any]] = []

        if RAW_DATA_FILE.exists() and RAW_DATA_FILE.stat().st_size > 0:
            try:
                with RAW_DATA_FILE.open("r", encoding="utf-8") as file:
                    data = json.load(file)
                    if isinstance(data, list):
                        records = data
            except json.JSONDecodeError:
                print(f"[WARNING] Gagal membaca {RAW_DATA_FILE}. Membuat array baru...")

        records.append(entry.model_dump())

        with RAW_DATA_FILE.open("w", encoding="utf-8") as file:
            json.dump(records, file, indent=2, ensure_ascii=False)
        print(f"[RAW DATA] Exported raw dataset -> {RAW_DATA_FILE}")

    @staticmethod
    def _append_to_json_log(prompt: str, response: str, timestamp: str) -> None:
        """Menambahkan entri log operasional ke `data/json/chat_logs.json`."""
        logs: list[dict[str, str]] = []

        if LOG_JSON_FILE.exists() and LOG_JSON_FILE.stat().st_size > 0:
            try:
                with LOG_JSON_FILE.open("r", encoding="utf-8") as file:
                    data = json.load(file)
                    if isinstance(data, list):
                        logs = data
            except json.JSONDecodeError:
                pass

        logs.append(
            {"timestamp": timestamp, "prompt": prompt, "response": response}
        )

        with LOG_JSON_FILE.open("w", encoding="utf-8") as file:
            json.dump(logs, file, indent=2, ensure_ascii=False)

    @staticmethod
    def _append_to_txt_log(prompt: str, response: str, timestamp: str) -> None:
        """Menambahkan entri log operasional ke `data/log/chat_logs.txt`."""
        formatted_entry = (
            f"{'=' * 60}\n"
            f"TIMESTAMP : {timestamp}\n"
            f"PROMPT    : {prompt}\n"
            f"RESPONSE  :\n{response}\n"
            f"{'=' * 60}\n\n"
        )

        with LOG_TXT_FILE.open("a", encoding="utf-8") as file:
            file.write(formatted_entry)


def check_and_handle_captcha(page: Page) -> None:
    """Mendeteksi indikator Captcha / Cloudflare secara interaktif."""
    captcha_selectors = [
        "iframe[src*='captcha']",
        "iframe[src*='cloudflare']",
        ".geetest_holder",
        "#captcha-box",
        "text=/verify/i",
        "text=/human/i",
    ]

    for selector in captcha_selectors:
        if page.locator(selector).is_visible():
            print("\n" + "=" * 60)
            print("[WARNING] CAPTCHA / Security Check Terdeteksi!")
            print("Silakan selesaikan verifikasi secara MANUAL di browser.")
            print("=" * 60 + "\n")
            input(">>> Selesai verifikasi? Tekan ENTER untuk melanjutkan... ")
            break


def get_authenticated_context(
    playwright: Playwright, creds: Credentials
) -> tuple[BrowserContext, Page]:
    """Mengelola sesi browser (Cookies/State) dan proses otentikasi."""
    ensure_directories_exist()
    browser = playwright.chromium.launch(headless=False)

    # 1. Gunakan sesi dari file jika tersedia
    if SESSION_FILE.exists():
        print(f"[INFO] Memuat sesi dari cache: {SESSION_FILE}")
        context = browser.new_context(storage_state=SESSION_FILE)
        page = context.new_page()
        page.goto("https://chat.deepseek.com/")

        page.wait_for_timeout(3000)
        check_and_handle_captcha(page)

        if "sign_in" not in page.url:
            print("[SUCCESS] Sesi aktif dan terverifikasi.")
            return context, page

        print("[WARNING] Sesi kadaluarsa. Memulai proses login ulang...")
        context.close()

    # 2. Login Baru jika belum ada sesi / kadaluarsa
    print("[INFO] Melakukan login baru...")
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://chat.deepseek.com/sign_in")

    page.get_by_role("textbox", name="Phone number / email address").click()
    page.get_by_role("textbox", name="Phone number / email address").fill(creds.email)
    page.get_by_role("textbox", name="Password").click()
    page.get_by_role("textbox", name="Password").fill(creds.password)

    page.get_by_role("button", name="Log in", exact=True).click()

    page.wait_for_timeout(2000)
    check_and_handle_captcha(page)

    try:
        page.wait_for_selector("textarea, [role='textbox']", timeout=30000)
    except Exception:
        check_and_handle_captcha(page)

    context.storage_state(path=SESSION_FILE)
    print(f"[SUCCESS] Sesi berhasil disimpan ke: {SESSION_FILE}")

    return context, page


def send_chat_and_get_response(
    page: Page, prompt: str, session_id: str, seq_idx: int
) -> str:
    """Mengirim pesan ke AI, mengambil balasan, lalu menyimpan data log & raw dataset."""
    print(f"\n[INFO] [Seq {seq_idx}] Sending Prompt: '{prompt}'")

    chat_input = page.get_by_role("textbox", name="Message DeepSeek")
    chat_input.click()
    chat_input.fill(prompt)
    chat_input.press("Enter")

    page.wait_for_timeout(2000)
    check_and_handle_captcha(page)

    # Tunggu balasan AI selesai di-render
    page.wait_for_selector(".ds-markdown", timeout=45000)
    page.wait_for_timeout(3000)

    responses = page.locator(".ds-markdown").all_text_contents()
    last_response = responses[-1] if responses else "No response generated."

    # Simpan log operasional DAN ekspor data mentah untuk analisis
    LoggerService.log_and_export(
        prompt=prompt,
        response=last_response,
        session_id=session_id,
        seq_idx=seq_idx,
    )

    return last_response


def run(playwright: Playwright) -> None:
    creds = Credentials()
    if not creds.email or not creds.password:
        print("[ERROR] DEEPSEEK_EMAIL atau DEEPSEEK_PASSWORD belum diset di .env!")
        sys.exit(1)

    context, page = get_authenticated_context(playwright, creds)

    # Menghasilkan ID Sesi Unik berbasis Timestamp untuk pengelompokan data analisis
    current_session_id = f"session_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    try:
        # Prompt 1
        res_1 = send_chat_and_get_response(
            page=page,
            prompt="Hai Ai",
            session_id=current_session_id,
            seq_idx=1,
        )
        print(f"\n--- Output 1 ---\n{res_1}\n")

        # Prompt 2
        res_2 = send_chat_and_get_response(
            page=page,
            prompt="buat markdown untuk code triangle",
            session_id=current_session_id,
            seq_idx=2,
        )
        print(f"\n--- Output 2 ---\n{res_2}\n")

    finally:
        context.close()


if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)