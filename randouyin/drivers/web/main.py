from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

app.mount(
    "/randouyin/drivers/web/static",
    StaticFiles(directory="randouyin/drivers/web/static"),
    name="static",
)

templates = Jinja2Templates(directory="randouyin/drivers/web/templates")


@app.get("/items/{id}", response_class=HTMLResponse)
async def read_item(request: Request, id: str):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"id": id}
    )
