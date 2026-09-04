"""Modul keamanan untuk autentikasi dan otorisasi API."""

import os
import secrets
from typing import Annotated

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

# Idealnya diambil dari app.config (misal menggunakan pydantic-settings)
# Fallback diletakkan di sini untuk kemudahan development lokal
EXPECTED_API_KEY = os.getenv("APP_API_KEY", "dev-secret-key-123")

# Inisialisasi skema keamanan OpenAPI
# auto_error=False mencegah FastAPI melempar 403 default, 
# sehingga kita bisa melempar 401 Unauthorized secara manual (best practice API).
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: Annotated[str | None, Security(api_key_header)]
) -> None:
    """
    Dependency FastAPI untuk memvalidasi keberadaan dan keabsahan X-API-Key.
    
    Args:
        api_key: Nilai dari header X-API-Key yang diinjeksi oleh FastAPI.
        
    Raises:
        HTTPException: 401 jika header tidak ada atau key tidak cocok.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header X-API-Key tidak ditemukan.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
        
    # Menggunakan secrets.compare_digest untuk mencegah timing attacks
    if not secrets.compare_digest(api_key, EXPECTED_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key tidak valid.",
            headers={"WWW-Authenticate": "ApiKey"},
        )