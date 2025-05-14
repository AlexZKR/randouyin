from abc import ABC, abstractmethod


class BaseClient(ABC):
    """Client to make async requests to Douyin for video"""

    @abstractmethod
    async def download_video(self, url: str) -> None:
        """Download video file from link"""
        ...
