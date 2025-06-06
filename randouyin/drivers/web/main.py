from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from randouyin.drivers.web.routes import register_routes

app = FastAPI()
register_routes(app)


app.mount(
    "/randouyin/drivers/web/static",
    StaticFiles(directory="randouyin/drivers/web/static"),
    name="static",
)
