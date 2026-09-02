"""Aplikasi Utama FastAPI Server."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI
from app.routers import chat_router
from app.services.browser_service import DeepSeekBrowserService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifecycle manager untuk inisialisasi dan cleanup Playwright Engine."""
    print("\n[SERVER STARTUP] Memulai inisialisasi Playwright Browser Engine...")
    browser_service = DeepSeekBrowserService.get_instance()
    
    # Inisialisasi Browser di Background Task agar Startup FastAPI tidak terblokir
    asyncio.create_task(browser_service.initialize_deepseek())

    yield

    print("\n[SERVER SHUTDOWN] Menutup browser engine...")
    await browser_service.shutdown()


app = FastAPI(
    title="DeepSeek Automation API",
    version="2.0.0",
    description="FastAPI Service yang membungkus Playwright Async untuk interaksi DeepSeek AI.",
    lifespan=lifespan,
)

app.include_router(chat_router.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)