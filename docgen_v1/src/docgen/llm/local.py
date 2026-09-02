from __future__ import annotations
import asyncio
from typing import Any
import aiohttp

class LocalLLMError(RuntimeError):
    pass

class LocalLLMClient:
    """HTTP client for the local FastAPI-compatible LLM endpoint."""

    def __init__(self, base_url: str, timeout: float = 120.0,
                 retries: int = 2, retry_delay: float = 2.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._retries = max(0, retries)
        self._retry_delay = retry_delay
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.close()

    async def start(self) -> None:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self._timeout)

    async def close(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()

    async def health(self) -> bool:
        await self.start()
        assert self._session is not None
        try:
            async with self._session.get(f"{self._base_url}/health") as response:
                if response.status != 200:
                    return False
                data = await response.json(content_type=None)
                return data.get("service_status") == "ready"
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
            return False

    async def generate(self, prompt: str) -> str:
        await self.start()
        assert self._session is not None
        last_error = None

        for attempt in range(self._retries + 1):
            try:
                async with self._session.post(
                    f"{self._base_url}/chat", json={"prompt": prompt}
                ) as response:
                    body = await response.text()

                    if response.status >= 500 and attempt < self._retries:
                        await asyncio.sleep(self._retry_delay)
                        continue

                    if response.status >= 400:
                        raise LocalLLMError(
                            f"LLM HTTP {response.status}: {body[:500]}"
                        )

                    try:
                        data = await response.json(content_type=None)
                    except ValueError as exc:
                        raise LocalLLMError(
                            f"LLM returned invalid JSON: {body[:500]}"
                        ) from exc

                    result = data.get("response")
                    if not isinstance(result, str):
                        raise LocalLLMError(
                            "LLM response must contain string field 'response'."
                        )
                    return result.strip()

            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                last_error = exc
                if attempt < self._retries:
                    await asyncio.sleep(self._retry_delay)
                    continue
                break

        raise LocalLLMError(
            f"Unable to reach local LLM after {self._retries + 1} attempt(s)."
        ) from last_error
