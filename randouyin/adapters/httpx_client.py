from httpx import AsyncClient

from randouyin.ports.base_client import BaseClient


class HttpxClient(BaseClient):
    async def download_video(self, url: str) -> None:
        async with AsyncClient() as client:
            async with client.stream("GET", url, follow_redirects=True) as response:
                response.raise_for_status()
                with open("video.mp4", "wb") as f:
                    async for chunk in response.aiter_bytes():
                        f.write(chunk)
