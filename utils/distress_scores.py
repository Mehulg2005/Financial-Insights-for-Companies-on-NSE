import math

from utils.pivot import pivot_by_period
from utils.features import _get


# ==================================================
# CONFIG / DATA-AVAILABILITY DECISIONS
#
# Current Assets / Current Liabilities:
#     Total Current Assets      = Other Assets
#     Total Current Liabilities = Other Liabilities
#
# Beneish M-Score uses:
#     Trade Receivables from the expanded Balance Sheet
#     Material Cost % from the expanded Profit & Loss
#     Manufacturing Cost % from the expanded Profit & Loss
#
# SG&A is derived as:
#     Expenses - COGS
#
# COGS is calculated as:
#     Sales * (Material Cost % + Manufacturing Cost %)
#
# TTM rows are excluded before selecting the latest and prior
# periods so Beneish compares two fiscal-year periods.
# ==================================================


def _to_float(value):

    if value is None:
        return None

    return float(value)


def _exclude_ttm(pivoted_rows):
    return [
        row
        for row in pivoted_rows
        if row.get("period") != "TTM"
    ]


def _latest_two_periods(pivoted_rows):

    pivoted_rows = _exclude_ttm(pivoted_rows)

    if not pivoted_rows:
        return None, None

    if len(pivoted_rows) == 1:
        return pivoted_rows[0], None

    return pivoted_rows[-1], pivoted_rows[-2]


# ==================================================
# Shared derived-value helpers
# ==================================================


def _total_assets(bs_row):
    return _to_float(
        _get(bs_row, ["Total Assets"])
    )


def _total_liabilities(bs_row):
    return _to_float(
        _get(bs_row, ["Total Liabilities"])
    )


def _current_assets(bs_row):
    return _to_float(
        _get(bs_row, ["Other Assets"])
    )


def _current_liabilities(bs_row):
    return _to_float(
        _get(bs_row, ["Other Liabilities"])
    )


def _working_capital(bs_row):

    current_assets = _current_assets(bs_row)
    current_liabilities = _current_liabilities(bs_row)

    if current_assets is None or current_liabilities is None:
        return None

    return current_assets - current_liabilities


def _ebit(pnl_row):

    profit_before_tax = _to_float(
        _get(
            pnl_row,
            [
                "Profit before tax",
                "Profit before Tax",
            ],
        )
    )

    interest = _to_float(
        _get(pnl_row, ["Interest"])
    )

    if profit_before_tax is None:
        return None

    return profit_before_tax + (interest or 0)


def _retained_earnings(pnl_row):

    net_profit = _to_float(
        _get(
            pnl_row,
            [
                "Net Profit",
                "Net profit",
            ],
        )
    )

    dividend_payout_percent = _to_float(
        _get(
            pnl_row,
            ["Dividend Payout %"],
        )
    )

    if (
        net_profit is None
        or dividend_payout_percent is None
    ):
        return None

    return net_profit - (
        net_profit * dividend_payout_percent / 100
    )


def _market_value_of_equity(pnl_row, latest_price):

    net_profit = _to_float(
        _get(
            pnl_row,
            [
                "Net Profit",
                "Net profit",
            ],
        )
    )

    eps = _to_float(
        _get(
            pnl_row,
            [
                "EPS in Rs",
                "EPS",
            ],
        )
    )

    latest_price = _to_float(latest_price)

    if (
        net_profit is None
        or eps in (None, 0)
        or latest_price is None
    ):
        return None

    shares_outstanding = net_profit / eps

    return shares_outstanding * latest_price


# ==================================================
# Beneish M-Score helpers
# ==================================================


def _trade_receivables(bs_row):

    return _to_float(
        _get(
            bs_row,
            [
                "Trade Receivables",
                "Trade receivables",
                "Trade Receivable",
                "Trade receivable",
                "Accounts Receivable",
                "Accounts receivable",
            ],
        )
    )


def _percentage_fraction(value):

    value = _to_float(value)

    if value is None:
        return None

    return value / 100


def _material_cost_fraction(pnl_row):

    return _percentage_fraction(
        _get(
            pnl_row,
            [
                "Material Cost %",
                "Material cost %",
                "Material Cost",
                "Material cost",
            ],
        )
    )


def _manufacturing_cost_fraction(pnl_row):

    return _percentage_fraction(
        _get(
            pnl_row,
            [
                "Manufacturing Cost %",
                "Manufacturing cost %",
                "Manufacturing Cost",
                "Manufacturing cost",
            ],
        )
    )


def _gross_margin_rate(pnl_row):

    material_cost = _material_cost_fraction(
        pnl_row
    )

    manufacturing_cost = _manufacturing_cost_fraction(
        pnl_row
    )

    if (
        material_cost is None
        or manufacturing_cost is None
    ):
        return None

    cogs_rate = (
        material_cost + manufacturing_cost
    )

    return 1 - cogs_rate


def _sg_and_a_expenses(pnl_row):

    expenses = _to_float(
        _get(
            pnl_row,
            ["Expenses"],
        )
    )

    sales = _to_float(
        _get(
            pnl_row,
            [
                "Sales",
                "Revenue",
            ],
        )
    )

    material_cost = _material_cost_fraction(
        pnl_row
    )

    manufacturing_cost = _manufacturing_cost_fraction(
        pnl_row
    )

    if None in (
        expenses,
        sales,
        material_cost,
        manufacturing_cost,
    ):
        return None

    cogs = sales * (
        material_cost + manufacturing_cost
    )

    return expenses - cogs


def _beneish_missing_inputs(
    pnl_row,
    prior_pnl_row,
    bs_row,
    prior_bs_row,
    cf_row,
):
    required = {
        "Trade Receivables": _trade_receivables(
            bs_row
        ),

        "Prior Trade Receivables": _trade_receivables(
            prior_bs_row
        ),

        "Sales": _to_float(
            _get(
                pnl_row,
                [
                    "Sales",
                    "Revenue",
                ],
            )
        ),

        "Prior Sales": _to_float(
            _get(
                prior_pnl_row,
                [
                    "Sales",
                    "Revenue",
                ],
            )
        ),

        "Gross Margin": _gross_margin_rate(
            pnl_row
        ),

        "Prior Gross Margin": _gross_margin_rate(
            prior_pnl_row
        ),

        "Total Assets": _total_assets(
            bs_row
        ),

        "Prior Total Assets": _total_assets(
            prior_bs_row
        ),

        "Fixed Assets": _to_float(
            _get(
                bs_row,
                ["Fixed Assets"],
            )
        ),

        "Prior Fixed Assets": _to_float(
            _get(
                prior_bs_row,
                ["Fixed Assets"],
            )
        ),

        "Depreciation": _to_float(
            _get(
                pnl_row,
                ["Depreciation"],
            )
        ),

        "Prior Depreciation": _to_float(
            _get(
                prior_pnl_row,
                ["Depreciation"],
            )
        ),

        "Net Profit": _to_float(
            _get(
                pnl_row,
                [
                    "Net Profit",
                    "Net profit",
                ],
            )
        ),

        "Prior Net Profit": _to_float(
            _get(
                prior_pnl_row,
                [
                    "Net Profit",
                    "Net profit",
                ],
            )
        ),

        "Cash from Operating Activity": _to_float(
            _get(
                cf_row,
                [
                    "Cash from Operating Activity",
                ],
            )
        ),

        "Expenses": _to_float(
            _get(
                pnl_row,
                ["Expenses"],
            )
        ),

        "Prior Expenses": _to_float(
            _get(
                prior_pnl_row,
                ["Expenses"],
            )
        ),

        "Material Cost %": _material_cost_fraction(
            pnl_row
        ),

        "Prior Material Cost %": _material_cost_fraction(
            prior_pnl_row
        ),

        "Manufacturing Cost %": _manufacturing_cost_fraction(
            pnl_row
        ),

        "Prior Manufacturing Cost %": _manufacturing_cost_fraction(
            prior_pnl_row
        ),

        "Total Liabilities": _total_liabilities(
            bs_row
        ),

        "Prior Total Liabilities": _total_liabilities(
            prior_bs_row
        ),
    }

    return [
        name
        for name, value in required.items()
        if value is None
    ]


def compute_beneish_m(
    pnl_row,
    prior_pnl_row,
    bs_row,
    prior_bs_row,
    cf_row,
):
    if (
        pnl_row is None
        or prior_pnl_row is None
        or bs_row is None
        or prior_bs_row is None
        or cf_row is None
    ):
        return {
            "score": None,
            "verdict": None,
            "severity": None,
            "note": "Not Available",
        }

    missing = _beneish_missing_inputs(
        pnl_row,
        prior_pnl_row,
        bs_row,
        prior_bs_row,
        cf_row,
    )

    if missing:
        return {
            "score": None,
            "verdict": None,
            "severity": None,
            "note": "Not Available",
        }

    sales = _to_float(
        _get(
            pnl_row,
            [
                "Sales",
                "Revenue",
            ],
        )
    )

    prior_sales = _to_float(
        _get(
            prior_pnl_row,
            [
                "Sales",
                "Revenue",
            ],
        )
    )

    receivables = _trade_receivables(
        bs_row
    )

    prior_receivables = _trade_receivables(
        prior_bs_row
    )

    gross_margin = _gross_margin_rate(
        pnl_row
    )

    prior_gross_margin = _gross_margin_rate(
        prior_pnl_row
    )

    total_assets = _total_assets(
        bs_row
    )

    prior_total_assets = _total_assets(
        prior_bs_row
    )

    fixed_assets = _to_float(
        _get(
            bs_row,
            ["Fixed Assets"],
        )
    )

    prior_fixed_assets = _to_float(
        _get(
            prior_bs_row,
            ["Fixed Assets"],
        )
    )

    depreciation = _to_float(
        _get(
            pnl_row,
            ["Depreciation"],
        )
    )

    prior_depreciation = _to_float(
        _get(
            prior_pnl_row,
            ["Depreciation"],
        )
    )

    net_profit = _to_float(
        _get(
            pnl_row,
            [
                "Net Profit",
                "Net profit",
            ],
        )
    )

    cash_from_operating = _to_float(
        _get(
            cf_row,
            [
                "Cash from Operating Activity",
            ],
        )
    )

    sg_and_a = _sg_and_a_expenses(
        pnl_row
    )

    prior_sg_and_a = _sg_and_a_expenses(
        prior_pnl_row
    )

    liabilities = _total_liabilities(
        bs_row
    )

    prior_liabilities = _total_liabilities(
        prior_bs_row
    )

    denominators = (
        prior_sales,
        sales,
        prior_gross_margin,
        gross_margin,
        total_assets,
        prior_total_assets,
        fixed_assets + depreciation,
        prior_fixed_assets + prior_depreciation,
        sg_and_a,
        prior_sg_and_a,
        liabilities,
        prior_liabilities,
    )

    if any(
        value in (None, 0)
        for value in denominators
    ):
        return {
            "score": None,
            "verdict": None,
            "severity": None,
            "note": "Not Available",
        }

    dsri = (
        receivables / sales
    ) / (
        prior_receivables / prior_sales
    )

    gmi = (
        prior_gross_margin / gross_margin
    )

    current_asset_quality = (
        1 - (
            (
                _current_assets(bs_row)
                + fixed_assets
            ) / total_assets
        )
    )

    prior_asset_quality = (
        1 - (
            (
                _current_assets(prior_bs_row)
                + prior_fixed_assets
            ) / prior_total_assets
        )
    )

    if prior_asset_quality == 0:
        return {
            "score": None,
            "verdict": None,
            "severity": None,
            "note": "Not Available",
        }

    aqi = (
        current_asset_quality
        / prior_asset_quality
    )

    sgi = sales / prior_sales

    depi = (
        prior_depreciation
        / (
            prior_depreciation
            + prior_fixed_assets
        )
    ) / (
        depreciation
        / (
            depreciation
            + fixed_assets
        )
    )

    sgai = (
        sg_and_a / sales
    ) / (
        prior_sg_and_a / prior_sales
    )

    tata = (
        net_profit - cash_from_operating
    ) / total_assets

    lvgi = (
        liabilities / total_assets
    ) / (
        prior_liabilities / prior_total_assets
    )

    score = (
        -4.84
        + 0.92 * dsri
        + 0.528 * gmi
        + 0.404 * aqi
        + 0.892 * sgi
        + 0.115 * depi
        - 0.172 * sgai
        + 4.679 * tata
        - 0.327 * lvgi
    )

    if score <= -2.22:
        verdict = "High earnings quality"
        severity = "positive"
    else:
        verdict = (
            "High probability of accounting manipulation"
        )
        severity = "negative"

    return {
        "score": round(score, 3),
        "verdict": verdict,
        "severity": severity,
        "note": None,
        "ratios": {
            "dsri": round(dsri, 3),
            "gmi": round(gmi, 3),
            "aqi": round(aqi, 3),
            "sgi": round(sgi, 3),
            "depi": round(depi, 3),
            "sgai": round(sgai, 3),
            "tata": round(tata, 3),
            "lvgi": round(lvgi, 3),
        },
    }


# ==================================================
# A. Altman Z-Score
# ==================================================


def compute_altman_z(
    pnl_row,
    bs_row,
    latest_price,
):

    total_assets = _total_assets(
        bs_row
    )

    total_liabilities = _total_liabilities(
        bs_row
    )

    working_capital = _working_capital(
        bs_row
    )

    ebit = _ebit(
        pnl_row
    )

    sales = _to_float(
        _get(
            pnl_row,
            [
                "Sales",
                "Revenue",
            ],
        )
    )

    retained_earnings = _retained_earnings(
        pnl_row
    )

    market_value_of_equity = _market_value_of_equity(
        pnl_row,
        latest_price,
    )

    missing = []

    if total_assets in (None, 0):
        missing.append("Total Assets")

    if total_liabilities in (None, 0):
        missing.append("Total Liabilities")

    if working_capital is None:
        missing.append(
            "Working Capital "
            "(Other Assets / Other Liabilities)"
        )

    if ebit is None:
        missing.append(
            "EBIT (Profit before Tax / Interest)"
        )

    if sales is None:
        missing.append("Sales")

    if retained_earnings is None:
        missing.append(
            "Retained Earnings "
            "(Net Profit / Dividend Payout %)"
        )

    if market_value_of_equity is None:
        missing.append(
            "Market Value of Equity "
            "(EPS / current price)"
        )

    if missing:
        return {
            "score": None,
            "zone": None,
            "severity": None,
            "note": "Not Available",        
            }

    x1 = working_capital / total_assets
    x2 = retained_earnings / total_assets
    x3 = ebit / total_assets
    x4 = market_value_of_equity / total_liabilities
    x5 = sales / total_assets

    z = (
        1.2 * x1
        + 1.4 * x2
        + 3.3 * x3
        + 0.6 * x4
        + 1.0 * x5
    )

    if z > 2.99:
        zone = "Safe Zone"
        severity = "positive"

    elif z >= 1.81:
        zone = "Grey Zone"
        severity = "mixed"

    else:
        zone = "Distress Zone"
        severity = "negative"

    return {
        "score": round(z, 2),
        "zone": zone,
        "severity": severity,
        "note": None,
    }


# ==================================================
# B. Piotroski F-Score
# ==================================================


def compute_piotroski_f(
    pnl_row,
    prior_pnl_row,
    bs_row,
    prior_bs_row,
    cf_row,
):

    if (
        prior_pnl_row is None
        or prior_bs_row is None
    ):
        return {
            "score": None,
            "max_score": 9,
            "severity": None,
            "note": "Not Available",
        }

    points = 0

    net_profit = _to_float(
        _get(
            pnl_row,
            [
                "Net Profit",
                "Net profit",
            ],
        )
    )

    total_assets = _total_assets(
        bs_row
    )

    cfo = (
        _to_float(
            _get(
                cf_row,
                [
                    "Cash from Operating Activity",
                ],
            )
        )
        if cf_row
        else None
    )

    if (
        net_profit is not None
        and net_profit > 0
    ):
        points += 1

    if (
        net_profit is not None
        and total_assets not in (None, 0)
        and net_profit / total_assets > 0
    ):
        points += 1

    if cfo is not None and cfo > 0:
        points += 1

    if (
        cfo is not None
        and net_profit is not None
        and cfo > net_profit
    ):
        points += 1

    borrowings = _to_float(
        _get(
            bs_row,
            ["Borrowings"],
        )
    )

    prior_borrowings = _to_float(
        _get(
            prior_bs_row,
            ["Borrowings"],
        )
    )

    prior_total_assets = _total_assets(
        prior_bs_row
    )

    if (
        None not in (
            borrowings,
            prior_borrowings,
            total_assets,
            prior_total_assets,
        )
        and total_assets
        and prior_total_assets
    ):
        if (
            borrowings / total_assets
            < prior_borrowings / prior_total_assets
        ):
            points += 1

    current_assets = _current_assets(
        bs_row
    )

    current_liabilities = _current_liabilities(
        bs_row
    )

    prior_current_assets = _current_assets(
        prior_bs_row
    )

    prior_current_liabilities = _current_liabilities(
        prior_bs_row
    )

    if (
        None not in (
            current_assets,
            current_liabilities,
            prior_current_assets,
            prior_current_liabilities,
        )
        and current_liabilities
        and prior_current_liabilities
    ):
        if (
            current_assets / current_liabilities
            > prior_current_assets / prior_current_liabilities
        ):
            points += 1

    equity_capital = _to_float(
        _get(
            bs_row,
            ["Equity Capital"],
        )
    )

    prior_equity_capital = _to_float(
        _get(
            prior_bs_row,
            ["Equity Capital"],
        )
    )

    if (
        equity_capital is not None
        and prior_equity_capital is not None
        and equity_capital <= prior_equity_capital
    ):
        points += 1

    # Criterion 8 (Gross Margin YoY) always scores 0.

    sales = _to_float(
        _get(
            pnl_row,
            [
                "Sales",
                "Revenue",
            ],
        )
    )

    prior_sales = _to_float(
        _get(
            prior_pnl_row,
            [
                "Sales",
                "Revenue",
            ],
        )
    )

    if (
        None not in (
            sales,
            prior_sales,
            total_assets,
            prior_total_assets,
        )
        and total_assets
        and prior_total_assets
    ):
        if (
            sales / total_assets
            > prior_sales / prior_total_assets
        ):
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
        "note": None,
    }


# ==================================================
# D. Ohlson O-Score
# ==================================================


def compute_ohlson_o(
    pnl_row,
    prior_pnl_row,
    bs_row,
    cf_row,
):

    total_assets = _total_assets(
        bs_row
    )

    total_liabilities = _total_liabilities(
        bs_row
    )

    working_capital = _working_capital(
        bs_row
    )

    current_assets = _current_assets(
        bs_row
    )

    current_liabilities = _current_liabilities(
        bs_row
    )

    net_income = _to_float(
        _get(
            pnl_row,
            [
                "Net Profit",
                "Net profit",
            ],
        )
    )

    cfo = (
        _to_float(
            _get(
                cf_row,
                [
                    "Cash from Operating Activity",
                ],
            )
        )
        if cf_row
        else None
    )

    required = [
        total_assets,
        total_liabilities,
        working_capital,
        current_assets,
        current_liabilities,
        net_income,
        cfo,
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
            "note": "Not Available",
        }

    prior_net_income = None

    if prior_pnl_row is not None:
        prior_net_income = _to_float(
            _get(
                prior_pnl_row,
                [
                    "Net Profit",
                    "Net profit",
                ],
            )
        )

    oeneg = int(
        total_liabilities > total_assets
    )

    intwo = 0

    if (
        net_income is not None
        and prior_net_income is not None
        and net_income < 0
        and prior_net_income < 0
    ):
        intwo = 1

    chin = 0

    if (
        net_income is not None
        and prior_net_income is not None
    ):
        denominator = (
            abs(net_income)
            + abs(prior_net_income)
        )

        if denominator:
            chin = (
                net_income - prior_net_income
            ) / denominator

    try:

        t_score = (
            -1.32
            - 0.407 * math.log(total_assets)
            + 6.03 * (
                total_liabilities / total_assets
            )
            - 1.43 * (
                working_capital / total_assets
            )
            + 0.0757 * (
                current_liabilities / current_assets
            )
            - 1.72 * oeneg
            - 2.37 * (
                net_income / total_assets
            )
            + 0.285 * (
                cfo / total_liabilities
            )
            - 1.72 * intwo
            - 0.521 * chin
        )

        probability = math.exp(t_score) / (
            1 + math.exp(t_score)
        )

    except (
        ValueError,
        OverflowError,
        ZeroDivisionError,
    ):
        return {
            "score": None,
            "probability": None,
            "severity": None,
            "note": "Not Available",
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
        "note": None,
    }


# ==================================================
# E. Springate S-Score
# ==================================================


def compute_springate_s(
    pnl_row,
    bs_row,
):

    total_assets = _total_assets(
        bs_row
    )

    working_capital = _working_capital(
        bs_row
    )

    ebit = _ebit(
        pnl_row
    )

    profit_before_tax = _to_float(
        _get(
            pnl_row,
            [
                "Profit before tax",
                "Profit before Tax",
            ],
        )
    )

    current_liabilities = _current_liabilities(
        bs_row
    )

    sales = _to_float(
        _get(
            pnl_row,
            [
                "Sales",
                "Revenue",
            ],
        )
    )

    required = [
        total_assets,
        working_capital,
        ebit,
        profit_before_tax,
        current_liabilities,
        sales,
    ]

    if (
        any(value is None for value in required)
        or total_assets in (None, 0)
        or current_liabilities in (None, 0)
    ):
        return {
            "score": None,
            "verdict": None,
            "severity": None,
            "note": "Not Available",
        }

    a = working_capital / total_assets
    b = ebit / total_assets
    c = profit_before_tax / current_liabilities
    d = sales / total_assets

    score = (
        1.03 * a
        + 3.07 * b
        + 0.66 * c
        + 0.4 * d
    )

    if score > 0.862:
        verdict = "Healthy"
        severity = "positive"

    else:
        verdict = "Financial distress warning"
        severity = "negative"

    return {
        "score": round(score, 3),
        "verdict": verdict,
        "severity": severity,
        "note": None,
    }


# ==================================================
# F. Zmijewski X-Score
# ==================================================


def compute_zmijewski_x(
    pnl_row,
    bs_row,
):

    total_assets = _total_assets(
        bs_row
    )

    total_liabilities = _total_liabilities(
        bs_row
    )

    net_income = _to_float(
        _get(
            pnl_row,
            [
                "Net Profit",
                "Net profit",
            ],
        )
    )

    current_assets = _current_assets(
        bs_row
    )

    current_liabilities = _current_liabilities(
        bs_row
    )

    required = [
        total_assets,
        total_liabilities,
        net_income,
        current_assets,
        current_liabilities,
    ]

    if (
        any(value is None for value in required)
        or total_assets in (None, 0)
        or current_liabilities in (None, 0)
    ):
        return {
            "score": None,
            "verdict": None,
            "severity": None,
            "note": "Not Available",
        }

    score = (
        -4.336
        - 4.513 * (
            net_income / total_assets
        )
        + 5.679 * (
            total_liabilities / total_assets
        )
        + 0.004 * (
            current_assets / current_liabilities
        )
    )

    if score > 0:
        verdict = "High distress profile"
        severity = "negative"

    else:
        verdict = "Solid buffer profile"
        severity = "positive"

    return {
        "score": round(score, 3),
        "verdict": verdict,
        "severity": severity,
        "note": None,
    }


# ==================================================
# Build all scores
# ==================================================


def build_distress_scores(
    profit_loss_records,
    balance_sheet_records,
    cash_flow_records,
    latest_price,
):

    pnl_pivoted = pivot_by_period(
        profit_loss_records
    )

    bs_pivoted = pivot_by_period(
        balance_sheet_records
    )

    cf_pivoted = pivot_by_period(
        cash_flow_records
    )

    pnl_row, prior_pnl_row = _latest_two_periods(
        pnl_pivoted
    )

    bs_row, prior_bs_row = _latest_two_periods(
        bs_pivoted
    )

    cf_row, _ = _latest_two_periods(
        cf_pivoted
    )

    if pnl_row is None or bs_row is None:

        empty_note = "Not Available"

        return {
            "altman_z": {
                "score": None,
                "zone": None,
                "severity": None,
                "note": empty_note,
            },
            "piotroski_f": {
                "score": None,
                "max_score": 9,
                "severity": None,
                "note": empty_note,
            },
            "beneish_m": {
                "score": None,
                "verdict": None,
                "severity": None,
                "note": empty_note,
            },
            "ohlson_o": {
                "score": None,
                "probability": None,
                "severity": None,
                "note": empty_note,
            },
            "springate_s": {
                "score": None,
                "verdict": None,
                "severity": None,
                "note": empty_note,
            },
            "zmijewski_x": {
                "score": None,
                "verdict": None,
                "severity": None,
                "note": empty_note,
            },
        }

    return {
        "altman_z": compute_altman_z(
            pnl_row,
            bs_row,
            latest_price,
        ),
        "piotroski_f": compute_piotroski_f(
            pnl_row,
            prior_pnl_row,
            bs_row,
            prior_bs_row,
            cf_row,
        ),
        "beneish_m": compute_beneish_m(
            pnl_row,
            prior_pnl_row,
            bs_row,
            prior_bs_row,
            cf_row,
        ),
        "ohlson_o": compute_ohlson_o(
            pnl_row,
            prior_pnl_row,
            bs_row,
            cf_row,
        ),
        "springate_s": compute_springate_s(
            pnl_row,
            bs_row,
        ),
        "zmijewski_x": compute_zmijewski_x(
            pnl_row,
            bs_row,
        ),
    }