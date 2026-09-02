"""Service pengelola Playwright secara Async dan Persistent Browser Instance."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Final, Self
from playwright.async_api import (
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

from app.config import settings
from app.models import ServiceStatusEnum
from app.services.exporter_service import ExporterService

CAPTCHA_SELECTORS: Final[list[str]] = [
    "iframe[src*='captcha']",
    "iframe[src*='cloudflare']",
    ".geetest_holder",
    "#captcha-box",
    "text=/verify/i",
    "text=/human/i",
]


class DeepSeekBrowserService:
    """Manager Singleton untuk Mengendalikan Browser Playwright secara Async."""

    _instance: Self | None = None

    def __init__(self) -> None:
        self.playwright: Playwright | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.status: ServiceStatusEnum = ServiceStatusEnum.INITIALIZING
        self.sequence_counter: int = 0
        self.current_session_id: str = (
            f"session_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        )
        self._ready_event: asyncio.Event = asyncio.Event()

    @classmethod
    def get_instance(cls) -> DeepSeekBrowserService:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def initialize_deepseek(self) -> None:
        """Inisialisasi Playwright Context dan Melakukan Sesi Check/Login."""
        settings.ensure_directories()
        self.status = ServiceStatusEnum.INITIALIZING
        self._ready_event.clear()

        try:
            self.playwright = await async_playwright().start()

            browser = await self.playwright.chromium.launch(
                headless=settings.headless,
                args=["--start-maximized"],
            )

            # 1. Cek State/Cookies
            if settings.session_file.exists():
                print(f"[INFO] Memuat sesi dari: {settings.session_file}")
                self.context = await browser.new_context(
                    storage_state=settings.session_file,
                    no_viewport=True,
                )
                self.page = await self.context.new_page()
                await self.page.goto("https://chat.deepseek.com/")
                await asyncio.sleep(3)

                await self._wait_for_captcha_resolution_if_any()

                if "sign_in" not in self.page.url:
                    print("[SUCCESS] Sesi aktif dan siap digunakan.")
                    self.status = ServiceStatusEnum.READY
                    self._ready_event.set()
                    return

                print("[WARNING] Sesi kadaluarsa. Menutup konteks lama...")
                await self.context.close()

            # 2. Login Baru
            print("[INFO] Melakukan login baru ke DeepSeek...")
            self.context = await browser.new_context(no_viewport=True)
            self.page = await self.context.new_page()
            await self.page.goto("https://chat.deepseek.com/sign_in")

            await self.page.get_by_role(
                "textbox", name="Phone number / email address"
            ).fill(settings.email)
            await self.page.get_by_role("textbox", name="Password").fill(
                settings.password
            )
            await self.page.get_by_role("button", name="Log in", exact=True).click()

            await asyncio.sleep(2)
            await self._wait_for_captcha_resolution_if_any()

            try:
                await self.page.wait_for_selector(
                    "textarea, [role='textbox']", timeout=30000
                )
            except Exception:
                await self._wait_for_captcha_resolution_if_any()

            await self.context.storage_state(path=settings.session_file)
            print(f"[SUCCESS] Sesi baru tersimpan di: {settings.session_file}")
            self.status = ServiceStatusEnum.READY
            self._ready_event.set()

        except Exception as exc:
            self.status = ServiceStatusEnum.ERROR
            print(f"[ERROR] Gagal menginisialisasi Browser Service: {exc}")
            self._ready_event.set()  # Release awaiter agar melemparkan Exception

    async def _check_is_captcha_present(self) -> bool:
        if not self.page:
            return False

        for selector in CAPTCHA_SELECTORS:
            try:
                locator = self.page.locator(selector)
                if await locator.is_visible():
                    return True
            except Exception:
                continue
        return False

    async def _wait_for_captcha_resolution_if_any(self) -> None:
        if await self._check_is_captcha_present():
            print("\n" + "=" * 60)
            print(
                "[WARNING] CAPTCHA Terdeteksi! Menunggu intervensi manual di browser..."
            )
            print("=" * 60 + "\n")

            self.status = ServiceStatusEnum.HUMAN_INTERVENTION_REQUIRED

            timer = 0
            while await self._check_is_captcha_present():
                await asyncio.sleep(2)
                timer += 2
                if timer >= settings.captcha_timeout_sec:
                    raise TimeoutError(
                        "Timeout menunggu intervensi CAPTCHA pengguna."
                    )

            print("[INFO] CAPTCHA Selesai diverifikasi oleh pengguna!")
            self.status = ServiceStatusEnum.READY

    async def send_prompt(self, prompt: str) -> tuple[str, bool]:
        """Mengirimkan prompt ke DeepSeek dan mengembalikan respon.

        Menunggu secara otomatis hingga browser siap (READY).
        """
        # Tunggu hingga proses inisialisasi awal selesai
        await self._ready_event.wait()

        if self.status == ServiceStatusEnum.HUMAN_INTERVENTION_REQUIRED:
            return (
                "Service sedang menunggu verifikasi CAPTCHA manual di browser.",
                True,
            )

        if not self.page or self.status != ServiceStatusEnum.READY:
            raise RuntimeError("Engine Browser belum siap / mengalami kesalahan.")

        self.sequence_counter += 1

        print(f"[API EXEC] Sending Prompt #{self.sequence_counter}: '{prompt}'")
        chat_input = self.page.get_by_role("textbox", name="Message DeepSeek")
        await chat_input.click()
        await chat_input.fill(prompt)
        await chat_input.press("Enter")

        await asyncio.sleep(2)

        if await self._check_is_captcha_present():
            asyncio.create_task(self._wait_for_captcha_resolution_if_any())
            return (
                "Terdeteksi CAPTCHA/Cloudflare! Silakan selesaikan verifikasi di browser.",
                True,
            )

        # Tunggu balasan AI muncul
        await self.page.wait_for_selector(".ds-markdown", timeout=45000)
        await asyncio.sleep(3)

        responses = await self.page.locator(".ds-markdown").all_text_contents()
        last_response = (
            responses[-1] if responses else "No response generated."
        )

        ExporterService.export(
            prompt=prompt,
            response=last_response,
            session_id=self.current_session_id,
            seq_idx=self.sequence_counter,
        )

        return last_response, False

    async def shutdown(self) -> None:
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()
        self.status = ServiceStatusEnum.INITIALIZING
        print("[INFO] Engine Playwright berhasil ditutup.")