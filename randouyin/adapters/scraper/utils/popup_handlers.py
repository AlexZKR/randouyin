"""This file contains page handler for certain popups

Handler for search page are installed in models/search_page.py
"""

import logging

from fastapi import HTTPException, status
from playwright.async_api import Page

logger = logging.getLogger("playwright")


async def handle_sign_in_popup(page: Page):
    """Handle \"Please, sign in\" popup

    Popup text: 请登录后继续使用
    Popup cancel button text: 取消
    Popup ok button text: 确定

    Args:
        page (Page): Page where to setup a handler
    """

    async def popup_handler():
        logger.info("Detected sign-in popup: clicking '取消'")
        cancel_locator = page.get_by_text("取消", exact=False)
        await cancel_locator.click()

    popup_locator = page.get_by_text("请登录后继续使用", exact=False)
    await page.add_locator_handler(
        popup_locator, handler=popup_handler, no_wait_after=True
    )


async def handle_captcha_popup(page: Page):
    """Handle CAPTCHA popup

    TODO: currently poor implementation, detect captchas properly

    Args:
        page (Page): Page where to setup a handler
    """

    async def popup_handler():
        logger.info("Detected captcha popup")
        await page.screenshot(path="randouyin/captcha.png", full_page=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CAPTCHA detected – screenshot saved to captcha.png",
        )

    popup_locator = page.locator("div#captcha_container")
    await page.add_locator_handler(
        popup_locator, handler=popup_handler, no_wait_after=True
    )
