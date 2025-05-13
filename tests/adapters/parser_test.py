import pytest
from randouyin.ports.base_parser import BaseParser


class TestDouyinParsing:
    def test_video_search_card_parsing(
        self, parser: BaseParser, search_video_card_html: tuple[str, dict]
    ) -> None:
        """Video search returns list of video ids"""
        try:
            result = parser.parse_video_card(search_video_card_html[0])

            # check fields and types
            result.model_validate(search_video_card_html[1])

            # check values
            assert search_video_card_html[1] == result.model_dump()

        except Exception as e:
            pytest.fail(reason=str(e))
