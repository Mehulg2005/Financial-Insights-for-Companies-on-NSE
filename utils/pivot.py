# ==================================================
# Pivot database records
# ==================================================

def pivot_by_period(records):
    """
    Convert database records from:

        id | nse_code | period | metric | value | last_updated

    into:

        [
            {
                "period": "Mar 2026",
                "Sales": 1234,
                "Expenses": 500
            },
            {
                "period": "Mar 2025",
                "Sales": 1100,
                "Expenses": 450
            }
        ]

    This format is used directly by the frontend.
    """

    if not records:
        return []

    periods = []
    period_seen = set()

    data = {}

    for record in records:

        # ==================================================
        # Database schema:
        #
        # 0 = id
        # 1 = nse_code
        # 2 = period
        # 3 = metric
        # 4 = value
        # 5 = last_updated
        # ==================================================

        period = record[2]
        metric = record[3]
        value = record[4]

        if period is None or metric is None:
            continue

        period = str(period).strip()
        metric = str(metric).strip()

        if not period or not metric:
            continue

        # --------------------------------------------------
        # Preserve period order
        # --------------------------------------------------

        if period not in period_seen:

            period_seen.add(period)
            periods.append(period)

        # --------------------------------------------------
        # Create period
        # --------------------------------------------------

        if period not in data:

            data[period] = {
                "period": period
            }

        # --------------------------------------------------
        # Add metric
        # --------------------------------------------------

        data[period][metric] = value

    # ==================================================
    # Return periods in original database order
    # ==================================================

    return [
        data[period]
        for period in periods
        if period in data
    ]