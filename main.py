import asyncio
from typing import Annotated

import nest_asyncio
from fastapi import Body, FastAPI, Query, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from news_filters import NewsFilter
from news_loader import NewsLoader
from orchestrator import Orchestrator
from styles import Style
from utils import JSONStreamingResponse

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.state.news_loader = NewsLoader()
app.state.orca = Orchestrator()


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/options")
async def get_options(request: Request):
    news_options = NewsFilter.get_json_options()
    style_options = Style.get_json_options()
    return {**news_options, **style_options}


@app.get("/api/feed")
async def get_news(request: Request, news_filter: Annotated[NewsFilter, Query()]):
    app.state.loaded_news = app.state.news_loader.get_news(news_filter)
    return {"news": app.state.loaded_news, "n_filter": news_filter}


@app.post("/api/generate")
async def generate(
    request: Request,
    article: Annotated[int, Body()],
    platform: Annotated[str, Body()],
):
    style = Style.model_validate_json(await request.body())
    nest_asyncio.apply(asyncio.get_event_loop())
    article = app.state.loaded_news[article]
    return JSONStreamingResponse(
        app.state.orca.generate(article, style, platform),
        media_type="text/event-stream",
    )
