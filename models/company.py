from utils.database import get_connection


def create_company(nse_code, company_name):
    """
    Insert a company into the database.

    If the company already exists, update its name
    and last_updated timestamp.
    """

    query = """
        INSERT INTO company (
            nse_code,
            company_name,
            last_updated
        )
        VALUES (
            %s,
            %s,
            CURRENT_TIMESTAMP
        )

        ON CONFLICT (nse_code)
        DO UPDATE SET
            company_name = EXCLUDED.company_name,
            last_updated = CURRENT_TIMESTAMP

        RETURNING
            company_id,
            nse_code,
            company_name,
            last_updated;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (nse_code, company_name)
            )

            result = cur.fetchone()

        conn.commit()

    return result


def get_company_by_nse(nse_code):
    """
    Retrieve a company using its NSE code.
    """

    query = """
        SELECT
            company_id,
            nse_code,
            company_name,
            last_updated
        FROM company
        WHERE nse_code = %s;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (nse_code,)
            )

            result = cur.fetchone()

    return result


def company_exists(nse_code):
    """
    Check whether a company exists in the database.
    """

    query = """
        SELECT EXISTS (
            SELECT 1
            FROM company
            WHERE nse_code = %s
        );
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (nse_code,)
            )

            result = cur.fetchone()

    return result[0]