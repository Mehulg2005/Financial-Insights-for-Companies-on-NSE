from utils.pivot import pivot_by_period
from utils.features import _get


# ==================================================
# CONFIG
#
# All thresholds and rules used by the trend analyser
# live here in one place, so they can be reviewed and
# tuned by the team without hunting through logic code.
#
# This is a first-draft rule set (Phase 1). It has not
# yet been validated across multiple companies (Phase 2)
# or reviewed against real trading judgement - treat the
# specific numbers below as a starting point, not gospel.
# ==================================================

TREND_WINDOW_PERIODS = 7
# The analyser only looks at the most recent N periods of
# each company's data, so old/stale history doesn't dilute
# a company's recent trajectory. If a company has fewer
# than N periods available, all of them are used.

MIN_PERIODS_FOR_TREND = 3
# Need at least this many periods to call something a
# "trend" - with 2 points, any single move looks like one.

MAX_OPPOSING_STEPS = 2
# Number of period-over-period steps allowed to move the
# "wrong" way (or stay flat) and still call the overall
# trend "improving" or "declining" - i.e. the number of
# tolerated blips. Anything beyond this, or a series with
# no clear majority direction, is "mixed".
#
# Note: this is a pure count, not a ratio. An earlier
# version combined a 70%-of-steps ratio with a blip count,
# but the two don't stay compatible as the window size
# changes (e.g. tolerating 2 blips out of only 6 steps is
# mathematically incompatible with also requiring 70% of
# steps to agree). The majority check below
# (up_steps > down_steps) is what prevents the blip
# allowance from swallowing the actual signal when there
# are very few steps to look at.

CASH_CONVERSION_ALIGNED_BAND = 0.25
# Cash Conversion (CFO / Net Profit) is considered
# "aligned" with profit if it stays within +/-25% of 1.0
# (i.e. between 0.75x and 1.25x) on average across the
# trend window.

CASH_CONVERSION_DIVERGED_BAND = 0.40
# Beyond this average deviation from 1.0, cash flow is
# considered meaningfully diverged from reported profit.

INVESTMENT_MIGRATION_STABLE_POINTS = 5.0
# Investment Migration is Investments as a % of Total
# Assets. A change of less than this many percentage
# points across the trend window is considered "stable"
# allocation. Larger shifts get checked against the
# Growth verdict for context (see _evaluate_capital_allocation)
# rather than judged on their own.

# --------------------------------------------------
# Rollup weights.
#
# Profitability and Growth each combine one "headline"
# metric with one "quality check" metric. The headline
# metric is weighted more heavily, so a quality-check
# metric moving the opposite way produces a lean rather
# than automatically forcing MIXED. The quality-check
# signal is NOT hidden - it still shows up as its own
# bullet - it just doesn't override the headline number
# outright.
# --------------------------------------------------

PROFITABILITY_PAT_WEIGHT = 2       # headline: PAT level
PROFITABILITY_MARGIN_WEIGHT = 1    # quality check: Operating Margin
PROFITABILITY_EPS_WEIGHT = 1       # quality check: EPS (dilution check)

GROWTH_REVENUE_WEIGHT = 2          # headline: Revenue level
GROWTH_PAT_RATE_WEIGHT = 1         # quality check: PAT growth rate

LEVERAGE_BORROWINGS_WEIGHT = 2     # headline: Borrowings-to-Net-Worth
LEVERAGE_COVERAGE_WEIGHT = 1       # quality check: Interest Coverage Ratio

# ==================================================
# Low-level trend helpers
# ==================================================

def _last_n_periods(pivoted_rows, window_size):
    """
    Restrict a chronologically-ordered list of pivoted
    period rows to just the most recent `window_size`
    periods, so the trend analyser reacts to a company's
    recent trajectory rather than being diluted by
    conditions from many years ago.

    If fewer periods than window_size are available, all
    of them are used (Python's slicing handles this
    automatically) - MIN_PERIODS_FOR_TREND still applies
    on top of this, so sparse data is correctly reported
    as "insufficient data" rather than guessed at.
    """

    if window_size is None or window_size <= 0:
        return pivoted_rows

    return pivoted_rows[-window_size:]


def _series(pivoted_rows, names):
    """
    Extract a chronological list of values for a metric
    (trying each candidate name) across pivoted period
    rows, skipping periods where it's missing.

    pivoted_rows are assumed to already be in chronological
    (oldest -> newest) order, matching pivot_by_period's
    output and how the rest of the app treats period order.
    """

    values = []

    for row in pivoted_rows:

        value = _get(row, names)

        if value is not None:
            values.append(value)

    return values


def _step_directions(values):
    """
    Given a chronological list of numeric values, return
    one direction per consecutive pair:
        +1 -> increased
         0 -> unchanged
        -1 -> decreased
    """

    directions = []

    for previous, current in zip(values, values[1:]):

        if current > previous:
            directions.append(1)
        elif current < previous:
            directions.append(-1)
        else:
            directions.append(0)

    return directions


def _classify_direction(values, higher_is_better=True):
    """
    Classify a chronological series of values as
    "improving", "declining", or "mixed", from the
    perspective of "is this a good outcome"
    (controlled by higher_is_better).

    Rule: no more than MAX_OPPOSING_STEPS steps are allowed
    to move the "wrong" way (or stay flat) - AND there must
    be a genuine majority in one direction (up_steps must
    strictly outnumber down_steps, or vice versa). The
    majority check exists so the blip allowance can't turn
    a short, mostly-declining series into a false
    "improving" read just because there aren't enough
    steps for the blip count to mean much.

    Returns "insufficient_data" if there aren't enough
    periods to say anything meaningful.
    """

    if len(values) < MIN_PERIODS_FOR_TREND:
        return "insufficient_data"

    directions = _step_directions(values)

    if not higher_is_better:
        directions = [-direction for direction in directions]

    total_steps = len(directions)
    up_steps = directions.count(1)
    down_steps = directions.count(-1)

    non_up_steps = total_steps - up_steps
    non_down_steps = total_steps - down_steps

    if non_up_steps <= MAX_OPPOSING_STEPS and up_steps > down_steps:
        return "improving"

    if non_down_steps <= MAX_OPPOSING_STEPS and down_steps > up_steps:
        return "declining"

    return "mixed"


def _growth_rates(values):
    """
    Convert a chronological list of raw values into
    period-over-period % growth rates. The first value
    has no prior period to compare to, so the result has
    one fewer entry than the input.

    Returns None for any step where % growth is undefined
    (prior value missing or zero) - callers should filter
    these out before classifying.
    """

    rates = []

    for previous, current in zip(values, values[1:]):

        if previous in (None, 0) or current is None:
            rates.append(None)
            continue

        rates.append(
            ((current - previous) / abs(previous)) * 100
        )

    return rates


def _trend_bullet(label, trend, improving_word, declining_word):
    """
    Turn a trend classification into a human-readable
    bullet. improving_word / declining_word are the verbs
    to use for a good / bad outcome respectively
    (e.g. "increased" / "declined").
    """

    if trend == "improving":
        return f"{label} {improving_word} consistently."

    if trend == "declining":
        return f"{label} {declining_word} consistently."

    if trend == "mixed":
        return f"{label} trend was inconsistent period to period."

    if trend == "insufficient_data":
        return f"{label}: not enough periods of data to assess a trend."

    return None


def _pat_level_bullet(trend):
    """
    Profitability's PAT bullet. Explicitly says "level" so
    it can't be confused with Growth's PAT growth-RATE
    bullet below, even though both derive from the same
    underlying Net Profit numbers.
    """

    if trend == "improving":
        return "PAT level rose consistently year over year."

    if trend == "declining":
        return "PAT level fell consistently year over year."

    if trend == "mixed":
        return "PAT level moved inconsistently period to period."

    if trend == "insufficient_data":
        return "PAT level: not enough periods of data to assess a trend."

    return None


def _pat_growth_rate_bullet(trend):
    """
    Growth's PAT bullet - about the PACE of change (the
    growth rate), not the level. A company's PAT level can
    rise every single year while its growth rate still
    bounces around (e.g. +40%, +5%, +25%, +8%) - both are
    true statements about the same numbers, so the mixed
    case spells this out explicitly to avoid the two
    bullets reading as contradictory.
    """

    if trend == "improving":
        return "PAT growth rate accelerated consistently (profit is not just rising, but rising faster each period)."

    if trend == "declining":
        return "PAT growth rate decelerated consistently (profit is still rising, but at a slowing pace)."

    if trend == "mixed":
        return (
            "PAT's growth rate fluctuated year to year - the profit "
            "level still moved as noted under Profitability, but the "
            "pace of that change was inconsistent."
        )

    if trend == "insufficient_data":
        return "PAT growth rate: not enough periods of data to assess a trend."

    return None


def _eps_bullet(net_profit_trend, eps_trend):
    """
    EPS bullet for Profitability. Framed as a dilution
    check: if PAT (level) is rising but EPS isn't keeping
    pace, that's a sign new shares have been issued faster
    than profit has grown - each existing share is worth a
    smaller slice of a bigger pie. This is the specific
    insight EPS adds that PAT level alone can't show.
    """

    if eps_trend == "insufficient_data":
        return "EPS: not enough periods of data to assess a trend."

    if eps_trend == "improving":
        return "EPS increased consistently."

    if net_profit_trend == "improving" and eps_trend != "improving":
        return (
            "EPS did not rise in step with PAT - worth checking "
            "for share dilution."
        )

    if eps_trend == "declining":
        return "EPS declined consistently."

    return "EPS trend was inconsistent period to period."


def _rollup(trends):
    """
    Roll up a list of per-metric trend classifications
    ("improving" / "declining" / "mixed" /
    "insufficient_data") into one category verdict,
    requiring unanimous agreement. Used where there's
    only a single metric driving the category (Leverage),
    where "unanimous" and "majority" are the same thing.
    """

    normalized = [
        "mixed" if trend == "insufficient_data" else trend
        for trend in trends
    ]

    if all(trend == "improving" for trend in normalized):
        return "POSITIVE"

    if all(trend == "declining" for trend in normalized):
        return "NEGATIVE"

    return "MIXED"


def _rollup_weighted(weighted_trends):
    """
    Roll up (trend, weight) pairs into one verdict by
    scoring each trend (+weight for improving, -weight for
    declining, 0 for mixed/insufficient_data) and summing.
    A positive total leans POSITIVE, negative leans
    NEGATIVE, exactly zero (including a tie between two
    equally-weighted opposing signals) is MIXED.

    This is what lets a heavily-weighted headline metric
    outvote a lighter-weighted quality-check metric moving
    the other way, instead of any disagreement forcing
    MIXED outright.
    """

    score = 0

    for trend, weight in weighted_trends:

        normalized = "mixed" if trend == "insufficient_data" else trend

        if normalized == "improving":
            score += weight
        elif normalized == "declining":
            score -= weight

    if score > 0:
        return "POSITIVE"

    if score < 0:
        return "NEGATIVE"

    return "MIXED"


# ==================================================
# Profitability
#   - PAT level trend (headline)
#   - Operating Margin trend (quality check)
# ==================================================

def _evaluate_profitability(pnl_pivoted):

    net_profit_series = _series(pnl_pivoted, ["Net Profit", "Net profit"])
    sales_series = _series(pnl_pivoted, ["Sales", "Revenue"])
    operating_profit_series = _series(pnl_pivoted, ["Operating Profit"])
    eps_series = _series(pnl_pivoted, ["EPS in Rs", "EPS"])

    margin_series = [
        (operating_profit / sales) * 100
        for sales, operating_profit in zip(sales_series, operating_profit_series)
        if sales
    ]

    net_profit_trend = _classify_direction(net_profit_series, higher_is_better=True)
    margin_trend = _classify_direction(margin_series, higher_is_better=True)
    eps_trend = _classify_direction(eps_series, higher_is_better=True)

    bullets = [
        _pat_level_bullet(net_profit_trend),
        _trend_bullet("Operating Margin", margin_trend, "improved", "worsened"),
        _eps_bullet(net_profit_trend, eps_trend),
    ]

    verdict = _rollup_weighted([
        (net_profit_trend, PROFITABILITY_PAT_WEIGHT),
        (margin_trend, PROFITABILITY_MARGIN_WEIGHT),
        (eps_trend, PROFITABILITY_EPS_WEIGHT),
    ])

    return {
        "category": "Profitability",
        "verdict": verdict,
        "bullets": [bullet for bullet in bullets if bullet]
    }


# ==================================================
# Growth
#   - Revenue (Sales) level trend (headline)
#   - PAT growth-rate trend (quality check - is growth
#     accelerating, not just the level of PAT, which
#     Profitability already covers above)
# ==================================================

def _evaluate_growth(pnl_pivoted):

    sales_series = _series(pnl_pivoted, ["Sales", "Revenue"])
    net_profit_series = _series(pnl_pivoted, ["Net Profit", "Net profit"])

    sales_trend = _classify_direction(sales_series, higher_is_better=True)

    pat_growth_rates = [
        rate for rate in _growth_rates(net_profit_series)
        if rate is not None
    ]
    pat_growth_trend = _classify_direction(pat_growth_rates, higher_is_better=True)

    bullets = [
        _trend_bullet("Revenue", sales_trend, "increased", "declined"),
        _pat_growth_rate_bullet(pat_growth_trend),
    ]

    verdict = _rollup_weighted([
        (sales_trend, GROWTH_REVENUE_WEIGHT),
        (pat_growth_trend, GROWTH_PAT_RATE_WEIGHT),
    ])

    return {
        "category": "Growth",
        "verdict": verdict,
        "bullets": [bullet for bullet in bullets if bullet]
    }


# ==================================================
# Cash Flow
#   - Is CFO staying aligned with reported PAT, on
#     average, across the trend window?
# ==================================================

def _evaluate_cash_flow(cf_pivoted, pnl_pivoted):

    pnl_by_period = {
        row["period"]: row
        for row in pnl_pivoted
    }

    ratios = []

    for row in cf_pivoted:

        cash_from_operating = _get(row, ["Cash from Operating Activity"])
        pnl_row = pnl_by_period.get(row["period"], {})
        net_profit = _get(pnl_row, ["Net Profit", "Net profit"])

        if cash_from_operating is not None and net_profit not in (None, 0):
            ratios.append(cash_from_operating / net_profit)

    if len(ratios) < MIN_PERIODS_FOR_TREND:

        return {
            "category": "Cash Flow",
            "verdict": "MIXED",
            "bullets": ["Not enough periods of data to assess cash flow quality."]
        }

    average_deviation = sum(abs(ratio - 1) for ratio in ratios) / len(ratios)

    if average_deviation <= CASH_CONVERSION_ALIGNED_BAND:

        return {
            "category": "Cash Flow",
            "verdict": "POSITIVE",
            "bullets": ["CFO remained aligned with PAT across the trend window."]
        }

    if average_deviation >= CASH_CONVERSION_DIVERGED_BAND:

        return {
            "category": "Cash Flow",
            "verdict": "NEGATIVE",
            "bullets": ["CFO diverged meaningfully from PAT - reported profit is not consistently backed by cash."]
        }

    return {
        "category": "Cash Flow",
        "verdict": "MIXED",
        "bullets": ["CFO was only loosely aligned with PAT."]
    }


# ==================================================
# Leverage
#   - Borrowings-to-Net-Worth trend (lower is better)
# ==================================================

def _evaluate_leverage(bs_pivoted, pnl_pivoted):

    ratio_series = []

    for row in bs_pivoted:

        equity_capital = _get(row, ["Equity Capital"])
        reserves = _get(row, ["Reserves"])
        borrowings = _get(row, ["Borrowings"])

        net_worth = None

        if equity_capital is not None or reserves is not None:
            net_worth = (equity_capital or 0) + (reserves or 0)

        if borrowings is not None and net_worth:
            ratio_series.append(borrowings / net_worth)

    # lower is better here - a declining ratio is the
    # "improving" outcome

    borrowings_trend = _classify_direction(ratio_series, higher_is_better=False)

    # --------------------------------------------------
    # Interest Coverage Ratio = Operating Profit / Interest.
    # Both fields live on the P&L, so no cross-statement
    # join is needed here (unlike Cash Flow, which genuinely
    # needs to match CFO against PAT across two statements).
    # --------------------------------------------------

    coverage_series = []

    for row in pnl_pivoted:

        operating_profit = _get(row, ["Operating Profit"])
        interest = _get(row, ["Interest"])

        if operating_profit is not None and interest not in (None, 0):
            coverage_series.append(operating_profit / interest)

    coverage_trend = _classify_direction(coverage_series, higher_is_better=True)

    bullets = [
        _trend_bullet("Borrowings-to-Net-Worth", borrowings_trend, "declined", "increased"),
        _trend_bullet("Interest Coverage Ratio", coverage_trend, "improved", "worsened"),
    ]

    verdict = _rollup_weighted([
        (borrowings_trend, LEVERAGE_BORROWINGS_WEIGHT),
        (coverage_trend, LEVERAGE_COVERAGE_WEIGHT),
    ])

    return {
        "category": "Leverage",
        "verdict": verdict,
        "bullets": [bullet for bullet in bullets if bullet]
    }


# ==================================================
# Capital Allocation
#   - How much has Investment Migration shifted across
#     the trend window? A stable ratio is POSITIVE. A
#     significant shift is checked against the Growth
#     verdict for context, rather than judged in
#     isolation:
#       increase + healthy growth   -> lean POSITIVE
#       increase + weak growth      -> lean NEGATIVE
#       decrease + weak growth      -> lean POSITIVE
#         (prudent tightening)
#       decrease + healthy growth   -> lean MIXED
#         (worth checking for under-investment)
#       growth context itself MIXED -> stays MIXED
#
#   This is a first-pass heuristic (Phase 1) - it isn't
#   trying to be a definitive judgement, just a better-
#   informed flag than "any big swing = MIXED".
# ==================================================

def _evaluate_capital_allocation(bs_pivoted, growth_verdict):

    migration_series = []

    for row in bs_pivoted:

        investments = _get(row, ["Investments"])
        total_assets = _get(row, ["Total Assets"])

        if investments is not None and total_assets:
            migration_series.append((investments / total_assets) * 100)

    if len(migration_series) < MIN_PERIODS_FOR_TREND:

        return {
            "category": "Capital Allocation",
            "verdict": "MIXED",
            "bullets": ["Not enough periods of data to assess investment allocation."]
        }

    change = migration_series[-1] - migration_series[0]

    if abs(change) < INVESTMENT_MIGRATION_STABLE_POINTS:

        return {
            "category": "Capital Allocation",
            "verdict": "POSITIVE",
            "bullets": ["Investment allocation (Investments as % of Total Assets) remained broadly stable."]
        }

    direction_word = "increased" if change > 0 else "decreased"
    swing_description = f"{direction_word} significantly ({abs(change):.1f} percentage points)"

    if change > 0 and growth_verdict == "POSITIVE":

        return {
            "category": "Capital Allocation",
            "verdict": "POSITIVE",
            "bullets": [
                f"Investment allocation {swing_description}, consistent with "
                f"the company's broader growth trend - likely deliberate "
                f"capacity expansion."
            ]
        }

    if change > 0 and growth_verdict == "NEGATIVE":

        return {
            "category": "Capital Allocation",
            "verdict": "NEGATIVE",
            "bullets": [
                f"Investment allocation {swing_description} despite a "
                f"weakening growth trend - raises capital discipline "
                f"concerns."
            ]
        }

    if change < 0 and growth_verdict == "NEGATIVE":

        return {
            "category": "Capital Allocation",
            "verdict": "POSITIVE",
            "bullets": [
                f"Investment allocation {swing_description} alongside a "
                f"weakening growth trend - consistent with prudent "
                f"capital discipline."
            ]
        }

    if change < 0 and growth_verdict == "POSITIVE":

        return {
            "category": "Capital Allocation",
            "verdict": "MIXED",
            "bullets": [
                f"Investment allocation {swing_description} despite a "
                f"healthy growth trend - worth checking whether the "
                f"company is under-investing for its growth trajectory."
            ]
        }

    return {
        "category": "Capital Allocation",
        "verdict": "MIXED",
        "bullets": [
            f"Investment allocation {swing_description} - this can "
            f"reflect a deliberate strategic shift or reduced capital "
            f"discipline, and needs closer review rather than a simple "
            f"good/bad call."
        ]
    }


# ==================================================
# Overall rollup
#
# First-draft rollup across the five categories into
# one Fundamental Aspect verdict. This is provisional
# for Phase 1/2 testing - it is NOT yet the final
# Fundamental + Technical combination logic (that's a
# later phase, and will use AND logic between the two
# aspects per the agreed approach).
# ==================================================

def _overall_verdict(categories):
    """
    First-draft rollup across the five categories into one
    Fundamental Aspect verdict. Provisional for Phase 1/2
    testing - not yet the final Fundamental + Technical
    combination logic (that's a later phase, using AND
    logic between the two aspects per the agreed approach).

    Rule:
      - 3 or more NEGATIVE categories is a hard veto -> NEGATIVE,
        regardless of how many categories are POSITIVE.
      - Otherwise, POSITIVE requires a margin of at least 2
        (positive_count - negative_count >= 2) - a single
        extra POSITIVE category isn't enough on its own to
        call the overall picture positive.
      - Anything else -> MIXED.

    This reduces to the same result as an explicit table of
    every positive/negative combination from (0,0) through
    (5,0) - it's written as two comparisons instead of a
    lookup table purely for readability.
    """

    verdicts = [category["verdict"] for category in categories]

    positive_count = verdicts.count("POSITIVE")
    negative_count = verdicts.count("NEGATIVE")

    if negative_count >= 3:
        return "NEGATIVE"

    if positive_count - negative_count >= 2:
        return "POSITIVE"

    return "MIXED"

# ==================================================
# Build full fundamental analysis
# ==================================================

def build_fundamental_analysis(
    profit_loss_records,
    balance_sheet_records,
    cash_flow_records
):

    pnl_pivoted = _last_n_periods(
        pivot_by_period(profit_loss_records),
        TREND_WINDOW_PERIODS
    )

    bs_pivoted = _last_n_periods(
        pivot_by_period(balance_sheet_records),
        TREND_WINDOW_PERIODS
    )

    cf_pivoted = _last_n_periods(
        pivot_by_period(cash_flow_records),
        TREND_WINDOW_PERIODS
    )

    profitability_result = _evaluate_profitability(pnl_pivoted)
    growth_result = _evaluate_growth(pnl_pivoted)
    cash_flow_result = _evaluate_cash_flow(cf_pivoted, pnl_pivoted)
    leverage_result = _evaluate_leverage(bs_pivoted, pnl_pivoted)

    # Capital Allocation needs Growth's verdict for context,
    # so it's computed after Growth rather than in parallel.

    capital_allocation_result = _evaluate_capital_allocation(
        bs_pivoted,
        growth_result["verdict"]
    )

    categories = [
        profitability_result,
        growth_result,
        cash_flow_result,
        leverage_result,
        capital_allocation_result,
    ]

    return {
        "categories": categories,
        "overall_verdict": _overall_verdict(categories)
    }