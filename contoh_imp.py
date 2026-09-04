"""Script Klien untuk Pengujian Endpoint DeepSeek FastAPI."""

from __future__ import annotations

import os
import sys
import time
from typing import Any

import requests

# --- CONFIGURATION ---
BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api/v1")
API_KEY = os.getenv("APP_API_KEY", "your-super-secret-default-key")
HEADER_API_KEY_NAME = "X-API-Key"

# --- HTTP CLIENT SETUP ---
def create_authenticated_session() -> requests.Session:
    """Membuat instance requests.Session dengan header autentikasi default."""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        HEADER_API_KEY_NAME: API_KEY,
    })
    return session


# --- CORE FUNCTIONS ---
def wait_for_service_ready(session: requests.Session, timeout_sec: int = 60) -> bool:
    """Memeriksa status health check hingga browser siap (Polling)."""
    print("[INFO] Mengecek readiness status server...")
    start_time = time.time()

    while time.time() - start_time < timeout_sec:
        try:
            res = session.get(f"{BASE_URL}/health", timeout=5)
            if res.status_code == 200:
                data = res.json()
                status = data.get("service_status")
                print(f"[STATUS] Engine Browser: {status}")

                if status == "ready":
                    return True
                if status == "human_intervention_required":
                    print("[WARN] Selesaikan CAPTCHA di browser yang terbuka!")
        except requests.RequestException:
            print("[WAIT] Menunggu FastAPI server berjalan...")

        time.sleep(3)

    return False


def send_chat_prompt(session: requests.Session, prompt: str, timeout_sec: int = 60) -> dict[str, Any] | None:
    """Mengirim request prompt ke endpoint /chat."""
    payload = {"prompt": prompt}
    print("\n[INFO] Mengirim request ke /api/v1/chat...")

    try:
        response = session.post(f"{BASE_URL}/chat", json=payload, timeout=timeout_sec)
        
        if response.status_code == 200:
            return response.json()
        
        print(f"[ERROR] HTTP {response.status_code}: {response.text}")
        return None
    except requests.RequestException as exc:
        print(f"[ERROR] Gagal melakukan request: {exc}")
        return None


def print_chat_response(data: dict[str, Any]) -> None:
    """Mencetak output respon chat dengan format yang rapi."""
    print("\n" + "=" * 50)
    print("Status   :", data.get("status"))
    print("Session  :", data.get("session_id"))
    print("Response :\n", data.get("response"))
    print("=" * 50)


# --- ENTRY POINT ---
def main() -> None:
    session = create_authenticated_session()

    if not wait_for_service_ready(session):
        print("[ERROR] Server/Browser tidak siap dalam batas waktu.")
        sys.exit(1)

    prompt_text = (
        "cari berita atau informasi terkini tentang kebakaran kalimantan di Indonesia, "
        "termasuk penyebab, dampak, dan upaya penanggulangannya. sertakan juga sumber nya. "
        "Dampak di sektor lain seperti kesehatan, ekonomi, dan lingkungan juga harus disertakan. "
        "Sertakan Perusahaan yang kemungkinan terpengaruh terhadap kebakaran tersebut"
        "buat ringkasan singkat dari berita tersebut dan berikan link ke sumber aslinya."
    )

    result = send_chat_prompt(session, prompt_text)
    if result:
        print_chat_response(result)


if __name__ == "__main__":
    main()