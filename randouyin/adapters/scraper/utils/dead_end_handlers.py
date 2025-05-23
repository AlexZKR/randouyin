"""Dead end is a situation where website stop fullfilling the request.
For example, "Log in to view exciting content" - we need to enter the query once more.

It's not a pop up - the message is displayed on the page itself, so it's not blocking anything
"""

import logging

from playwright.async_api import Page

from randouyin.adapters.scraper.utils.exc import DeadEndException

logger = logging.getLogger("playwright")


async def handle_log_in_to_view_content_de(page: Page):
    """Handle \"Log in to view exciting content\" dead end

    Popup text: 登录后查看精彩内容

    Args:
        page (Page): Page where to setup a handler
    """

    async def popup_handler():
        logger.info("Detected log in dead end. Retrying the request...")
        raise DeadEndException

    popup_locator = page.get_by_text("登录后查看精彩内容", exact=False)
    await page.add_locator_handler(
        popup_locator, handler=popup_handler, no_wait_after=True
    )
