import asyncio
from random import choice, randint, random, uniform

from playwright.async_api import Page


async def random_waiting(a: float = 0.1, b: float = 1) -> None:
    """Random waiting in range [a, b], from 0.1 to 2 secs by default"""
    await asyncio.sleep(uniform(a, b))


async def simulate_scrolling(page: Page) -> None:
    for i in range(3):
        await page.mouse.wheel(delta_y=randint(300, 500), delta_x=randint(0, 50))
        await asyncio.sleep(uniform(1, 3))


async def simulate_human_behavior(page: Page) -> None:
    for _ in range(randint(3, 7)):
        await page.mouse.move(randint(100, 800), randint(100, 600))
        await asyncio.sleep(uniform(0.1, 0.3))

    if random() > 0.7:  # noqa: PLR2004
        await page.keyboard.press(choice(["Tab", "Shift", "Alt"]))
        await asyncio.sleep(uniform(0.1, 0.2))
