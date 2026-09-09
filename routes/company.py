from fastapi import APIRouter, HTTPException

from services.company_service import (
    get_or_scrape_company,
    update_company
)


router = APIRouter(
    prefix="/company",
    tags=["Company"]
)


# ==================================================
# Helper: format raw DB rows into JSON-friendly dict
# ==================================================

def format_company_data(data):

    company = data["company"]

    return {

        "company": {
            "company_id": company[0],
            "nse_code": company[1],
            "company_name": company[2],
            "last_updated": company[3]
        },

        "quarterly_insights": [
            {
                "id": row[0],
                "nse_code": row[1],
                "metric": row[2],
                "period": row[3],
                "value": row[4],
                "last_updated": row[5]
            }
            for row in data["quarterly_insights"]
        ],

        "profit_loss": [
            {
                "id": row[0],
                "nse_code": row[1],
                "period": row[2],
                "metric": row[3],
                "value": row[4],
                "last_updated": row[5]
            }
            for row in data["profit_loss"]
        ],

        "balance_sheet": [
            {
                "id": row[0],
                "nse_code": row[1],
                "period": row[2],
                "metric": row[3],
                "value": row[4],
                "last_updated": row[5]
            }
            for row in data["balance_sheet"]
        ],

        "cash_flow": [
            {
                "id": row[0],
                "nse_code": row[1],
                "period": row[2],
                "metric": row[3],
                "value": row[4],
                "last_updated": row[5]
            }
            for row in data["cash_flow"]
        ]
    }

# ==================================================
# Get Company Data (from DB, scraping only if missing)
# ==================================================

@router.get("/{nse_code}")
def get_company(nse_code: str):

    nse_code = nse_code.upper().strip()

    try:

        data = get_or_scrape_company(nse_code)

    except Exception as e:

        print("\n" + "=" * 100)
        print("SCRAPING PIPELINE FAILED")
        print("=" * 100)

        print(str(e))

        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve company '{nse_code}'"
        )

    if not data:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Company '{nse_code}' could not be found "
                f"or scraped"
            )
        )

    return format_company_data(data)


# ==================================================
# Update Company Data (always re-scrapes Screener)
# ==================================================

@router.post("/{nse_code}/update")
def update_company_route(nse_code: str):
    """
    Re-scrape a company from Screener (whether or not it
    already exists in the database) and store the latest
    data. Reuses an already-open Selenium session if present.
    """

    nse_code = nse_code.upper().strip()

    try:

        data = update_company(nse_code)

    except Exception as e:

        print("\n" + "=" * 100)
        print("UPDATE PIPELINE FAILED")
        print("=" * 100)

        print(str(e))

        raise HTTPException(
            status_code=500,
            detail=f"Unable to update company '{nse_code}'"
        )

    if not data:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Company '{nse_code}' was scraped but "
                f"could not be updated"
            )
        )

    return format_company_data(data)