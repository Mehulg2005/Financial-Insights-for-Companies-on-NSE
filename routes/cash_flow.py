from fastapi import APIRouter, HTTPException

from models.company import get_company_by_nse
from models.cash_flow import get_cash_flow
from utils.pivot import pivot_by_period


router = APIRouter(
    prefix="/company",
    tags=["Cash Flow"]
)


@router.get("/{nse_code}/cash-flow")
def company_cash_flow(nse_code: str):

    nse_code = nse_code.upper()

    company = get_company_by_nse(nse_code)

    if not company:
        raise HTTPException(
            status_code=404,
            detail=f"Company '{nse_code}' not found"
        )

    records = get_cash_flow(nse_code)

    return {
        "nse_code": nse_code,
        "company_name": company[2],
        "records": pivot_by_period(records)
    }