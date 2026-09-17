from fastapi import APIRouter, HTTPException

from services.price_service import (
    fetch_range_price_chart,
    fetch_intraday_price_chart,
    PriceFetchError,
)


router = APIRouter(
    prefix="/company",
    tags=["Price"]
)


@router.get("/{nse_code}/price-chart")
def company_price_chart(nse_code: str, mode: str = "range"):

    nse_code = nse_code.upper()

    try:

        if mode == "live":
            data = fetch_intraday_price_chart(nse_code)
        else:
            data = fetch_range_price_chart(nse_code)

    except PriceFetchError as error:

        raise HTTPException(
            status_code=502,
            detail=str(error)
        )

    return {
        "nse_code": nse_code,
        "mode": mode,
        "candles": data["candles"],
        "closing_price": data["closing_price"],
        "change_value": data["change_value"],
        "change_percent": data["change_percent"],
    }