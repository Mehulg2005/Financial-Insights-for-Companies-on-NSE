from fastapi import APIRouter, HTTPException

from models.company import get_company_by_nse
from models.profit_loss import get_profit_loss
from models.balance_sheet import get_balance_sheet
from models.cash_flow import get_cash_flow

from services.price_service import fetch_range_price_chart, PriceFetchError

from utils.distress_scores import build_distress_scores


router = APIRouter(
    prefix="/company",
    tags=["Distress Scores"]
)


@router.get("/{nse_code}/distress-scores")
def company_distress_scores(nse_code: str):

    nse_code = nse_code.upper()

    company = get_company_by_nse(nse_code)

    if not company:
        raise HTTPException(
            status_code=404,
            detail=f"Company '{nse_code}' not found"
        )

    profit_loss = get_profit_loss(nse_code)
    balance_sheet = get_balance_sheet(nse_code)
    cash_flow = get_cash_flow(nse_code)

    latest_price = None

    try:

        price_data = fetch_range_price_chart(nse_code)
        latest_price = price_data.get("closing_price")

    except PriceFetchError:

        # Only Altman Z's X4 term needs price - if Groww is
        # unreachable, that one score reports insufficient
        # data rather than failing this whole endpoint.
        latest_price = None

    scores = build_distress_scores(
        profit_loss,
        balance_sheet,
        cash_flow,
        latest_price
    )

    return {
        "nse_code": nse_code,
        "company_name": company[2],
        "scores": scores,
    }