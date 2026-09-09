# ==================================================
# Utility functions
# ==================================================

def clean_metric(metric):
    """
    Clean Screener metric names.

    Examples:
        'Sales +'        -> 'Sales'
        'Equity Capital' -> 'Equity Capital'
    """

    if metric is None:
        return None

    metric = " ".join(metric.split())

    # Remove Screener's '+' indicator
    if metric.endswith("+"):
        metric = metric[:-1].strip()

    return metric


def parse_number(value):
    """
    Convert a Screener value into a float.

    Examples:
        '328,013' -> 328013.0
        '16.46'   -> 16.46
        '-512'    -> -512.0
        '10%'     -> 10.0
        ''        -> None
        '-'       -> None
    """

    if value is None:
        return None

    value = value.strip()

    if value == "":
        return None

    if value == "-":
        return None

    # Remove commas
    value = value.replace(",", "")

    # Remove percentage sign
    value = value.replace("%", "")

    try:
        return float(value)

    except ValueError:
        return None


def parse_integer(value):
    """
    Convert a Screener value into an integer.
    """

    number = parse_number(value)

    if number is None:
        return None

    return int(number)


# ==================================================
# Generic Metric Table Parser
# ==================================================

def parse_metric_table(data):
    """
    Convert any Screener metric table into
    long-format records.

    Input:

        [
            ["", "Mar 2025", "Mar 2026"],
            ["Sales", "100", "200"],
            ["Expenses", "50", "80"],
            ["Other Income", "10", "20"]
        ]

    Output:

        [
            {
                "metric": "Sales",
                "period": "Mar 2025",
                "value": 100.0
            },
            {
                "metric": "Sales",
                "period": "Mar 2026",
                "value": 200.0
            },
            ...
        ]

    IMPORTANT:
    No metrics are filtered out.
    Every Screener metric is preserved.
    """

    if not data:
        return []

    # --------------------------------------------------
    # First row contains periods
    # --------------------------------------------------

    header = data[0]

    if len(header) < 2:
        return []

    periods = header[1:]

    records = []

    # --------------------------------------------------
    # Process every metric row
    # --------------------------------------------------

    for row in data[1:]:

        if not row:
            continue

        # First column = metric name
        metric = clean_metric(row[0])

        if not metric:
            continue

        values = row[1:]

        # --------------------------------------------------
        # Process every period
        # --------------------------------------------------

        for index, period in enumerate(periods):

            if index >= len(values):
                continue

            period = period.strip()

            if not period:
                continue

            value = parse_number(
                values[index]
            )

            # Do not insert missing values
            if value is None:
                continue

            records.append(
                {
                    "metric": metric,
                    "period": period,
                    "value": value
                }
            )

    return records


# ==================================================
# Quarterly Insights
# ==================================================

def parse_quarterly_insights(data):
    """
    Parse Quarterly Insights.

    ALL metrics are retained.
    """

    return parse_metric_table(data)


# ==================================================
# Profit & Loss
# ==================================================

def parse_profit_loss(data):
    """
    Parse Profit & Loss.

    ALL Screener metrics are retained.

    No hardcoded metric map is used because
    different companies can have different
    Profit & Loss structures.
    """

    return parse_metric_table(data)


# ==================================================
# Balance Sheet
# ==================================================

def parse_balance_sheet(data):
    """
    Parse Balance Sheet.

    ALL Screener metrics are retained.
    """

    return parse_metric_table(data)


# ==================================================
# Cash Flow
# ==================================================

def parse_cash_flow(data):
    """
    Parse Cash Flow.

    ALL Screener metrics are retained.
    """

    return parse_metric_table(data)