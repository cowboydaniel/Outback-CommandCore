"""Asyncio basics with async/await and tasks."""

from __future__ import annotations

import asyncio


async def fetch_data(delay: float) -> str:
    await asyncio.sleep(delay)
    return f"data after {delay}s"


async def main() -> None:
    tasks = [asyncio.create_task(fetch_data(0.1)), asyncio.create_task(fetch_data(0.2))]
    results = await asyncio.gather(*tasks)
    print(results)


if __name__ == "__main__":
    asyncio.run(main())
