from randouyin.ports.base_scraper import BaseScraper


class PlaywrightScraper(BaseScraper):
    def search_videos(self, query: str) -> list[str]:
        raise NotImplementedError
