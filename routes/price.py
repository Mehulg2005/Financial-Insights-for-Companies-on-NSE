from fastapi import APIRouter, HTTPException

from services.price_service import fetch_price_chart, PriceFetchError


router = APIRouter(
    prefix="/company",
    tags=["Price"]
)


@router.get("/{nse_code}/price-chart")
def company_price_chart(nse_code: str):

    nse_code = nse_code.upper()

    try:

        data = fetch_price_chart(nse_code)

    except PriceFetchError as error:

        raise HTTPException(
            status_code=502,
            detail=str(error)
        )

    return {
        "nse_code": nse_code,
        "candles": data["candles"],
        "closing_price": data["closing_price"],
        "change_value": data["change_value"],
        "change_percent": data["change_percent"],
    }