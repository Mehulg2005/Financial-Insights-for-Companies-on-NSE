from utils.database import get_connection


def insert_insight(
    nse_code,
    metric,
    period,
    value
):
    """
    Insert or update a Quarterly Insight.
    """

    query = """
        INSERT INTO qres_insights (
            nse_code,
            metric,
            period,
            value,
            last_updated
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            CURRENT_TIMESTAMP
        )

        ON CONFLICT (nse_code, metric, period)
        DO UPDATE SET
            value = EXCLUDED.value,
            last_updated = CURRENT_TIMESTAMP

        RETURNING
            id,
            nse_code,
            metric,
            period,
            value,
            last_updated;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    nse_code,
                    metric,
                    period,
                    value
                )
            )

            result = cur.fetchone()

        conn.commit()

    return result


def get_insights(nse_code):
    """
    Retrieve all Quarterly Insights
    for a company.
    """

    query = """
        SELECT
            id,
            nse_code,
            metric,
            period,
            value,
            last_updated
        FROM qres_insights
        WHERE nse_code = %s
        ORDER BY period;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (nse_code,)
            )

            result = cur.fetchall()

    return result