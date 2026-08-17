from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

from routes.search import router as search_router
from routes.update import router as update_router

from utils.database import initialize_database


app = FastAPI(
    title="Screener Insights API",
    description="API for searching and updating Screener Insights data.",
    version="1.0"
)


templates = Jinja2Templates(
    directory="templates"
)


@app.on_event("startup")
def startup():

    print("\nInitializing PostgreSQL...")

    initialize_database()

    print("PostgreSQL database initialized.")


app.include_router(search_router)
app.include_router(update_router)


@app.get("/")
def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )