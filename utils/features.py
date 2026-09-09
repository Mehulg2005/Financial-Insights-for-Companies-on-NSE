from utils.pivot import pivot_by_period


# ==================================================
# Helpers
# ==================================================

def _get(period_row, names):
    """
    Look up a metric's value in a pivoted period dict,
    trying each candidate name in order.

    Different companies (and Screener sections) can label
    the same line item slightly differently
    (e.g. "Net Profit" vs "Net profit"), so callers pass
    a list of acceptable names.
    """

    for name in names:

        value = period_row.get(name)

        if value is not None:
            return value

    return None


def _record(metric, period, value, decimals=4):
    """
    Build a single feature record, skipping values that
    can't be computed (None, or division blew up).
    """

    if value is None:
        return None

    return {
        "metric": metric,
        "period": period,
        "value": round(value, decimals)
    }


# ==================================================
# Profitability
#
# Values are decimal fractions (e.g. 0.184 for 18.4%),
# matching how the frontend's formatRatioAsPercent()
# expects Feature values to arrive.
# ==================================================

def build_profitability(pnl_pivoted):

    records = []

    for row in pnl_pivoted:

        period = row["period"]

        sales = _get(row, ["Sales", "Revenue"])
        net_profit = _get(row, ["Net Profit", "Net profit"])
        operating_profit = _get(row, ["Operating Profit"])
        tax_percent = _get(row, ["Tax %"])

        # --------------------------------------------------
        # Operating Margin = Operating Profit / Sales
        # --------------------------------------------------

        if sales and operating_profit is not None:

            record = _record(
                "Operating Margin",
                period,
                operating_profit / sales
            )

            if record:
                records.append(record)

        # --------------------------------------------------
        # Net Profit Margin = Net Profit / Sales
        # --------------------------------------------------

        if sales and net_profit is not None:

            record = _record(
                "Net Profit Margin",
                period,
                net_profit / sales
            )

            if record:
                records.append(record)

        # --------------------------------------------------
        # Effective Tax Rate (Screener's Tax % is already
        # a percentage, e.g. 25.0 -> convert to fraction)
        # --------------------------------------------------

        if tax_percent is not None:

            record = _record(
                "Effective Tax Rate",
                period,
                tax_percent / 100
            )

            if record:
                records.append(record)

    return records


# ==================================================
# Growth
#
# Period-over-period % change, expressed as a decimal
# fraction (e.g. 0.12 for +12%).
# ==================================================

def build_growth(pnl_pivoted):

    records = []

    metrics_to_track = [
        ("Sales Growth", ["Sales", "Revenue"]),
        ("Net Profit Growth", ["Net Profit", "Net profit"]),
        ("EPS Growth", ["EPS in Rs", "EPS"]),
    ]

    for i in range(1, len(pnl_pivoted)):

        previous_row = pnl_pivoted[i - 1]
        current_row = pnl_pivoted[i]

        period = current_row["period"]

        for label, names in metrics_to_track:

            previous_value = _get(previous_row, names)
            current_value = _get(current_row, names)

            if (
                previous_value in (None, 0)
                or current_value is None
            ):
                continue

            growth = (
                (current_value - previous_value)
                / abs(previous_value)
            )

            record = _record(label, period, growth)

            if record:
                records.append(record)

    return records


# ==================================================
# Leverage
#
# Plain ratios (not percentages), e.g. Debt to Equity
# of 0.6 means borrowings are 0.6x equity.
# ==================================================

def build_leverage(bs_pivoted):

    records = []

    for row in bs_pivoted:

        period = row["period"]

        equity_capital = _get(row, ["Equity Capital"])
        reserves = _get(row, ["Reserves"])
        borrowings = _get(row, ["Borrowings"])
        total_liabilities = _get(row, ["Total Liabilities"])

        equity = None

        if equity_capital is not None or reserves is not None:
            equity = (equity_capital or 0) + (reserves or 0)

        # --------------------------------------------------
        # Debt to Equity = Borrowings / Equity
        # --------------------------------------------------

        if borrowings is not None and equity:

            record = _record(
                "Debt to Equity",
                period,
                borrowings / equity,
                decimals=2
            )

            if record:
                records.append(record)

        # --------------------------------------------------
        # Total Liabilities to Equity
        # --------------------------------------------------

        if total_liabilities is not None and equity:

            record = _record(
                "Total Liabilities to Equity",
                period,
                total_liabilities / equity,
                decimals=2
            )

            if record:
                records.append(record)

    return records


# ==================================================
# Cash Flow Quality
#
# Ratios relating cash generation to reported profit,
# expressed as decimal fractions.
# ==================================================

def build_cash_flow_quality(cf_pivoted, pnl_pivoted):

    records = []

    pnl_by_period = {
        row["period"]: row
        for row in pnl_pivoted
    }

    for row in cf_pivoted:

        period = row["period"]

        cash_from_operating = _get(
            row,
            ["Cash from Operating Activity"]
        )

        pnl_row = pnl_by_period.get(period, {})

        net_profit = _get(
            pnl_row,
            ["Net Profit", "Net profit"]
        )

        sales = _get(
            pnl_row,
            ["Sales", "Revenue"]
        )

        # --------------------------------------------------
        # Cash Conversion = CFO / Net Profit
        # (how much of reported profit actually showed up
        # as operating cash)
        # --------------------------------------------------

        if (
            cash_from_operating is not None
            and net_profit not in (None, 0)
        ):

            record = _record(
                "Cash Conversion (CFO / Net Profit)",
                period,
                cash_from_operating / net_profit
            )

            if record:
                records.append(record)

        # --------------------------------------------------
        # Operating Cash Margin = CFO / Sales
        # --------------------------------------------------

        if cash_from_operating is not None and sales:

            record = _record(
                "Operating Cash Margin",
                period,
                cash_from_operating / sales
            )

            if record:
                records.append(record)

    return records


# ==================================================
# Build all features
# ==================================================

def build_features(
    profit_loss_records,
    balance_sheet_records,
    cash_flow_records
):
    """
    Compute all feature categories from raw DB records
    (as returned by models.profit_loss.get_profit_loss,
    models.balance_sheet.get_balance_sheet, and
    models.cash_flow.get_cash_flow).
    """

    pnl_pivoted = pivot_by_period(profit_loss_records)
    bs_pivoted = pivot_by_period(balance_sheet_records)
    cf_pivoted = pivot_by_period(cash_flow_records)

    return {
        "profitability": build_profitability(pnl_pivoted),
        "growth": build_growth(pnl_pivoted),
        "leverage": build_leverage(bs_pivoted),
        "cash_flow_quality": build_cash_flow_quality(
            cf_pivoted,
            pnl_pivoted
        ),
    }