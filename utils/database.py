# utils/database.py

import os
from datetime import datetime

import psycopg
from dotenv import load_dotenv


# --------------------------------------------------
# Load environment variables
# --------------------------------------------------

load_dotenv()


# --------------------------------------------------
# Database configuration
# --------------------------------------------------

DB_NAME = os.getenv("DB_NAME", "screener_v2_db")
DB_USER = os.getenv("DB_USER", "mehulgupta")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")


# --------------------------------------------------
# Database connection
# --------------------------------------------------

def get_connection():

    return psycopg.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )


# --------------------------------------------------
# Insert / update company
# --------------------------------------------------

def upsert_company(nse_code, company_name):

    query = """
        INSERT INTO company (
            nse_code,
            company_name,
            last_updated
        )
        VALUES (%s, %s, %s)

        ON CONFLICT (nse_code)
        DO UPDATE SET
            company_name = EXCLUDED.company_name,
            last_updated = EXCLUDED.last_updated;
    """

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                query,
                (
                    nse_code,
                    company_name,
                    datetime.now()
                )
            )

        conn.commit()


# --------------------------------------------------
# Quarterly Insights
# --------------------------------------------------

def upsert_quarterly_insights(
    nse_code,
    quarterly_insights
):

    query = """
        INSERT INTO qres_insights (
            nse_code,
            metric,
            period,
            value,
            last_updated
        )
        VALUES (%s, %s, %s, %s, %s)

        ON CONFLICT (nse_code, metric, period)
        DO UPDATE SET
            value = EXCLUDED.value,
            last_updated = EXCLUDED.last_updated;
    """

    now = datetime.now()

    records = []

    for item in quarterly_insights:

        records.append(
            (
                nse_code,
                item["metric"],
                item["period"],
                item["value"],
                now
            )
        )

    if not records:
        return

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.executemany(
                query,
                records
            )

        conn.commit()


# --------------------------------------------------
# Profit & Loss
# --------------------------------------------------

def upsert_profit_loss(
    nse_code,
    profit_loss
):

    query = """
        INSERT INTO profit_n_loss (
            nse_code,
            period,
            sales,
            expenses,
            operating_profit,
            opm_percent,
            other_income,
            interest,
            depreciation,
            profit_before_tax,
            tax_percent,
            net_profit,
            eps,
            dividend_payout_percent,
            last_updated
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s
        )

        ON CONFLICT (nse_code, period)
        DO UPDATE SET
            sales = EXCLUDED.sales,
            expenses = EXCLUDED.expenses,
            operating_profit = EXCLUDED.operating_profit,
            opm_percent = EXCLUDED.opm_percent,
            other_income = EXCLUDED.other_income,
            interest = EXCLUDED.interest,
            depreciation = EXCLUDED.depreciation,
            profit_before_tax = EXCLUDED.profit_before_tax,
            tax_percent = EXCLUDED.tax_percent,
            net_profit = EXCLUDED.net_profit,
            eps = EXCLUDED.eps,
            dividend_payout_percent =
                EXCLUDED.dividend_payout_percent,
            last_updated = EXCLUDED.last_updated;
    """

    now = datetime.now()

    records = []

    for item in profit_loss:

        records.append(
            (
                nse_code,
                item["period"],
                item["sales"],
                item["expenses"],
                item["operating_profit"],
                item["opm_percent"],
                item["other_income"],
                item["interest"],
                item["depreciation"],
                item["profit_before_tax"],
                item["tax_percent"],
                item["net_profit"],
                item["eps"],
                item["dividend_payout_percent"],
                now
            )
        )

    if not records:
        return

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.executemany(
                query,
                records
            )

        conn.commit()


# --------------------------------------------------
# Balance Sheet
# --------------------------------------------------

def upsert_balance_sheet(
    nse_code,
    balance_sheet
):

    query = """
        INSERT INTO balance_sheet (
            nse_code,
            period,
            equity_capital,
            reserves,
            deposits,
            borrowings,
            other_liabilities,
            total_liabilities,
            fixed_assets,
            cwip,
            investments,
            other_assets,
            total_assets,
            last_updated
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s
        )

        ON CONFLICT (nse_code, period)
        DO UPDATE SET
            equity_capital = EXCLUDED.equity_capital,
            reserves = EXCLUDED.reserves,
            deposits = EXCLUDED.deposits,
            borrowings = EXCLUDED.borrowings,
            other_liabilities = EXCLUDED.other_liabilities,
            total_liabilities = EXCLUDED.total_liabilities,
            fixed_assets = EXCLUDED.fixed_assets,
            cwip = EXCLUDED.cwip,
            investments = EXCLUDED.investments,
            other_assets = EXCLUDED.other_assets,
            total_assets = EXCLUDED.total_assets,
            last_updated = EXCLUDED.last_updated;
    """

    now = datetime.now()

    records = []

    for item in balance_sheet:

        records.append(
            (
                nse_code,
                item["period"],
                item.get("equity_capital"),
                item.get("reserves"),
                item.get("deposits"),
                item.get("borrowings"),
                item.get("other_liabilities"),
                item.get("total_liabilities"),
                item.get("fixed_assets"),
                item.get("cwip"),
                item.get("investments"),
                item.get("other_assets"),
                item.get("total_assets"),
                now
            )
        )

    if not records:
        return

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.executemany(
                query,
                records
            )

        conn.commit()


# --------------------------------------------------
# Cash Flow
# --------------------------------------------------

def upsert_cash_flow(
    nse_code,
    cash_flow
):

    query = """
        INSERT INTO cash_flow (
            nse_code,
            period,
            cash_from_operating,
            cash_from_investing,
            cash_from_financing,
            net_cash_flow,
            free_cash_flow,
            cfo_op,
            last_updated
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s
        )

        ON CONFLICT (nse_code, period)
        DO UPDATE SET
            cash_from_operating =
                EXCLUDED.cash_from_operating,
            cash_from_investing =
                EXCLUDED.cash_from_investing,
            cash_from_financing =
                EXCLUDED.cash_from_financing,
            net_cash_flow =
                EXCLUDED.net_cash_flow,
            free_cash_flow =
                EXCLUDED.free_cash_flow,
            cfo_op =
                EXCLUDED.cfo_op,
            last_updated =
                EXCLUDED.last_updated;
    """

    now = datetime.now()

    records = []

    for item in cash_flow:

        records.append(
            (
                nse_code,
                item["period"],
                item["cash_from_operating"],
                item["cash_from_investing"],
                item["cash_from_financing"],
                item["net_cash_flow"],
                item["free_cash_flow"],
                item["cfo_op"],
                now
            )
        )

    if not records:
        return

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.executemany(
                query,
                records
            )

        conn.commit()


# --------------------------------------------------
# Store complete company data
# --------------------------------------------------

def save_company_data(
    nse_code,
    data
):

    company_name = data["company_name"]

    print(
        f"\nSaving {company_name} ({nse_code})..."
    )

    # --------------------------------------------------
    # Company
    # --------------------------------------------------

    upsert_company(
        nse_code,
        company_name
    )

    print("Company saved.")


    # --------------------------------------------------
    # Quarterly Insights
    # --------------------------------------------------

    upsert_quarterly_insights(
        nse_code,
        data.get("quarterly_insights", [])
    )

    print("Quarterly Insights saved.")


    # --------------------------------------------------
    # Profit & Loss
    # --------------------------------------------------

    upsert_profit_loss(
        nse_code,
        data.get("profit_loss", [])
    )

    print("Profit & Loss saved.")


    # --------------------------------------------------
    # Balance Sheet
    # --------------------------------------------------

    upsert_balance_sheet(
        nse_code,
        data.get("balance_sheet", [])
    )

    print("Balance Sheet saved.")


    # --------------------------------------------------
    # Cash Flow
    # --------------------------------------------------

    upsert_cash_flow(
        nse_code,
        data.get("cash_flow", [])
    )

    print("Cash Flow saved.")


    print(
        f"\nSuccessfully saved {nse_code} to PostgreSQL."
    )


# --------------------------------------------------
# Test database connection
# --------------------------------------------------

def test_connection():

    try:

        with get_connection() as conn:

            with conn.cursor() as cur:

                cur.execute(
                    "SELECT current_database();"
                )

                database = cur.fetchone()[0]

                print(
                    f"Database connection successful: {database}"
                )

        return True

    except Exception as e:

        print(
            f"Database connection failed: {e}"
        )

        return False


# --------------------------------------------------
# Run directly
# --------------------------------------------------

if __name__ == "__main__":

    test_connection()