import pytest
from randouyin.ports.base_client import BaseClient


class TestHttpxDownload:
    @pytest.mark.parametrize(
        "source_url",
        [
            (
                "https://www.douyin.com/aweme/v1/play/?file_id=df7eebaf785e451ca39774b73b5733a3&is_play_url=1&line=0&sign=b4b678ab6fcfde9a0f58a7fa2dfac985&source=PackSourceEnum_AWEME_DETAIL&uifid=e6c27fbf464929995ee328d4ad6a224ecf7f3ea8d9b074dfc158d2c84c45cda16a91be900fafbf96ccd4d8ca77db863e9386d59930a4d8500e89b3a3dc7f8991035258c9d5f5d6aebf1c7ecdad69e079&video_id=v0300fg10000d0djabvog65na200aj2g&aid=6383"
            ),
        ],
    )
    async def test_video_downloading(
        self, downloader: BaseClient, source_url: str
    ) -> None:
        """Test that video can be downloaded"""
        try:
            await downloader.download_video(url=source_url)
        except Exception as e:
            pytest.fail(reason=str(e))
