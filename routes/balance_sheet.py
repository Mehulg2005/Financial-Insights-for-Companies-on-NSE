from fastapi import APIRouter, HTTPException

from models.company import get_company_by_nse
from models.balance_sheet import get_balance_sheet
from utils.pivot import pivot_by_period


router = APIRouter(
    prefix="/company",
    tags=["Balance Sheet"]
)


@router.get("/{nse_code}/balance-sheet")
def company_balance_sheet(nse_code: str):

    nse_code = nse_code.upper()

    company = get_company_by_nse(nse_code)

    if not company:
        raise HTTPException(
            status_code=404,
            detail=f"Company '{nse_code}' not found"
        )

    records = get_balance_sheet(nse_code)

    return {
        "nse_code": nse_code,
        "company_name": company[2],
        "records": pivot_by_period(records)
    }