from functools import lru_cache

from pydantic import BaseModel
from pydantic_settings import BaseSettings

from randouyin.config.config_logging import setup_logging


class ScrapingSettings(BaseModel):
    douyin_search_url: str = "https://www.douyin.com/root/search/{query}"
    """Douyin search URL"""


class Settings(BaseSettings):
    LOG_LEVEL: str = "INFO"

    scraping: ScrapingSettings = ScrapingSettings()


@lru_cache
def get_settings():
    settings = Settings()
    setup_logging(log_level=settings.LOG_LEVEL)
    return settings
