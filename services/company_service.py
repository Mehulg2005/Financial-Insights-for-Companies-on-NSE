from models.company import create_company, get_company_by_nse
from models.qres_insights import insert_insight
from models.profit_loss import insert_profit_loss
from models.balance_sheet import insert_balance_sheet
from models.cash_flow import insert_cash_flow

from utils.company_data import get_company_data
from utils.scraper import (
    start_selenium,
    scrape_company
)

from utils.parser import (
    parse_quarterly_insights,
    parse_profit_loss,
    parse_balance_sheet,
    parse_cash_flow
)


def scrape_and_store_company(nse_code):
    """
    Scrape a company from Screener, parse the data,
    and store everything in PostgreSQL.

    Used both when a company is missing from the database
    and when an existing company's data is being refreshed
    via the "Update" action.

    NOTE: Selenium is intentionally NOT closed here. It is
    started (or reused, if already running) so that a login
    session persists across multiple searches/updates in the
    same app run. Selenium is only closed on app shutdown
    (see api.py's lifespan handler).
    """

    nse_code = nse_code.upper().strip()

    print("\n" + "=" * 100)
    print(f"SCRAPING: {nse_code}")
    print("=" * 100)

    # --------------------------------------------------
    # Start (or reuse) Selenium
    # --------------------------------------------------

    start_selenium()

    # --------------------------------------------------
    # Scrape company
    # --------------------------------------------------

    data = scrape_company(nse_code)

    company_name = data["company_name"]

    print(f"Company Name: {company_name}")

    # --------------------------------------------------
    # Parse data
    # --------------------------------------------------

    quarterly_insights = parse_quarterly_insights(
        data["quarterly_insights"]
    )

    profit_loss = parse_profit_loss(
        data["profit_loss"]
    )

    balance_sheet = parse_balance_sheet(
        data["balance_sheet"]
    )

    cash_flow = parse_cash_flow(
        data["cash_flow"]
    )

    # --------------------------------------------------
    # Insert company
    # --------------------------------------------------

    print("\n" + "=" * 100)
    print("INSERTING COMPANY")
    print("=" * 100)

    create_company(
        nse_code,
        company_name
    )

    print(
        f"Company inserted/updated: {company_name}"
    )

    # --------------------------------------------------
    # Insert Quarterly Insights
    # --------------------------------------------------

    print("\n" + "=" * 100)
    print("INSERTING QUARTERLY INSIGHTS")
    print("=" * 100)

    insight_count = 0

    for record in quarterly_insights:

        insert_insight(
            nse_code=nse_code,
            metric=record["metric"],
            period=record["period"],
            value=record["value"]
        )

        insight_count += 1

    print(
        f"Quarterly Insights inserted/updated: "
        f"{insight_count}"
    )

    # --------------------------------------------------
    # Insert Profit & Loss
    # --------------------------------------------------

    print("\n" + "=" * 100)
    print("INSERTING PROFIT & LOSS")
    print("=" * 100)

    pnl_count = 0

    for record in profit_loss:

        insert_profit_loss(
            nse_code=nse_code,
            period=record["period"],
            metric=record["metric"],
            value=record["value"]
        )

        pnl_count += 1

    print(
        f"Profit & Loss inserted/updated: "
        f"{pnl_count}"
    )

    # --------------------------------------------------
    # Insert Balance Sheet
    # --------------------------------------------------

    print("\n" + "=" * 100)
    print("INSERTING BALANCE SHEET")
    print("=" * 100)

    balance_count = 0

    for record in balance_sheet:

        insert_balance_sheet(
            nse_code=nse_code,
            period=record["period"],
            metric=record["metric"],
            value=record["value"]
        )

        balance_count += 1

    print(
        f"Balance Sheet inserted/updated: "
        f"{balance_count}"
    )

    # --------------------------------------------------
    # Insert Cash Flow
    # --------------------------------------------------

    print("\n" + "=" * 100)
    print("INSERTING CASH FLOW")
    print("=" * 100)

    cash_count = 0

    for record in cash_flow:

        insert_cash_flow(
            nse_code=nse_code,
            period=record["period"],
            metric=record["metric"],
            value=record["value"]
        )

        cash_count += 1

    print(
        f"Cash Flow inserted/updated: "
        f"{cash_count}"
    )

    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    print("\n" + "=" * 100)
    print("DATABASE INSERT SUMMARY")
    print("=" * 100)

    print(f"Company              : {company_name}")
    print(f"NSE Code             : {nse_code}")
    print(
        f"Quarterly Insights   : {insight_count}"
    )
    print(
        f"Profit & Loss        : {pnl_count}"
    )
    print(
        f"Balance Sheet        : {balance_count}"
    )
    print(
        f"Cash Flow            : {cash_count}"
    )

    print("=" * 100)

    # --------------------------------------------------
    # Return data from database
    # (Selenium is intentionally left open for reuse)
    # --------------------------------------------------

    return get_company_data(nse_code)


def get_or_scrape_company(nse_code):
    """
    Retrieve company data from PostgreSQL.

    If the company does not exist, scrape it from Screener
    (opening/reusing a Selenium session as needed) and store
    it first.
    """

    nse_code = nse_code.upper().strip()

    # --------------------------------------------------
    # Check database first
    # --------------------------------------------------

    company = get_company_by_nse(nse_code)

    if company:

        print("\n" + "=" * 100)
        print(f"COMPANY FOUND IN DATABASE: {nse_code}")
        print("=" * 100)

        return get_company_data(nse_code)

    # --------------------------------------------------
    # Company not found -> scrape
    # --------------------------------------------------

    print("\n" + "=" * 100)
    print(f"COMPANY NOT FOUND IN DATABASE: {nse_code}")
    print("=" * 100)

    return scrape_and_store_company(nse_code)


def update_company(nse_code):
    """
    Force a fresh scrape of a company from Screener
    (whether or not it already exists in the database)
    and upsert the latest data.

    This backs the "Update" button: it always re-scrapes,
    reusing an already-open Selenium session if present.
    """

    return scrape_and_store_company(nse_code)