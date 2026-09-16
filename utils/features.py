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
# Effective Tax Rate / Operating Margin are decimal
# fractions (e.g. 0.184 for 18.4%), matching how the
# frontend's formatRatioAsPercent() expects them.
# Sales / Net Profit / Profit before Tax / Profit
# After Tax are raw rupee-crore values.
# ==================================================

def build_profitability(pnl_pivoted):

    records = []

    for row in pnl_pivoted:

        period = row["period"]

        sales = _get(row, ["Sales", "Revenue"])
        net_profit = _get(row, ["Net Profit", "Net profit"])
        operating_profit = _get(row, ["Operating Profit"])
        tax_percent = _get(row, ["Tax %"])
        profit_before_tax = _get(
            row,
            ["Profit before tax", "Profit before Tax"]
        )

        eps = _get(row, ["EPS in Rs", "EPS"])

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
        # Sales (raw)
        # --------------------------------------------------

        if sales is not None:

            record = _record(
                "Sales",
                period,
                sales,
                decimals=2
            )

            if record:
                records.append(record)

        # --------------------------------------------------
        # Net Profit (raw)
        # --------------------------------------------------

        if net_profit is not None:

            record = _record(
                "Net Profit",
                period,
                net_profit,
                decimals=2
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

        # --------------------------------------------------
        # Profit before Tax (raw)
        # --------------------------------------------------

        if profit_before_tax is not None:

            record = _record(
                "Profit before Tax",
                period,
                profit_before_tax,
                decimals=2
            )

            if record:
                records.append(record)

        # --------------------------------------------------
        # Profit After Tax
        #   = Profit before Tax - (Profit before Tax * Tax% / 100)
        # --------------------------------------------------

        if profit_before_tax is not None and tax_percent is not None:

            pat = profit_before_tax - (
                profit_before_tax * tax_percent / 100
            )

            record = _record(
                "Profit After Tax",
                period,
                pat,
                decimals=2
            )

            if record:
                records.append(record)

        # --------------------------------------------------
        # EPS (raw) - a distinct signal from PAT level: PAT
        # can rise while EPS stays flat or falls if the
        # company has issued new shares (dilution).
        # --------------------------------------------------

        if eps is not None:

            record = _record(
                "EPS",
                period,
                eps,
                decimals=2
            )

            if record:
                records.append(record)

    return records


# ==================================================
# Cash Flow Quality
#
# CFO is a raw rupee-crore value. CFO Contribution and
# Cash Conversion are decimal fractions (e.g. 0.18 for
# 18%), matching formatRatioAsPercent() on the frontend.
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

        net_cash_flow = _get(
            row,
            ["Net Cash Flow"]
        )

        pnl_row = pnl_by_period.get(period, {})

        net_profit = _get(
            pnl_row,
            ["Net Profit", "Net profit"]
        )

        # --------------------------------------------------
        # Cash from Operating Activity (CFO) - raw
        # --------------------------------------------------

        if cash_from_operating is not None:

            record = _record(
                "Cash from Operating Activity (CFO)",
                period,
                cash_from_operating,
                decimals=2
            )

            if record:
                records.append(record)

        # --------------------------------------------------
        # CFO Contribution = CFO / Net Cash Flow
        # (how much of the company's overall net cash
        # movement came from operations)
        # --------------------------------------------------

        if (
            cash_from_operating is not None
            and net_cash_flow not in (None, 0)
        ):

            record = _record(
                "CFO Contribution",
                period,
                cash_from_operating / net_cash_flow
            )

            if record:
                records.append(record)

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

    return records


# ==================================================
# Growth Trends
#
# Reserves / Equity Capital are raw rupee-crore values.
# Investment Migration is a decimal fraction (e.g. 0.12
# for 12%). Borrowings to Net Worth Ratio is a plain
# ratio (e.g. 0.6 means borrowings are 0.6x net worth).
# ==================================================

def build_growth_trends(bs_pivoted, pnl_pivoted):

    records = []

    pnl_by_period = {
        row["period"]: row
        for row in pnl_pivoted
    }

    for row in bs_pivoted:

        period = row["period"]

        reserves = _get(row, ["Reserves"])
        equity_capital = _get(row, ["Equity Capital"])
        investments = _get(row, ["Investments"])
        total_assets = _get(row, ["Total Assets"])
        borrowings = _get(row, ["Borrowings"])

        net_worth = None

        if equity_capital is not None or reserves is not None:
            net_worth = (equity_capital or 0) + (reserves or 0)

        # --------------------------------------------------
        # Reserves (raw)
        # --------------------------------------------------

        if reserves is not None:

            record = _record(
                "Reserves",
                period,
                reserves,
                decimals=2
            )

            if record:
                records.append(record)

        # --------------------------------------------------
        # Equity Capital (raw)
        # --------------------------------------------------

        if equity_capital is not None:

            record = _record(
                "Equity Capital",
                period,
                equity_capital,
                decimals=2
            )

            if record:
                records.append(record)

        # --------------------------------------------------
        # Investment Migration = (Investments / Total Assets) * 100%
        # --------------------------------------------------

        if investments is not None and total_assets:

            record = _record(
                "Investment Migration",
                period,
                investments / total_assets
            )

            if record:
                records.append(record)

        # --------------------------------------------------
        # Borrowings to Net Worth Ratio
        #   = Borrowings / (Equity Capital + Reserves)
        # --------------------------------------------------

        if borrowings is not None and net_worth:

            record = _record(
                "Borrowings to Net Worth Ratio",
                period,
                borrowings / net_worth,
                decimals=2
            )

            if record:
                records.append(record)

        # --------------------------------------------------
        # Interest Coverage Ratio = Operating Profit / Interest
        # Shows whether operating earnings can comfortably
        # service the company's debt - a different question
        # from "how much debt" (Borrowings to Net Worth above).
        # --------------------------------------------------

        pnl_row = pnl_by_period.get(period, {})

        operating_profit = _get(pnl_row, ["Operating Profit"])
        interest = _get(pnl_row, ["Interest"])

        if operating_profit is not None and interest not in (None, 0):

            record = _record(
                "Interest Coverage Ratio",
                period,
                operating_profit / interest,
                decimals=2
            )

            if record:
                records.append(record)

    return records

# ==================================================
# Other Metrics
#
# Chart data points (not a pivot table). Each entry is
# one point per period: {period, x, y}, in rupee-crore
# values, ready to feed a scatter/line chart.
# ==================================================

def build_other_metrics(bs_pivoted):

    total_liabilities_vs_total_assets = []
    borrowings_vs_total_assets = []

    for row in bs_pivoted:

        period = row["period"]

        total_assets = _get(row, ["Total Assets"])
        total_liabilities = _get(row, ["Total Liabilities"])
        borrowings = _get(row, ["Borrowings"])

        # --------------------------------------------------
        # Graph 1: Total Liabilities (y) vs Total Assets (x)
        # --------------------------------------------------

        if total_assets is not None and total_liabilities is not None:

            total_liabilities_vs_total_assets.append({
                "period": period,
                "x": round(total_assets, 2),
                "y": round(total_liabilities, 2)
            })

        # --------------------------------------------------
        # Graph 2: Borrowings (y) vs Total Assets (x)
        # --------------------------------------------------

        if total_assets is not None and borrowings is not None:

            borrowings_vs_total_assets.append({
                "period": period,
                "x": round(total_assets, 2),
                "y": round(borrowings, 2)
            })

    return {
        "total_liabilities_vs_total_assets": total_liabilities_vs_total_assets,
        "borrowings_vs_total_assets": borrowings_vs_total_assets
    }


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
        "cash_flow_quality": build_cash_flow_quality(
            cf_pivoted,
            pnl_pivoted
        ),
        "growth_trends": build_growth_trends(bs_pivoted, pnl_pivoted),
        "other_metrics": build_other_metrics(bs_pivoted),
    }