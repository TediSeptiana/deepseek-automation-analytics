"""Router Endpoints untuk Layanan Chat DeepSeek."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from app.models import ChatRequest, ChatResponse
from app.services.browser_service import DeepSeekBrowserService

router = APIRouter(prefix="/api/v1", tags=["DeepSeek Chat"])


@router.get("/health")
async def get_health_status() -> dict[str, str]:
    """Mengecek status kesehatan server dan readiness browser engine."""
    service = DeepSeekBrowserService.get_instance()
    return {
        "service_status": service.status.value,
        "current_session_id": service.current_session_id,
    }


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """Mengirim pesan ke DeepSeek AI dan mengembalikan teks balasan."""
    service = DeepSeekBrowserService.get_instance()

    try:
        response_text, requires_human = await service.send_prompt(request.prompt)

        if requires_human:
            return ChatResponse(
                status="human_intervention_required",
                session_id=service.current_session_id,
                prompt=request.prompt,
                response=response_text,
                human_intervention_required=True,
                message="Silakan selesaikan CAPTCHA di browser yang terbuka.",
            )

        return ChatResponse(
            status="completed",
            session_id=service.current_session_id,
            prompt=request.prompt,
            response=response_text,
            human_intervention_required=False,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan pada Browser Service: {str(exc)}",
        ) from exc