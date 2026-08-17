from fastapi import APIRouter, HTTPException

from utils.selenium_scraper import (
    scrape_company,
    start_selenium
)

from utils.data_processor import (
    process_scraped_data
)

from utils.database import (
    insert_company_data,
    get_company_data,
    get_last_updated
)


router = APIRouter()


# --------------------------------------------------
# Update company
# --------------------------------------------------

@router.post(
    "/update/{nse_code}"
)
def update_company(nse_code: str):

    nse_code = nse_code.upper().strip()


    if not nse_code:

        raise HTTPException(
            status_code=400,
            detail="NSE code cannot be empty."
        )


    print(
        f"\nUpdating: {nse_code}"
    )


    try:

        # --------------------------------------------------
        # Make sure Selenium is running
        # --------------------------------------------------

        start_selenium()


        # --------------------------------------------------
        # Scrape Screener
        # --------------------------------------------------

        company_name, data = (
            scrape_company(nse_code)
        )


        # --------------------------------------------------
        # Process scraped data
        # --------------------------------------------------

        processed_data = (
            process_scraped_data(
                data,
                nse_code,
                company_name
            )
        )


        # --------------------------------------------------
        # Insert/update PostgreSQL
        # --------------------------------------------------

        records_count = (
            insert_company_data(
                nse_code,
                company_name,
                processed_data
            )
        )


        print(
            f"Inserted/updated "
            f"{records_count} records."
        )


        # --------------------------------------------------
        # Get updated data
        # --------------------------------------------------

        rows = get_company_data(
            nse_code
        )


        last_updated = (
            get_last_updated(nse_code)
        )


        # --------------------------------------------------
        # Get periods
        # --------------------------------------------------

        periods = sorted(
            set(
                row[3]
                for row in rows
            ),
            key=period_sort_key
        )


        # --------------------------------------------------
        # Organize metrics
        # --------------------------------------------------

        metrics = {}


        for row in rows:

            metric = row[2]
            period = row[3]
            value = row[4]


            if metric not in metrics:

                metrics[metric] = {}


            metrics[metric][period] = value


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
            "success": True,
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


    except Exception as e:

        print(
            f"Error updating "
            f"{nse_code}: {e}"
        )


        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


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