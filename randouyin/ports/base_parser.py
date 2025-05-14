from abc import ABC, abstractmethod

from randouyin.domain.video import ParsedVideo, SourcedVideo


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
    def parse_single_video_tag(
        self, parsed_video: ParsedVideo, tag_html: str
    ) -> SourcedVideo:
        """Populate model with links for downloading the video

        Args:
            parsed_video (ParsedVideo): basic video model, parsed from search card
            tag_html (str): video tag, parsed from single video page

        Returns:
            SourcedVideo: `ParsedVideo` model, populated with list of sources for download
        """
        ...
