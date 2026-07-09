from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from shared.observability import setup_observability
setup_observability("multi-agent-app")

from api.routes import router

app = FastAPI()

app.include_router(router)

BASE_DIR = Path(__file__).resolve().parent.parent  # Поднимается из api/ в корень проекта

app.mount("/static", StaticFiles(directory=BASE_DIR / "ui" / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "ui" / "templates")


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        name="index.html",
        context={"request": request},
        request=request
    )

import logging;
root = logging.getLogger(); print(f"🔍 Root: level={root.level}, handlers={[type(h).__name__ for h in root.handlers]}")