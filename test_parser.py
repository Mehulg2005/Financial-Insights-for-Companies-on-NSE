from utils.scraper import (
    start_selenium,
    scrape_company,
    close_selenium
)

from utils.parser import (
    parse_quarterly_insights,
    parse_profit_loss,
    parse_balance_sheet,
    parse_cash_flow
)

from models.company import create_company
from models.qres_insights import insert_insight
from models.profit_loss import insert_profit_loss
from models.balance_sheet import insert_balance_sheet
from models.cash_flow import insert_cash_flow


def main():

    nse_code = "HDFCBANK"

    try:

        # ==================================================
        # Start Selenium
        # ==================================================

        print("\nStarting Selenium...")

        start_selenium()

        # ==================================================
        # Scrape Company
        # ==================================================

        print("\n" + "=" * 100)
        print(f"Scraping: {nse_code}")
        print("=" * 100)

        data = scrape_company(nse_code)

        company_name = data["company_name"]

        print(f"Company Name: {company_name}")

        # ==================================================
        # Parse
        # ==================================================

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

        # ==================================================
        # Insert Company
        # ==================================================

        print("\n" + "=" * 100)
        print("INSERTING COMPANY")
        print("=" * 100)

        company = create_company(
            nse_code,
            company_name
        )

        print(
            f"Company inserted/updated: "
            f"{company[2]}"
        )

        # ==================================================
        # Insert Quarterly Insights
        # ==================================================

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

        # ==================================================
        # Insert Profit & Loss
        # ==================================================

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

        # ==================================================
        # Insert Balance Sheet
        # ==================================================

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

        # ==================================================
        # Insert Cash Flow
        # ==================================================

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

        # ==================================================
        # Final Summary
        # ==================================================

        print("\n" + "=" * 100)
        print("DATABASE INSERT SUMMARY")
        print("=" * 100)

        print(f"Company              : {company_name}")
        print(f"NSE Code             : {nse_code}")
        print(f"Quarterly Insights   : {insight_count}")
        print(f"Profit & Loss        : {pnl_count}")
        print(f"Balance Sheet        : {balance_count}")
        print(f"Cash Flow            : {cash_count}")

        print("=" * 100)

    finally:

        close_selenium()


if __name__ == "__main__":
    main()