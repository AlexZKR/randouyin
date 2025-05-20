"""Script interception utilities for playwright scraper"""

from playwright.async_api import BrowserContext


async def set_request_interceptions(context: BrowserContext) -> None:
    """Intercept optional auxilary requests to Doyuin, like CSS, telemetry, etc.

    Args:
        context (BrowserContext): context of the PW browser
    """
    # Global rules
    await context.route("**/*", stub_security)
    await context.route(
        "**/*",
        lambda route: route.abort()
        if route.request.resource_type
        in {
            "image",
            "stylesheet",
            "font",
            "media",
            "texttrack",
            "eventsource",
            "websocket",
            "manifest",
            "other",
        }
        else route.continue_(),
    )

    # Images, styling, fonts
    await context.route("**/*.css", lambda r: r.abort())
    await context.route("**/*.{png,jpg,jpeg}", lambda route: route.abort())

    await context.route("**/*ad*.js", lambda r: r.abort())
    await context.route("**/*.woff2", lambda r: r.abort())
    await context.route("**/*.ttf", lambda r: r.abort())

    # Specific packages
    await context.route("**/collect/5.1/collect.zip.js*", lambda route: route.abort())
    await context.route(
        "**/webmssdk.es5.js",
        lambda r: r.fulfill(status=200, content_type="application/javascript", body=""),
    )
    await context.route(
        "**/sdk-glue.js",
        lambda r: r.fulfill(status=200, content_type="application/javascript", body=""),
    )
    await context.add_init_script("delete navigator.serviceWorker;")


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
