"""
End-to-End Integration Tests untuk Layanan DeepSeek API.
Menjalankan 7 Skenario Pengujian Kritis (Auth, Rate Limiting, Git Leaks, Data Leaks).
"""

import asyncio
import os
import subprocess
from typing import Any

import httpx
import pytest

# --- KONFIGURASI ---
BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api/v1")
VALID_API_KEY = os.getenv("APP_API_KEY", "dev-secret-key-123")
HEADER_NAME = "X-API-Key"
DUMMY_PAYLOAD = {"prompt": "ping"}


@pytest.fixture
async def async_client() -> httpx.AsyncClient:
    """Fixture untuk menyediakan HTTPX AsyncClient."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        yield client


# ==========================================
# TEST 1: POST /chat tanpa API key -> 401
# ==========================================
@pytest.mark.asyncio
async def test_post_chat_no_api_key(async_client: httpx.AsyncClient) -> None:
    """Memastikan request tanpa header API Key ditolak dengan 401."""
    response = await async_client.post("/chat", json=DUMMY_PAYLOAD)
    assert response.status_code == 401
    assert "header" in response.json()["detail"].lower()


# ==========================================
# TEST 2: POST /chat API key salah -> 401
# ==========================================
@pytest.mark.asyncio
async def test_post_chat_wrong_api_key(async_client: httpx.AsyncClient) -> None:
    """Memastikan request dengan API Key yang salah ditolak dengan 401."""
    headers = {HEADER_NAME: "wrong-api-key-123"}
    response = await async_client.post("/chat", headers=headers, json=DUMMY_PAYLOAD)
    assert response.status_code == 401
    assert "tidak valid" in response.json()["detail"].lower()


# ==========================================
# TEST 3: POST /chat API key benar -> 200
# ==========================================
@pytest.mark.asyncio
async def test_post_chat_valid_api_key(async_client: httpx.AsyncClient) -> None:
    """Memastikan request dengan API Key valid diterima dengan 200."""
    headers = {HEADER_NAME: VALID_API_KEY}
    response = await async_client.post("/chat", headers=headers, json=DUMMY_PAYLOAD)
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "response" in data


# ==========================================
# TEST 4: 30+ request dalam waktu singkat -> 429
# ==========================================
@pytest.mark.asyncio
async def test_rate_limiting(async_client: httpx.AsyncClient) -> None:
    """
    Memastikan Rate Limiter aktif dengan menembakkan 35 request serentak.
    Harus ada minimal satu request yang mengembalikan status 429 (Too Many Requests).
    """
    headers = {HEADER_NAME: VALID_API_KEY}
    
    # Mengirim 35 requests secara concurrent (bersamaan)
    tasks = [
        async_client.post("/chat", headers=headers, json=DUMMY_PAYLOAD)
        for _ in range(35)
    ]
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    # Ambil status code dari setiap response yang valid
    status_codes = [
        res.status_code for res in responses if isinstance(res, httpx.Response)
    ]
    
    # Verifikasi bahwa Rate Limiter memblokir request berlebih
    assert 429 in status_codes, "Sistem tidak memblokir spam request (429 tidak ditemukan)!"


# ==========================================
# TEST 5: .env -> tidak tracked Git
# ==========================================
def test_env_not_tracked_in_git() -> None:
    """Memastikan file .env (credentials) tidak ter-track oleh Git."""
    # `git ls-files .env` akan kosong jika file tidak dilacak oleh git
    result = subprocess.run(
        ["git", "ls-files", ".env"], capture_output=True, text=True, check=False
    )
    output = result.stdout.strip()
    assert output == "", f"BAHAYA KEAMANAN: File .env terdeteksi di Git track! ({output})"


# ==========================================
# TEST 6: data/state/ -> tidak tracked Git
# ==========================================
def test_data_state_not_tracked_in_git() -> None:
    """Memastikan folder state browser tidak ter-track oleh Git."""
    result = subprocess.run(
        ["git", "ls-files", "data/state/"], capture_output=True, text=True, check=False
    )
    output = result.stdout.strip()
    assert output == "", "BAHAYA KEAMANAN: Folder data/state/ terdeteksi di Git track!"


# ==========================================
# TEST 7: API response -> tidak mengandung kredensial sensitif
# ==========================================
@pytest.mark.asyncio
async def test_api_response_no_sensitive_data(async_client: httpx.AsyncClient) -> None:
    """Memastikan response API tidak membocorkan password, API Key, atau raw state."""
    headers = {HEADER_NAME: VALID_API_KEY}
    response = await async_client.post("/chat", headers=headers, json=DUMMY_PAYLOAD)
    
    # Cek response body JSON
    data: dict[str, Any] = response.json()
    response_string = response.text.lower()
    
    # 1. Pengecekan pada Keys dict (Struktur Data)
    forbidden_keys = {"password", "api_key", "apikey", "secret", "session_state", "browser_state"}
    for key in data.keys():
        assert key.lower() not in forbidden_keys, f"Response mengandung key terlarang: {key}"
        
    # 2. Pengecekan pada Values (Kebocoran data ke klien)
    assert VALID_API_KEY.lower() not in response_string, "API KEY BOCOOR dalam response text!"
    assert "password" not in response_string