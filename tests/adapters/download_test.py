import pytest
from randouyin.ports.base_client import BaseClient


class TestHttpxDownload:
    @pytest.mark.parametrize(
        "source_url",
        [
            (
                "https://v3-dy-o.zjcdn.com/942d52dbcb5d63251c078842e7111a67/68247a5b/video/tos/cn/tos-cn-ve-15/o00kIkTAABiFFgCEFThBfiC3qADpXEIUeZDAVQ/?a=6383&br=686&bt=686&btag=c0000e00020000&cc=1f&cd=0%7C0%7C0%7C3&ch=26&cquery=100B_100x_100z_100o_100w&cr=3&cs=0&cv=1&dr=0&ds=6&dy_q=1747210235&feature_id=46a7bb47b4fd1280f3d3825bf2b29388&ft=FYraJC~03u17cvjVQFtiiB7usDvSNSnaglcjp&l=20250514161035889612FF3BD45107A774&lr=all&mime_type=video_mp4&qs=12&rc=NjY6ZTo3OjZmOGg7aWVoaUBpam0zNXE5cmVtMzMzNGkzM0BeMDIwXzQ2Xi4xMjReYjRhYSMvXi1eMmRzXmFhLS1kLTBzcw%3D%3D&req_cdn_type=&temp=1"
            ),
            (
                "https://v3-dy-o.zjcdn.com/942d52dbcb5d63251c078842e7111a67/68247a5b/video/tos/cn/tos-cn-ve-15/o00kIkTAABiFFgCEFThBfiC3qADpXEIUeZDAVQ/?a=6383&br=686&bt=686&btag=c0000e00020000&cc=1f&cd=0%7C0%7C0%7C3&ch=26&cquery=100z_100o_100w_100B_100x&cr=3&cs=0&cv=1&dr=0&ds=6&dy_q=1747210235&feature_id=46a7bb47b4fd1280f3d3825bf2b29388&ft=FYraJC~03u17cvjVQFtiiB7usDvSNSnaglcjp&l=20250514161035889612FF3BD45107A774&lr=all&mime_type=video_mp4&qs=12&rc=NjY6ZTo3OjZmOGg7aWVoaUBpam0zNXE5cmVtMzMzNGkzM0BeMDIwXzQ2Xi4xMjReYjRhYSMvXi1eMmRzXmFhLS1kLTBzcw%3D%3D&req_cdn_type=&temp=1"
            ),
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
