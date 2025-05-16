from pydantic import BaseModel


class ParsedVideo(BaseModel):
    """Video, parsed from search results card

    Scraper gets it first
    """

    id: int
    image_url: str
    duration: str | None
    title: str
    date: str
    author: str
    likes: int | None


class SourcedVideo(BaseModel):
    """Video, selected for download,
    contains list of sources for download
    """

    id: int
    sources: list[str]
