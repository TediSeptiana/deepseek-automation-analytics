"""Router Endpoints untuk Layanan Chat DeepSeek."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models import ChatRequest, ChatResponse
from app.security import verify_api_key
from app.services.browser_service import DeepSeekBrowserService

# Inisialisasi Rate Limiter berbasis IP address klien
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/api/v1", tags=["DeepSeek Chat"])


def get_browser_service() -> DeepSeekBrowserService:
    """Dependency provider untuk mengakses instance browser service."""
    return DeepSeekBrowserService.get_instance()


@router.get("/health")
async def get_health_status(
    service: DeepSeekBrowserService = Depends(get_browser_service),
) -> dict[str, str]:
    """Mengecek status kesehatan server dan readiness browser engine."""
    return {
        "service_status": service.status.value,
        "current_session_id": service.current_session_id,
    }


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("30/minute")  # Batasi maksimal 30 request per menit per IP (Memperbaiki TEST 4)
async def chat_endpoint(
    request: Request,  # Wajib ada agar slowapi bisa mendeteksi IP klien
    chat_req: ChatRequest,
    _: None = Depends(verify_api_key),  # Memperbaiki TEST 1 & 2 (Autentikasi wajib)
    service: DeepSeekBrowserService = Depends(get_browser_service),
) -> ChatResponse:
    """Mengirim pesan ke DeepSeek AI dengan proteksi API Key dan Rate Limiting."""
    try:
        response_text, requires_human = await service.send_prompt(chat_req.prompt)

        status_str = "human_intervention_required" if requires_human else "completed"
        msg = "Silakan selesaikan CAPTCHA di browser yang terbuka." if requires_human else None

        return ChatResponse(
            status=status_str,
            session_id=service.current_session_id,
            prompt=chat_req.prompt,
            response=response_text,
            human_intervention_required=requires_human,
            message=msg,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan pada Browser Service: {str(exc)}",
        ) from exc