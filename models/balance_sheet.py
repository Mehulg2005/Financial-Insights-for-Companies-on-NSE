from utils.database import get_connection


def insert_balance_sheet(nse_code, period, metric, value):
    """
    Insert or update a single Balance Sheet metric
    for a given period.
    """

    query = """
        INSERT INTO balance_sheet (
            nse_code,
            period,
            metric,
            value,
            last_updated
        )
        VALUES (
            %s, %s, %s, %s, CURRENT_TIMESTAMP
        )

        ON CONFLICT (nse_code, metric, period)
        DO UPDATE SET
            value = EXCLUDED.value,
            last_updated = CURRENT_TIMESTAMP

        RETURNING *;
    """

    values = (nse_code, period, metric, value)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, values)
            result = cur.fetchone()

        conn.commit()

    return result


def get_balance_sheet(nse_code):
    """
    Retrieve all Balance Sheet records for a company.
    """

    query = """
        SELECT
            id,
            nse_code,
            period,
            metric,
            value,
            last_updated
        FROM balance_sheet
        WHERE nse_code = %s
        ORDER BY period;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (nse_code,))
            result = cur.fetchall()

    return result