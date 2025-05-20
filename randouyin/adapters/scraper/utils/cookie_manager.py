import json
import logging
import os
from os import path

from playwright.async_api import BrowserContext

from randouyin.config.settings import get_settings

logger = logging.getLogger("playwright")


class PWCookieManager:
    """Manages cookies of Playwright browser context

    TODO: manage cookie expiration
    """

    def __init__(self) -> None:
        self.cookie_folder = get_settings().scraping.COOKIE_FOLDER
        self.cookie_filename = get_settings().scraping.COOKIE_FILENAME
        self.cookie_path = path.join(self.cookie_folder, self.cookie_filename)

    async def load_from_file(self, context: BrowserContext) -> None:
        """Load cookies from JSON file (path defined in scraper settings)

        Args:
            context (BrowserContext): Context for which to load cookies
        """
        if path.exists(self.cookie_path):
            with open(self.cookie_path) as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
            logger.info("Loaded cookies!")
        else:
            logger.info("Can't load cookies from file: no cookie file.")

    async def save_to_file(self, context: BrowserContext) -> None:
        """Save cookies to a JSON file

        Args:
            context (BrowserContext): Context from which to take cookies
        """
        cookies = await context.cookies()
        if path.exists(self.cookie_path):
            logger.info("Saving cookies to JSON")
            with open(self.cookie_path, "w") as f:
                f.write(json.dumps(cookies))
        else:
            logger.info(
                f"Can't save cookies to file: cookie path {self.cookie_path} don't exists."
            )

    def delete_cookie_file(self) -> None:
        """Delete JSON cookie file"""
        if path.exists(self.cookie_path):
            logger.info("Deleting old cookies")
            os.remove(self.cookie_path)
