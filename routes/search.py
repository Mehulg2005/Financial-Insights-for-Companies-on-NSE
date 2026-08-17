from fastapi import APIRouter, HTTPException

from utils.database import (
    company_exists,
    get_company_data,
    get_last_updated
)


router = APIRouter()


# --------------------------------------------------
# Search company
# --------------------------------------------------

@router.get(
    "/search/{nse_code}"
)
def search_company(nse_code: str):

    nse_code = nse_code.upper().strip()


    if not nse_code:

        raise HTTPException(
            status_code=400,
            detail="NSE code cannot be empty."
        )


    print(
        f"\nSearching for: {nse_code}"
    )


    print(
        "Checking PostgreSQL..."
    )


    # --------------------------------------------------
    # Check database
    # --------------------------------------------------

    if not company_exists(nse_code):

        print(
            "Company not found in PostgreSQL."
        )

        return {
            "found": False,
            "nse_code": nse_code,
            "message": (
                f"{nse_code} is not present "
                "in the database. "
                "Use Update Data to scrape Screener."
            )
        }


    print(
        "Company found in PostgreSQL."
    )


    rows = get_company_data(
        nse_code
    )


    if not rows:

        raise HTTPException(
            status_code=404,
            detail="No data found."
        )


    # --------------------------------------------------
    # Company information
    # --------------------------------------------------

    company_name = rows[0][1]

    last_updated = (
        get_last_updated(nse_code)
    )


    # --------------------------------------------------
    # Get all periods
    # --------------------------------------------------

    periods = sorted(
        set(
            row[3]
            for row in rows
        ),
        key=period_sort_key
    )


    # --------------------------------------------------
    # Organize data by metric
    # --------------------------------------------------

    metrics = {}


    for row in rows:

        metric = row[2]
        period = row[3]
        value = row[4]


        if metric not in metrics:

            metrics[metric] = {}


        metrics[metric][period] = value


    # --------------------------------------------------
    # Convert to frontend-friendly format
    # --------------------------------------------------

    result = []


    for metric, values in metrics.items():

        result.append(
            {
                "metric": metric,
                "values": [
                    values.get(period)
                    for period in periods
                ]
            }
        )


    return {
        "found": True,
        "nse_code": nse_code,
        "company_name": company_name,
        "last_updated": (
            last_updated.isoformat()
            if last_updated
            else None
        ),
        "periods": periods,
        "metrics": result
    }


# --------------------------------------------------
# Sort periods chronologically
# --------------------------------------------------

def period_sort_key(period):

    try:

        month, year = period.split()

        month_numbers = {
            "Jan": 1,
            "Feb": 2,
            "Mar": 3,
            "Apr": 4,
            "May": 5,
            "Jun": 6,
            "Jul": 7,
            "Aug": 8,
            "Sep": 9,
            "Oct": 10,
            "Nov": 11,
            "Dec": 12
        }

        return (
            int(year),
            month_numbers.get(
                month,
                0
            )
        )

    except Exception:

        return (
            9999,
            9999
        )