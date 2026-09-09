from fastapi import APIRouter, HTTPException

from models.company import get_company_by_nse
from models.qres_insights import get_insights


router = APIRouter(
    prefix="/company",
    tags=["Quarterly Insights"]
)


@router.get("/{nse_code}/insights")
def company_insights(nse_code: str):

    nse_code = nse_code.upper()

    company = get_company_by_nse(nse_code)

    if not company:
        raise HTTPException(
            status_code=404,
            detail=f"Company '{nse_code}' not found"
        )

    records = get_insights(nse_code)

    return {
        "nse_code": nse_code,
        "company_name": company[2],
        "records": [
            {
                "metric": row[2],
                "period": row[3],
                "value": row[4]
            }
            for row in records
        ]
    }