from functools import lru_cache

from pydantic import BaseModel
from pydantic_settings import BaseSettings

from randouyin.config.config_logging import setup_logging


class ScrapingSettings(BaseModel):
    # Page locators
    SEARCH_LIST_CONTAINER_LOCATOR: str = (
        "div#waterFallScrollContainer div[id^='waterfall_item']"
    )
    """Used to extract """

    # Scraper
    USE_HEADLESS_BROWSER: bool = True
    """Use headless (without UI) or not (with UI) browser for playwright scraping"""

    # URLs
    DOUYIN_SEARCH_URL: str = "https://www.douyin.com/root/search/{query}"
    """Douyin search URL"""


class Settings(BaseSettings):
    LOG_LEVEL: str = "INFO"

    scraping: ScrapingSettings = ScrapingSettings()


@lru_cache
def get_settings():
    settings = Settings()
    setup_logging(log_level=settings.LOG_LEVEL)
    return settings
