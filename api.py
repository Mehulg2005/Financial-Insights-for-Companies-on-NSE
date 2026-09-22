from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from routes.concalls import router as concalls_router
from contextlib import asynccontextmanager

from utils.scraper import close_selenium

from routes.company import router as company_router
from routes.insights import router as insights_router
from routes.profit_loss import router as profit_loss_router
from routes.balance_sheet import router as balance_sheet_router
from routes.cash_flow import router as cash_flow_router
from routes.features import router as features_router
from routes.price import router as price_router
from routes.distress import router as distress_router

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

templates = Jinja2Templates(directory="templates")

# ==================================================
# Pages
#
# Bare paths (no "/company" prefix) so these never
# collide with the JSON API routes below, which all
# live under /company/{nse_code}/...
# ==================================================

@app.get("/")
def landing_page(request: Request):
    return templates.TemplateResponse(
        request,
        "landing.html",
        {
            "nse_code": None,
            "active_page": None,
        }
    )


@app.get("/{nse_code}")
def overview_page(request: Request, nse_code: str):

    return templates.TemplateResponse(
        request,
        "overview.html",
        {
            "nse_code": nse_code.upper(),
            "active_page": "overview",
        }
    )


@app.get("/{nse_code}/financials")
def financials_page(request: Request, nse_code: str):

    return templates.TemplateResponse(
        request,
        "financials.html",
        {
            "nse_code": nse_code.upper(),
            "active_page": "financials",
            # Title card price keeps updating, but no chart card.
            "price_tracker_mode": "title_only",
        }
    )


@app.get("/{nse_code}/fundamentals")
def fundamentals_page(request: Request, nse_code: str):

    return templates.TemplateResponse(
        request,
        "fundamentals.html",
        {
            "nse_code": nse_code.upper(),
            "active_page": "fundamentals",
            # No price data at all on this page - just the
            # company name in the title card.
            "price_tracker_mode": "none",
        }
    )
@app.get("/{nse_code}/market")
def market_page(request: Request, nse_code: str):

    return templates.TemplateResponse(
        request,
        "market.html",
        {
            "nse_code": nse_code.upper(),
            "active_page": "market",
            "price_tracker_mode": "full",
        }
    )
# ==================================================
# Routers
# ==================================================

app.include_router(company_router)
app.include_router(insights_router)
app.include_router(profit_loss_router)
app.include_router(balance_sheet_router)
app.include_router(cash_flow_router)
app.include_router(features_router)
app.include_router(price_router)
app.include_router(distress_router)
app.include_router(concalls_router)