from utils.database import get_connection


def insert_profit_loss(nse_code, period, metric, value):
    """
    Insert or update a single Profit & Loss metric
    for a given period.
    """

    query = """
        INSERT INTO profit_n_loss (
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


def get_profit_loss(nse_code):
    """
    Retrieve all Profit & Loss records for a company.
    """

    query = """
        SELECT
            id,
            nse_code,
            period,
            metric,
            value,
            last_updated
        FROM profit_n_loss
        WHERE nse_code = %s
        ORDER BY period;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (nse_code,))
            result = cur.fetchall()

    return result