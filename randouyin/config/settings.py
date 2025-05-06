from functools import lru_cache

from pydantic import BaseModel
from pydantic_settings import BaseSettings

from randouyin.config.config_logging import setup_logging


class ParsingSettings(BaseModel):
    douyin_video_list_url: str = "https://www.douyin.com/root/search/{query}"
    """URL for search results page. Used to parse IDs of videos"""


class Settings(BaseSettings):
    LOG_LEVEL: str = "INFO"

    parsing: ParsingSettings = ParsingSettings()


@lru_cache
def get_settings():
    settings = Settings()
    setup_logging(log_level=settings.LOG_LEVEL)
    return settings
