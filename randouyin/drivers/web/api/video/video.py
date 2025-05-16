from logging import getLogger

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from randouyin.domain.video import SourcedVideo
from randouyin.drivers.web.dependencies import client, parser, scraper
from randouyin.ports.base_client import BaseClient
from randouyin.ports.base_parser import BaseParser
from randouyin.ports.base_scraper import BaseScraper

logger = getLogger("fastapi")
router = APIRouter(prefix="/video")


@router.post("/download/{id}")
async def download_video(
    request: Request,
    id: int,
    scraper: BaseScraper = Depends(scraper),
    parser: BaseParser = Depends(parser),
    client: BaseClient = Depends(client),
):
    logger.info(f"Received request for downloading video {id}")
    async with scraper as s:
        video_html = await s.get_video(id)
    sources = parser.parse_single_video_tag(video_html)
    model = SourcedVideo(id=id, sources=sources)

    return StreamingResponse(
        client.stream_video(model.sources[0]),
        media_type="video/mp4",
        headers={"Content-Disposition": f'attachment; filename="video_{id}.mp4"'},
    )
