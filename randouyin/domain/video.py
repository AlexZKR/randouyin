from pydantic import BaseModel


class ParsedVideo(BaseModel):
    """Video, parsed from search results card

    Scraper gets it first
    """

    id: int
    image_url: str
    duration: str
    title: str
    date: str
    author: str
    likes: int


class SourcedVideo(ParsedVideo):
    """`ParsedVideo`, selected for download,
    contains list of sources for download
    """

    sources: list[str]
