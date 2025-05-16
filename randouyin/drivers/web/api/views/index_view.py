from logging import getLogger

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from randouyin.drivers.web.dependencies import parser, scraper
from randouyin.ports.base_parser import BaseParser
from randouyin.ports.base_scraper import BaseScraper

logger = getLogger("fastapi")

router = APIRouter()
templates = Jinja2Templates(directory="randouyin/drivers/web/templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@router.post("/search")
async def search_videos(
    request: Request,
    query: str = Form(...),
    scraper: BaseScraper = Depends(scraper),
    parser: BaseParser = Depends(parser),
):
    async with scraper as s:
        logger.info("Searching for videos")
        html_list = await s.search_videos(query)
        logger.info(f"Found {len(html_list)} videos")
        # videos = [parser.parse_video_card(html).model_dump() for html in html_list]

        videos = []
        i = 0
        for h in html_list:
            logger.info(f"Parsing {i} video")
            # logger.info(f"\n\n{h}\n\n\n")
            if "直播中" in h:  # skip live broadcasts
                continue
            m = parser.parse_video_card(h)
            videos.append(m.model_dump())
            i += 1

        return templates.TemplateResponse(
            "index.html", {"request": request, "query": query, "videos": videos}
        )
