from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator


class BaseClient(ABC):
    """Client to make async requests to Douyin for video"""

    @abstractmethod
    async def download_video(self, url: str) -> None:
        """Download video file from link"""
        ...

    @abstractmethod
    async def stream_video(self, url: str) -> AsyncGenerator[bytes]:
        """Stream video data from link"""
        # To satifsy static type checker
        if False:
            yield b""
