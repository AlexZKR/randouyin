from randouyin.adapters.beautiful_soup_parser import BeautifulSoupParser
from randouyin.adapters.httpx_client import HttpxClient
from randouyin.adapters.playwright_scraper import PlaywrightScraper
from randouyin.ports.base_client import BaseClient
from randouyin.ports.base_parser import BaseParser
from randouyin.ports.base_scraper import BaseScraper


def scraper() -> BaseScraper:
    return PlaywrightScraper()


def parser() -> BaseParser:
    return BeautifulSoupParser()


def client() -> BaseClient:
    return HttpxClient()


def downloader() -> BaseClient:
    return HttpxClient()
