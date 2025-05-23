import os
from os import path
from uuid import UUID, uuid4

from fastapi import HTTPException
from playwright.async_api import Page, TimeoutError

from randouyin.config.settings import get_settings


async def handle_timeout_crash(
    page: Page, e: TimeoutError, requests_info: str, raise_exc: bool = False
) -> UUID:
    """Handler for Playwright timeout errors: saves screenshots, HTML and error stack

    Every timeout error creates a folder named `timeout_<UUID>`. The folder contains
    a screenshot, html of the page and error information. Func either returns UUID of the crash or
    raises a HTTPException with informative message for the user (contains `timeout_id`).

    Args:
        page (Page): page where timeout happened
        e (TimeoutError): error from which to save the trace
        requests_info (str): message, that contains information about requests, made during an operation. Can be arbitrary or received from
        `RequestTimeLogger`
        raise_exc (bool, optional): Whether to raise `fastapi.HTTPException` that will send `timeout_id` to the user. Defaults to False.

    Raises:
        HTTPException: Optional. See `raise_exc` arg description

    Returns:
        UUID: `timeout_id` if HTTPException wasn't raised.
    """
    timeout_id = uuid4()

    folder_name = f"timeout_{timeout_id}"
    crash_folder = get_settings().scraping.TIMEOUT_CRASH_FOLDER

    wd = path.join(crash_folder, folder_name)

    if not path.exists(crash_folder):
        os.mkdir(crash_folder)

    if not path.exists(wd):
        os.mkdir(wd)

    # take screenshot
    await page.screenshot(path=f"{wd}/screenshot.png")

    # save html
    html = await page.content()
    if html:
        with open(f"{wd}/page.html", "w", encoding="utf-8") as f:
            f.write(html)

    # write error stack and message to txt file
    with open(f"{wd}/error.txt", "a", encoding="utf-8") as f:
        f.write(f"MESSAGE:\n\n{e.message}\n")
        if e.stack:
            f.write("STACK:\n\n")
            f.write(e.stack)

    if requests_info:
        with open(f"{wd}/requests.txt", "a", encoding="utf-8") as f:
            f.write(requests_info)

    # send error message to the user
    if raise_exc:
        raise HTTPException(
            status_code=500,
            detail=f"Timeout error happened. Contact admin and send him this:\n\nTimeout error: {timeout_id}",
        )
    return timeout_id
