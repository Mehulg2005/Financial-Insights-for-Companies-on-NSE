import requests


# ==================================================
# Groww price chart endpoint
#
# Unofficial, undocumented endpoint discovered via
# browser DevTools (Network tab) on groww.in. No login
# or cookies required. Since it's not a published/
# versioned API, Groww can change its shape or break
# this without notice - every failure mode here is
# caught and surfaced as a clear error rather than
# crashing the company page, since price data is a
# bonus feature, not core to the app.
# ==================================================

class PriceFetchError(Exception):
    """Raised when Groww's price chart data can't be fetched or parsed."""
    pass


GROWW_CHART_URL = (
    "https://groww.in/v1/api/charting_service/v2/chart/"
    "delayed/exchange/NSE/segment/CASH/{nse_code}/monthly/v2"
)

REQUEST_TIMEOUT_SECONDS = 8

# A plain requests.get with no headers can get rejected by
# some sites as "not a real browser" - these headers make
# the request look like an ordinary browser visit, even
# though no login/session is actually required here.
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://groww.in/",
    "Accept": "application/json",
}


def fetch_price_chart(nse_code, months=3):
    """
    Fetch daily closing prices for the last `months` months
    from Groww's delayed chart endpoint.

    Returns a dict:
        {
            "candles": [{"timestamp": <epoch seconds>, "price": <float>}, ...],
            "closing_price": <float> or None,
            "change_value": <float> or None,
            "change_percent": <float> or None,
        }

    Raises PriceFetchError on any failure (network issue,
    unexpected status code, unexpected JSON shape) so the
    caller can decide how to degrade gracefully instead of
    the whole request blowing up.
    """

    url = GROWW_CHART_URL.format(nse_code=nse_code)

    try:

        response = requests.get(
            url,
            params={
                "months": months,
                "minimal": "true",
            },
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

        response.raise_for_status()

        payload = response.json()

    except requests.RequestException as error:

        raise PriceFetchError(
            f"Could not reach Groww for '{nse_code}': {error}"
        ) from error

    except ValueError as error:

        raise PriceFetchError(
            f"Groww returned an unexpected (non-JSON) response for '{nse_code}'."
        ) from error

    raw_candles = payload.get("candles")

    if not isinstance(raw_candles, list):

        raise PriceFetchError(
            f"Groww's response for '{nse_code}' did not contain a 'candles' "
            f"list - the endpoint's shape may have changed."
        )

    candles = []

    for entry in raw_candles:

        if not isinstance(entry, list) or len(entry) < 2:
            continue

        timestamp, price = entry[0], entry[1]

        if timestamp is None or price is None:
            continue

        candles.append({
            "timestamp": timestamp,
            "price": price,
        })

    return {
        "candles": candles,
        "closing_price": payload.get("closingPrice"),
        "change_value": payload.get("changeValue"),
        "change_percent": payload.get("changePerc"),
    }