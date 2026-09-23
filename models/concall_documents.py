from utils.database import get_connection


def insert_document(
    nse_code,
    period,
    document_no
):
    """
    Insert or update a manually-collected concall document
    reference. (nse_code, period) identifies one summary.
    """

    query = """
        INSERT INTO concall_documents (
            nse_code,
            period,
            document_no,
            last_updated
        )
        VALUES (
            %s,
            %s,
            %s,
            CURRENT_TIMESTAMP
        )

        ON CONFLICT (nse_code, period)
        DO UPDATE SET
            document_no = EXCLUDED.document_no,
            last_updated = CURRENT_TIMESTAMP

        RETURNING
            id,
            nse_code,
            period,
            document_no,
            last_updated;
    """

    nse_code = nse_code.upper().strip()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    nse_code,
                    period,
                    document_no
                )
            )

            result = cur.fetchone()

        conn.commit()

    return result


def get_latest_documents(nse_code, limit=6):
    """
    Retrieve the most recently added concall documents
    for a company, newest first.
    """

    query = """
        SELECT
            id,
            nse_code,
            period,
            document_no,
            last_updated
        FROM concall_documents
        WHERE nse_code = %s
        ORDER BY last_updated DESC, id DESC
        LIMIT %s;
    """

    nse_code = nse_code.upper().strip()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (nse_code, limit)
            )

            columns = [
                description[0]
                for description in cur.description
            ]

            rows = cur.fetchall()

    return [
        dict(zip(columns, row))
        for row in rows
    ]