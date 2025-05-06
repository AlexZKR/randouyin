import logging

import httpx

from randouyin.ports.base_client import BaseClient

logger = logging.getLogger("httpx")


class HttpxClient(BaseClient):
    async def get_list_video_page(self, query: str) -> str:
        async with httpx.AsyncClient(http2=True) as c:
            logger.info(f"Querying {query} for list video page")

            r = await c.get("https://www.douyin.com/")
            r.raise_for_status()

            r = await c.get(query)
            logger.debug(r.status_code)
            if httpx.codes.is_redirect(r.status_code) and r.next_request:
                r = await c.send(r.next_request)
                logger.debug(r.status_code)
                with open("index.html", "wb") as f:
                    f.write(r.read())
            return "str"
