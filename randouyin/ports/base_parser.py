from abc import ABC, abstractmethod

from randouyin.domain.video import ParsedVideo


class BaseParser(ABC):
    """Class for parsing HTML from Doyuin website"""

    @abstractmethod
    def parse_video_card(self, card_html: str) -> ParsedVideo:
        """Parse one video card HTML

        Args:
            card_html (str): Video card HTML from Douyin search results

        Returns:
            ParserVideo: ParsedVideo base model
        """
        ...

    @abstractmethod
    def parse_single_video_tag(self, tag_html: str) -> list[str]:
        """Get links for downloading the video

        Args:
            tag_html (str): video tag, parsed from single video page

        Returns:
            list (str): List of video download sources
        """
        ...
