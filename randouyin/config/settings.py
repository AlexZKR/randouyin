from functools import lru_cache

from pydantic import BaseModel
from pydantic_settings import BaseSettings

from randouyin.config.config_logging import setup_logging


class ScrapingSettings(BaseModel):
    # Logging
    SLOWNESS_THRESHOLD_MS: float = 100
    """Request time logger uses this value to identify slow requests"""

    # Page locators
    SEARCH_LIST_CONTAINER_LOCATOR: str = (
        "div#waterFallScrollContainer div[id^='waterfall_item']"
    )
    """Used to extract video card containers"""

    SINGLE_VIDEO_TAG_LOCATOR: str = "video"
    """Used to get HTML video element of one video"""

    SEARCH_PAGE_SEARCH_BTN_LOCATOR: str = 'button[data-e2e="searchbar-button"]'
    """Button that submits search input for video search"""

    SEARCH_PAGE_SEARCH_INTPUT_LOCATOR: str = 'input[data-e2e="searchbar-input"]'
    """Text field for search query"""

    # Scraper
    USE_HEADLESS_BROWSER: bool = True
    """Use headless (without UI) or not (with UI) browser for playwright scraping"""

    SEARCH_PAGE_LOADING_TIMEOUT: float = 50000
    """Page takes some time to load and display the content"""

    # Cookies
    COOKIE_FOLDER: str = "randouyin/config/"
    """Folder for storing Doyuin cookies"""

    COOKIE_FILENAME: str = "cookies.json"
    """Filename for Doyuin cookies"""

    # Timeout crash folder
    TIMEOUT_CRASH_FOLDER: str = "timeout_crashes"

    # URLs
    DOUYIN_SEARCH_URL: str = "https://www.douyin.com/search/{query}"
    """Douyin search URL"""

    DOUYIN_VIDEO_URL: str = "https://www.douyin.com/video/{id}"
    """URL for single video (has download srcs)"""


class Settings(BaseSettings):
    LOG_LEVEL: str = "INFO"

    scraping: ScrapingSettings = ScrapingSettings()


@lru_cache
def get_settings():
    settings = Settings()
    setup_logging(log_level=settings.LOG_LEVEL)
    return settings
