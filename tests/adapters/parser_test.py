import pytest
from randouyin.domain.video import ParsedVideo
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

    def test_single_video_tag_parsing(
        self, parser: BaseParser, video_tag_html: tuple[str, dict, dict]
    ) -> None:
        """Video tag parsing results in list of links for video download

        Args:
            parser (BaseParser): BS4 parser fixture
            video_tag_html (tuple[str, dict, dict]): test fixture
                - str - example HTML;
                - dict - dict of `ParsedVideo` model;
                - dict - expected result (`SourcedVideo` model).
        """
        try:
            model = ParsedVideo.model_validate(video_tag_html[1])
            result = parser.parse_single_video_tag(
                parsed_video=model, tag_html=video_tag_html[0]
            )

            # check fields and types
            result.model_validate(video_tag_html[2])

            # check values
            assert video_tag_html[2] == result.model_dump()
        except Exception as e:
            pytest.fail(reason=str(e))
