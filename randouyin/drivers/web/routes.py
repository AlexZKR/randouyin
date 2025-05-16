from fastapi import FastAPI

from randouyin.drivers.web.api.video.video import router as video_router
from randouyin.drivers.web.api.views.index_view import router as views_router


def register_routes(app: FastAPI):
    app.include_router(views_router)
    app.include_router(video_router)
