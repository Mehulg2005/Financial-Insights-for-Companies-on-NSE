import math

from utils.pivot import pivot_by_period
from utils.features import _get


# ==================================================
# CONFIG / DATA-AVAILABILITY DECISIONS
#
# These were explicitly confirmed with the team before
# implementation, not assumed unilaterally. Kept here in
# one place, same convention as trend_analyzer.py, so
# anyone reviewing this file can see exactly what's real
# data vs a documented proxy.
#
# Current Assets / Current Liabilities:
#     Total Current Assets      = Other Assets
#     Total Current Liabilities = Other Liabilities
# This is used everywhere Current Assets/Liabilities appear -
# Altman X1, Piotroski's Current Ratio criterion, Ohlson's
# WC/TA and CL/CA terms, Springate's A and C terms, and
# Zmijewski's CA/CL term - since they all share the same
# helper functions below.
#
# Altman X2 (Retained Earnings) is a single-period flow
# measure, not Altman's original cumulative balance-sheet
# definition:
#     Retained Earnings = Net Profit - (Net Profit * Dividend Payout % / 100)
#
# Altman X3 (EBIT) / Springate B, shared:
#     EBIT = Profit before Tax + Interest
#
# Altman X4 (Market Value of Equity): shares outstanding is
# approximated as Net Profit / EPS, multiplied by the latest
# available closing price.
#
# FFO (Ohlson) = Cash from Operating Activity
#
# Piotroski criterion #8 (Gross Margin YoY) always scores 0 -
# no reliable Gross Margin data is available.
#
# Ohlson's GNP Index term is dropped (ln(Total Assets) used
# directly) - the original term is a US-specific 1968-base-
# year macroeconomic deflator with no Indian-market equivalent.
#
# Beneish M-Score is NOT implemented - needs Accounts
# Receivable and true Gross Margin, neither available.
#
# TYPE HANDLING: DB values arrive as Decimal, Groww price
# values as float. _to_float() normalizes both before any
# arithmetic mixes them.
#
# SEVERITY: each computed score reports "positive" / "mixed"
# / "negative" (or None if not computed), used by the
# frontend to color-code the card instead of printing an
# interpretation sentence.
# ==================================================


def _to_float(value):

    if value is None:
        return None

    return float(value)


def _latest_two_periods(pivoted_rows):

    if not pivoted_rows:
        return None, None

    if len(pivoted_rows) == 1:
        return pivoted_rows[0], None

    return pivoted_rows[-1], pivoted_rows[-2]


# ==================================================
# Derived value helpers
# ==================================================

def _total_assets(bs_row):
    return _to_float(_get(bs_row, ["Total Assets"]))


def _total_liabilities(bs_row):
    return _to_float(_get(bs_row, ["Total Liabilities"]))


def _current_assets(bs_row):
    return _to_float(_get(bs_row, ["Other Assets"]))


def _current_liabilities(bs_row):
    return _to_float(_get(bs_row, ["Other Liabilities"]))


def _working_capital(bs_row):

    current_assets = _current_assets(bs_row)
    current_liabilities = _current_liabilities(bs_row)

    if current_assets is None or current_liabilities is None:
        return None

    return current_assets - current_liabilities


def _ebit(pnl_row):

    profit_before_tax = _to_float(_get(pnl_row, ["Profit before tax", "Profit before Tax"]))
    interest = _to_float(_get(pnl_row, ["Interest"]))

    if profit_before_tax is None:
        return None

    return profit_before_tax + (interest or 0)


def _retained_earnings(pnl_row):

    net_profit = _to_float(_get(pnl_row, ["Net Profit", "Net profit"]))
    dividend_payout_percent = _to_float(_get(pnl_row, ["Dividend Payout %"]))

    if net_profit is None or dividend_payout_percent is None:
        return None

    return net_profit - (net_profit * dividend_payout_percent / 100)


def _market_value_of_equity(pnl_row, latest_price):

    net_profit = _to_float(_get(pnl_row, ["Net Profit", "Net profit"]))
    eps = _to_float(_get(pnl_row, ["EPS in Rs", "EPS"]))
    latest_price = _to_float(latest_price)

    if net_profit is None or eps in (None, 0) or latest_price is None:
        return None

    shares_outstanding = net_profit / eps

    return shares_outstanding * latest_price


# ==================================================
# A. Altman Z-Score
# ==================================================

def compute_altman_z(pnl_row, bs_row, latest_price):

    total_assets = _total_assets(bs_row)
    total_liabilities = _total_liabilities(bs_row)
    working_capital = _working_capital(bs_row)
    ebit = _ebit(pnl_row)
    sales = _to_float(_get(pnl_row, ["Sales", "Revenue"]))
    retained_earnings = _retained_earnings(pnl_row)
    market_value_of_equity = _market_value_of_equity(pnl_row, latest_price)

    # Report exactly which input(s) are missing, rather than
    # a generic "insufficient data" - makes this self-
    # diagnosing instead of requiring manual investigation.

    missing = []

    if total_assets in (None, 0):
        missing.append("Total Assets")
    if total_liabilities in (None, 0):
        missing.append("Total Liabilities")
    if working_capital is None:
        missing.append("Working Capital (Other Assets / Other Liabilities)")
    if ebit is None:
        missing.append("EBIT (Profit before Tax / Interest)")
    if sales is None:
        missing.append("Sales")
    if retained_earnings is None:
        missing.append("Retained Earnings (Net Profit / Dividend Payout %)")
    if market_value_of_equity is None:
        missing.append("Market Value of Equity (EPS / current price)")

    if missing:
        return {
            "score": None,
            "zone": None,
            "severity": None,
            "note": f"Insufficient data to compute Altman Z-Score - missing: {', '.join(missing)}."
        }

    x1 = working_capital / total_assets
    x2 = retained_earnings / total_assets
    x3 = ebit / total_assets
    x4 = market_value_of_equity / total_liabilities
    x5 = sales / total_assets

    z = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5

    if z > 2.99:
        zone = "Safe Zone"
        severity = "positive"
    elif z >= 1.81:
        zone = "Grey Zone"
        severity = "mixed"
    else:
        zone = "Distress Zone"
        severity = "negative"

    return {"score": round(z, 2), "zone": zone, "severity": severity, "note": None}


# ==================================================
# B. Piotroski F-Score
# ==================================================

def compute_piotroski_f(pnl_row, prior_pnl_row, bs_row, prior_bs_row, cf_row):

    if prior_pnl_row is None or prior_bs_row is None:
        return {
            "score": None,
            "max_score": 9,
            "severity": None,
            "note": "Needs at least 2 periods of data."
        }

    points = 0

    net_profit = _to_float(_get(pnl_row, ["Net Profit", "Net profit"]))
    total_assets = _total_assets(bs_row)
    cfo = _to_float(_get(cf_row, ["Cash from Operating Activity"])) if cf_row else None

    if net_profit is not None and net_profit > 0:
        points += 1

    if net_profit is not None and total_assets not in (None, 0) and (net_profit / total_assets) > 0:
        points += 1

    if cfo is not None and cfo > 0:
        points += 1

    if cfo is not None and net_profit is not None and cfo > net_profit:
        points += 1

    borrowings = _to_float(_get(bs_row, ["Borrowings"]))
    prior_borrowings = _to_float(_get(prior_bs_row, ["Borrowings"]))
    prior_total_assets = _total_assets(prior_bs_row)

    if (
        None not in (borrowings, prior_borrowings, total_assets, prior_total_assets)
        and total_assets and prior_total_assets
    ):
        if (borrowings / total_assets) < (prior_borrowings / prior_total_assets):
            points += 1

    current_assets = _current_assets(bs_row)
    current_liabilities = _current_liabilities(bs_row)
    prior_current_assets = _current_assets(prior_bs_row)
    prior_current_liabilities = _current_liabilities(prior_bs_row)

    if (
        None not in (current_assets, current_liabilities, prior_current_assets, prior_current_liabilities)
        and current_liabilities and prior_current_liabilities
    ):
        if (current_assets / current_liabilities) > (prior_current_assets / prior_current_liabilities):
            points += 1

    equity_capital = _to_float(_get(bs_row, ["Equity Capital"]))
    prior_equity_capital = _to_float(_get(prior_bs_row, ["Equity Capital"]))

    if equity_capital is not None and prior_equity_capital is not None:
        if equity_capital <= prior_equity_capital:
            points += 1

    # Criterion 8 (Gross Margin YoY) always scores 0.

    sales = _to_float(_get(pnl_row, ["Sales", "Revenue"]))
    prior_sales = _to_float(_get(prior_pnl_row, ["Sales", "Revenue"]))

    if (
        None not in (sales, prior_sales, total_assets, prior_total_assets)
        and total_assets and prior_total_assets
    ):
        if (sales / total_assets) > (prior_sales / prior_total_assets):
            points += 1

    if points >= 8:
        band = "Excellent financial health"
        severity = "positive"
    elif points >= 3:
        band = "Average or steady performance"
        severity = "mixed"
    else:
        band = "Weak fundamentals, high risk"
        severity = "negative"

    return {
        "score": points,
        "max_score": 9,
        "band": band,
        "severity": severity,
        "note": "Gross Margin criterion always scores 0 - no reliable Gross Margin data available."
    }


# ==================================================
# D. Ohlson O-Score
# ==================================================

def compute_ohlson_o(pnl_row, prior_pnl_row, bs_row, cf_row):

    total_assets = _total_assets(bs_row)
    total_liabilities = _total_liabilities(bs_row)
    working_capital = _working_capital(bs_row)
    current_assets = _current_assets(bs_row)
    current_liabilities = _current_liabilities(bs_row)
    net_income = _to_float(_get(pnl_row, ["Net Profit", "Net profit"]))
    cfo = _to_float(_get(cf_row, ["Cash from Operating Activity"])) if cf_row else None

    required = [
        total_assets, total_liabilities, working_capital,
        current_assets, current_liabilities, net_income, cfo
    ]

    if (
        any(value is None for value in required)
        or total_assets in (None, 0)
        or total_liabilities in (None, 0)
        or current_assets in (None, 0)
    ):
        return {
            "score": None,
            "probability": None,
            "severity": None,
            "note": "Insufficient data to compute Ohlson O-Score."
        }

    prior_net_income = None

    if prior_pnl_row is not None:
        prior_net_income = _to_float(_get(prior_pnl_row, ["Net Profit", "Net profit"]))

    oeneg = 1 if total_liabilities > total_assets else 0

    intwo = 0

    if net_income is not None and prior_net_income is not None:
        if net_income < 0 and prior_net_income < 0:
            intwo = 1

    chin = 0

    if net_income is not None and prior_net_income is not None:

        denominator = abs(net_income) + abs(prior_net_income)

        if denominator:
            chin = (net_income - prior_net_income) / denominator

    try:

        t_score = (
            -1.32
            - 0.407 * math.log(total_assets)
            + 6.03 * (total_liabilities / total_assets)
            - 1.43 * (working_capital / total_assets)
            + 0.0757 * (current_liabilities / current_assets)
            - 1.72 * oeneg
            - 2.37 * (net_income / total_assets)
            + 0.285 * (cfo / total_liabilities)
            - 1.72 * intwo
            - 0.521 * chin
        )

        probability = math.exp(t_score) / (1 + math.exp(t_score))

    except (ValueError, OverflowError):

        return {
            "score": None,
            "probability": None,
            "severity": None,
            "note": "Could not compute Ohlson O-Score (invalid inputs)."
        }

    if probability > 0.50:
        risk = "High risk of bankruptcy"
        severity = "negative"
    else:
        risk = "Safe/Normal operational standing"
        severity = "positive"

    return {
        "score": round(t_score, 3),
        "probability": round(probability, 3),
        "risk": risk,
        "severity": severity,
        "note": "GNP Index term omitted (US-specific, no Indian-market equivalent)."
    }


# ==================================================
# E. Springate S-Score
# ==================================================

def compute_springate_s(pnl_row, bs_row):

    total_assets = _total_assets(bs_row)
    working_capital = _working_capital(bs_row)
    ebit = _ebit(pnl_row)
    profit_before_tax = _to_float(_get(pnl_row, ["Profit before tax", "Profit before Tax"]))
    current_liabilities = _current_liabilities(bs_row)
    sales = _to_float(_get(pnl_row, ["Sales", "Revenue"]))

    required = [total_assets, working_capital, ebit, profit_before_tax, current_liabilities, sales]

    if (
        any(value is None for value in required)
        or total_assets in (None, 0)
        or current_liabilities in (None, 0)
    ):
        return {
            "score": None,
            "verdict": None,
            "severity": None,
            "note": "Insufficient data to compute Springate S-Score."
        }

    a = working_capital / total_assets
    b = ebit / total_assets
    c = profit_before_tax / current_liabilities
    d = sales / total_assets

    s = 1.03 * a + 3.07 * b + 0.66 * c + 0.4 * d

    if s > 0.862:
        verdict = "Healthy"
        severity = "positive"
    else:
        verdict = "Financial distress warning"
        severity = "negative"

    return {"score": round(s, 3), "verdict": verdict, "severity": severity, "note": None}


# ==================================================
# F. Zmijewski X-Score
# ==================================================

def compute_zmijewski_x(pnl_row, bs_row):

    total_assets = _total_assets(bs_row)
    total_liabilities = _total_liabilities(bs_row)
    net_income = _to_float(_get(pnl_row, ["Net Profit", "Net profit"]))
    current_assets = _current_assets(bs_row)
    current_liabilities = _current_liabilities(bs_row)

    required = [total_assets, total_liabilities, net_income, current_assets, current_liabilities]

    if (
        any(value is None for value in required)
        or total_assets in (None, 0)
        or current_liabilities in (None, 0)
    ):
        return {
            "score": None,
            "verdict": None,
            "severity": None,
            "note": "Insufficient data to compute Zmijewski X-Score."
        }

    x = (
        -4.336
        - 4.513 * (net_income / total_assets)
        + 5.679 * (total_liabilities / total_assets)
        + 0.004 * (current_assets / current_liabilities)
    )

    if x > 0:
        verdict = "High distress profile"
        severity = "negative"
    else:
        verdict = "Solid buffer profile"
        severity = "positive"

    return {"score": round(x, 3), "verdict": verdict, "severity": severity, "note": None}


# ==================================================
# Build all scores
# ==================================================

def build_distress_scores(profit_loss_records, balance_sheet_records, cash_flow_records, latest_price):

    pnl_pivoted = pivot_by_period(profit_loss_records)
    bs_pivoted = pivot_by_period(balance_sheet_records)
    cf_pivoted = pivot_by_period(cash_flow_records)

    pnl_row, prior_pnl_row = _latest_two_periods(pnl_pivoted)
    bs_row, prior_bs_row = _latest_two_periods(bs_pivoted)
    cf_row, _ = _latest_two_periods(cf_pivoted)

    beneish_placeholder = {
        "score": None,
        "verdict": None,
        "severity": None,
        "note": "Not implemented - requires Accounts Receivable and Gross Margin data not currently available."
    }

    if pnl_row is None or bs_row is None:

        empty_note = "Insufficient data to compute distress scores."

        return {
            "altman_z": {"score": None, "zone": None, "severity": None, "note": empty_note},
            "piotroski_f": {"score": None, "max_score": 9, "severity": None, "note": empty_note},
            "beneish_m": beneish_placeholder,
            "ohlson_o": {"score": None, "probability": None, "severity": None, "note": empty_note},
            "springate_s": {"score": None, "verdict": None, "severity": None, "note": empty_note},
            "zmijewski_x": {"score": None, "verdict": None, "severity": None, "note": empty_note},
        }

    return {
        "altman_z": compute_altman_z(pnl_row, bs_row, latest_price),
        "piotroski_f": compute_piotroski_f(pnl_row, prior_pnl_row, bs_row, prior_bs_row, cf_row),
        "beneish_m": beneish_placeholder,
        "ohlson_o": compute_ohlson_o(pnl_row, prior_pnl_row, bs_row, cf_row),
        "springate_s": compute_springate_s(pnl_row, bs_row),
        "zmijewski_x": compute_zmijewski_x(pnl_row, bs_row),
    }