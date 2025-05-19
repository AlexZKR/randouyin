from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status

from randouyin.adapters.beautiful_soup_parser import BeautifulSoupParser
from randouyin.adapters.httpx_client import HttpxClient
from randouyin.adapters.playwright_scraper import PlaywrightScraper
from randouyin.ports.base_client import BaseClient
from randouyin.ports.base_parser import BaseParser
from randouyin.ports.base_scraper import BaseScraper

pw_scraper: PlaywrightScraper | None = None


async def scraper(request: Request) -> BaseScraper:
    scraper = getattr(request.app.state, "pw_scraper", None)
    if scraper:
        return scraper
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Playwright scraper isn't initialized",
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize Playwright scraper before the app starts"""
    async with PlaywrightScraper() as pw:
        app.state.pw_scraper = pw
        yield


def parser() -> BaseParser:
    return BeautifulSoupParser()


def client() -> BaseClient:
    return HttpxClient()


def downloader() -> BaseClient:
    return HttpxClient()
