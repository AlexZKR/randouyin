import html
import re

from bs4 import BeautifulSoup

from randouyin.domain.video import ParsedVideo, SourcedVideo
from randouyin.ports.base_parser import BaseParser


class BeautifulSoupParser(BaseParser):
    def parse_video_card(self, card_html: str) -> ParsedVideo:
        soup = BeautifulSoup(card_html, "html.parser")
        model: dict = {}

        # 1) Container by id
        container = soup.find("div", attrs={"id": re.compile(r"^waterfall_item_\d+$")})

        model["id"] = container["id"].split("waterfall_item_")[-1]

        # 3) <img> URL
        img_tag = container.find("img", src=True)
        model["image_url"] = html.unescape(img_tag["src"])

        # 4) Duration: find a text node matching HH:MM
        duration_text = container.find(string=re.compile(r"^\d{2}:\d{2}$"))
        model["duration"] = duration_text.strip() if duration_text else None

        # 5) Likes: span immediately after the SVG
        svg = container.find("svg")
        likes = None
        if svg:
            sib = svg.find_next_sibling("span")
            if sib and sib.string and sib.string.isdigit():
                likes = int(sib.string)
        model["likes"] = likes

        # 6) Title
        image_container = container.find(
            "div", attrs={"style": re.compile(r"padding-top:\s*\d+(\.\d+)?%;")}
        )
        bottom_container = image_container.find_next_sibling("div")
        title_container = bottom_container.next.next
        model["title"] = title_container.find_next("div").text

        # 7) Author & date: look in the last metadata div
        author = date = None
        for div in reversed(container.find_all("div")):
            txt = div.get_text(strip=True)
            if "@" in txt:
                parts = re.split(r"\s*·\s*", txt)
                # remove leading @ if present
                author = parts[0].lstrip("@")
                date = parts[1] if len(parts) > 1 else None
                break
        model["author"] = author
        model["date"] = date

        # logger.info(f"\n\n\n {model} \n\n\n")

        return ParsedVideo(**model)

    def parse_single_video_tag(
        self, parsed_video: ParsedVideo, tag_html: str
    ) -> SourcedVideo:
        soup = BeautifulSoup(tag_html, "html.parser")

        # extract every src from each source child element of video tag
        res = [
            c.attrs["src"]
            for c in soup.find("video").children
            if "\n" not in c.get_text()
        ]
        sourced_video = SourcedVideo(**parsed_video.model_dump(), sources=res)
        return sourced_video
