import requests


# ==================================================
# Groww price chart endpoints
#
# Unofficial, undocumented endpoints discovered via
# browser DevTools (Network tab) on groww.in. No login
# or cookies required. Since neither is a published/
# versioned API, Groww can change their shape or break
# without notice - every failure mode here is caught and
# surfaced as a clear error rather than crashing the
# company page, since price data is a bonus feature, not
# core to the app.
#
# Two distinct resolutions, same response shape:
#   - "monthly/v2" : daily closing candles over N months
#   - "daily"      : per-minute candles for the current
#                     trading day (used for the live view,
#                     intended to be polled repeatedly by
#                     the caller)
# ==================================================

class PriceFetchError(Exception):
    """Raised when Groww's price chart data can't be fetched or parsed."""
    pass


GROWW_BASE_URL = (
    "https://groww.in/v1/api/charting_service/v2/chart/"
    "delayed/exchange/NSE/segment/CASH/{nse_code}/{resolution}"
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


def _fetch_groww_chart(nse_code, resolution, params):
    """
    Shared fetch + parse logic. The range and intraday
    endpoints only differ in URL resolution segment and
    query params - the response shape is otherwise
    identical, so this is the one place that talks to
    Groww and parses its JSON.
    """

    url = GROWW_BASE_URL.format(nse_code=nse_code, resolution=resolution)

    try:

        response = requests.get(
            url,
            params=params,
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


def fetch_range_price_chart(nse_code, months=3):
    """
    Daily closing prices over the last `months` months.
    """

    return _fetch_groww_chart(
        nse_code,
        resolution="monthly/v2",
        params={
            "months": months,
            "minimal": "true",
        },
    )


def fetch_intraday_price_chart(nse_code, interval_minutes=1):
    """
    Per-minute candles for the current trading day. This
    function does a single fetch - the caller (the frontend,
    via repeated requests to the /price-chart?mode=live
    endpoint) is responsible for polling it on an interval
    for a "live" view.
    """

    return _fetch_groww_chart(
        nse_code,
        resolution="daily",
        params={
            "intervalInMinutes": interval_minutes,
            "minimal": "true",
        },
    )