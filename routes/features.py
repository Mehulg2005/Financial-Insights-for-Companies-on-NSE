from fastapi import APIRouter, HTTPException

from models.company import get_company_by_nse
from models.profit_loss import get_profit_loss
from models.balance_sheet import get_balance_sheet
from models.cash_flow import get_cash_flow

from utils.features import build_features


router = APIRouter(
    prefix="/company",
    tags=["Features"]
)


@router.get("/{nse_code}/features")
def company_features(nse_code: str):

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

    features = build_features(
        profit_loss,
        balance_sheet,
        cash_flow
    )

    return {
        "nse_code": nse_code,
        "company_name": company[2],
        "profitability": features["profitability"],
        "growth": features["growth"],
        "leverage": features["leverage"],
        "cash_flow_quality": features["cash_flow_quality"],
    }