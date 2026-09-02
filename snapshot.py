import asyncio
from pathlib import Path
from playwright.async_api import async_playwright


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://books.toscrape.com/")
        snapshot = await page.aria_snapshot()
        print(snapshot)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())