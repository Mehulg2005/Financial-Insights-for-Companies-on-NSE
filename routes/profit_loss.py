from fastapi import APIRouter, HTTPException

from models.company import get_company_by_nse
from models.profit_loss import get_profit_loss
from utils.pivot import pivot_by_period


router = APIRouter(
    prefix="/company",
    tags=["Profit & Loss"]
)


@router.get("/{nse_code}/profit-loss")
def company_profit_loss(nse_code: str):

    nse_code = nse_code.upper()

    company = get_company_by_nse(nse_code)

    if not company:
        raise HTTPException(
            status_code=404,
            detail=f"Company '{nse_code}' not found"
        )

    records = get_profit_loss(nse_code)

    return {
        "nse_code": nse_code,
        "company_name": company[2],
        "records": pivot_by_period(records)
    }