import psycopg

from config import (
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
    DB_HOST,
    DB_PORT
)

from models.screener_db import (
    CREATE_TABLE_QUERY,
    CREATE_INDEX_QUERY
)


# --------------------------------------------------
# Get PostgreSQL connection
# --------------------------------------------------

def get_connection():

    connection = psycopg.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

    return connection


# --------------------------------------------------
# Initialize database
# --------------------------------------------------

def initialize_database():

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                CREATE_TABLE_QUERY
            )

            cursor.execute(
                CREATE_INDEX_QUERY
            )

        connection.commit()

        print("PostgreSQL database initialized.")

    finally:

        connection.close()


# --------------------------------------------------
# Check if company exists
# --------------------------------------------------

def company_exists(nse_code):

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM insights
                    WHERE nse_code = %s
                );
                """,
                (nse_code,)
            )

            result = cursor.fetchone()

            return result[0]

    finally:

        connection.close()


# --------------------------------------------------
# Get company information
# --------------------------------------------------

def get_company_data(nse_code):

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    nse_code,
                    company_name,
                    metric,
                    period,
                    value,
                    last_updated
                FROM insights
                WHERE nse_code = %s
                ORDER BY metric;
                """,
                (nse_code,)
            )

            rows = cursor.fetchall()

            return rows

    finally:

        connection.close()


# --------------------------------------------------
# Insert / update scraped data
# --------------------------------------------------

def insert_company_data(
    nse_code,
    company_name,
    data
):

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            inserted_count = 0

            for row in data:

                metric = row["Metric"]
                period = row["Period"]
                value = row["Value"]

                cursor.execute(
                    """
                    INSERT INTO insights (
                        nse_code,
                        company_name,
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
                        %s,
                        CURRENT_TIMESTAMP
                    )

                    ON CONFLICT (
                        nse_code,
                        metric,
                        period
                    )

                    DO UPDATE SET

                        company_name =
                            EXCLUDED.company_name,

                        value =
                            EXCLUDED.value,

                        last_updated =
                            CURRENT_TIMESTAMP;
                    """,
                    (
                        nse_code,
                        company_name,
                        metric,
                        period,
                        value
                    )
                )

                inserted_count += 1

            # --------------------------------------------------
            # Update last_updated for the entire company
            # --------------------------------------------------

            cursor.execute(
                """
                UPDATE insights
                SET last_updated = CURRENT_TIMESTAMP
                WHERE nse_code = %s;
                """,
                (nse_code,)
            )

        connection.commit()

        return inserted_count

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


# --------------------------------------------------
# Get company's last updated time
# --------------------------------------------------

def get_last_updated(nse_code):

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT MAX(last_updated)
                FROM insights
                WHERE nse_code = %s;
                """,
                (nse_code,)
            )

            result = cursor.fetchone()

            return result[0]

    finally:

        connection.close()