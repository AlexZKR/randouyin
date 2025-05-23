"""Script interception utilities for playwright scraper"""

from playwright.async_api import BrowserContext, Route


async def set_request_interceptions(context: BrowserContext) -> None:
    """Intercept optional auxiliary requests to Douyin, like CSS, telemetry, etc.

    Args:
        context (BrowserContext): context of the PW browser
    """
    # Security SDKs and telemetry
    await context.route("**/*", stub_security)

    # Specific packages and ad scripts
    await context.route(
        "**/collect/5.1/collect.zip.js*",
        lambda route: route.fulfill(
            status=200,
            content_type="application/javascript",
            body="// blocked collect.zip.js",
        ),
    )

    await context.route(
        "**/*.woff2",
        lambda route: route.fulfill(status=200, content_type="font/woff2", body=b""),
    )
    await context.route(
        "**/*.ttf",
        lambda route: route.fulfill(status=200, content_type="font/ttf", body=b""),
    )

    # General fallback for all other resource types
    # await context.route("**/*", fulfill_resource)

    # Remove service worker
    await context.add_init_script("delete navigator.serviceWorker;")


async def fulfill_resource(route: Route):
    resource_type = route.request.resource_type
    if resource_type in ("xhr", "fetch", "script", "document"):
        await route.continue_()
    elif resource_type == "image":
        await route.fulfill(status=200, content_type="image/png", body=b"")
    elif resource_type == "stylesheet":
        await route.fulfill(
            status=200, content_type="text/css", body="/* blocked css */"
        )
    elif resource_type == "font":
        await route.fulfill(status=200, content_type="font/woff2", body=b"")
    elif resource_type == "media":
        await route.fulfill(status=200, content_type="video/mp4", body=b"")
    elif resource_type == "texttrack":
        await route.fulfill(status=200, content_type="text/vtt", body="")
    elif resource_type == "eventsource":
        await route.fulfill(status=200, content_type="text/event-stream", body="")
    elif resource_type == "websocket":
        await route.fulfill(
            status=200, content_type="application/octet-stream", body=b""
        )
    elif resource_type == "manifest":
        await route.fulfill(
            status=200, content_type="application/manifest+json", body="{}"
        )
    else:
        await route.continue_()


async def stub_security(route, request):
    """Instead of requesting heavy security (and other) SDKs fulfill the request right away"""
    url = request.url
    # Match all known security SDK patterns
    if any(
        domain in url
        for domain in [
            "secsdk-lastest.umd.js",
            "webmssdk.es5.js",
            "sdk-glue.js",
            "monitor_browser/collect",
            "strategy_90.js",
            "runtime.js",
            "collect",
            "security-secsdk",
        ]
    ):
        await route.fulfill(
            status=200,
            content_type="application/javascript",
            body="/* stubbed security SDK */\nwindow.__sdk_stub = true;",
        )
    else:
        await route.continue_()
