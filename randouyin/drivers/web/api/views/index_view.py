from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from randouyin.drivers.web.dependencies import parser, scraper
from randouyin.ports.base_parser import BaseParser
from randouyin.ports.base_scraper import BaseScraper

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
        html_list = await s.search_videos(query)
        videos = [parser.parse_video_card(html).model_dump() for html in html_list]

        return templates.TemplateResponse(
            "index.html", {"request": request, "query": query, "videos": videos}
        )
