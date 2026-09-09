from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from contextlib import asynccontextmanager

from utils.scraper import close_selenium

from routes.company import router as company_router
from routes.insights import router as insights_router
from routes.profit_loss import router as profit_loss_router
from routes.balance_sheet import router as balance_sheet_router
from routes.cash_flow import router as cash_flow_router
from routes.features import router as features_router


@asynccontextmanager
async def lifespan(app: FastAPI):

    # --------------------------------------------------
    # Startup
    #
    # NOTE: Selenium is intentionally NOT started here.
    # It is started lazily (see utils.scraper.start_selenium)
    # the first time a company is searched that isn't already
    # in the database, or when the "Update" button is used.
    # Once open, the same session is reused for every
    # subsequent scrape until the app shuts down.
    # --------------------------------------------------

    print("\n" + "=" * 100)
    print("STARTING APP")
    print("=" * 100)

    yield

    # --------------------------------------------------
    # Shutdown
    # --------------------------------------------------

    print("\n" + "=" * 100)
    print("SHUTTING DOWN")
    print("=" * 100)

    close_selenium()


app = FastAPI(
    title="Financial Insights API",
    description="Financial data API for NSE companies",
    version="2.0.0",
    lifespan=lifespan
)

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

# ==================================================
# Root
# ==================================================

@app.get("/")
def root():
    return FileResponse("templates/index.html")

# ==================================================
# Routers
# ==================================================

app.include_router(company_router)
app.include_router(insights_router)
app.include_router(profit_loss_router)
app.include_router(balance_sheet_router)
app.include_router(cash_flow_router)
app.include_router(features_router)