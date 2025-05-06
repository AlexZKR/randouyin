from playwright.sync_api import Playwright, sync_playwright


def run(play: Playwright):
    start_url = "https://www.douyin.com/root/search/1123"
    chrome = play.chromium
    browser = chrome.launch(headless=False)
    page = browser.new_page()
    page.goto(start_url)

    divs = page.locator("div[id^='waterfall_item']")

    ids = divs.evaluate_all("divs => divs.map(div => div.id)")

    for div_id in ids:
        print(div_id)

    browser.close()


with sync_playwright() as play:
    run(play)
