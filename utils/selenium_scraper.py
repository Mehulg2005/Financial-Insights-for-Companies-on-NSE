from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from config import (
    SCREENER_LOGIN_URL,
    SCREENER_COMPANY_URL
)


# --------------------------------------------------
# Selenium driver
# --------------------------------------------------

driver = None


# --------------------------------------------------
# Start Selenium
# --------------------------------------------------

def start_selenium():

    global driver

    if driver is not None:

        try:

            # Check whether browser is still alive
            driver.current_url

            return driver

        except Exception:

            driver = None


    print("\nStarting Selenium...")

    options = Options()

    options.add_argument(
        "--start-maximized"
    )


    driver = webdriver.Chrome(
        options=options
    )


    # --------------------------------------------------
    # Open Screener login
    # --------------------------------------------------

    driver.get(
        SCREENER_LOGIN_URL
    )


    input(
        "Log in to Screener, "
        "then press Enter here..."
    )


    print(
        "Screener login completed."
    )

    print(
        "Selenium is ready."
    )


    return driver


# --------------------------------------------------
# Scrape company
# --------------------------------------------------

def scrape_company(nse_code):

    global driver


    # Make sure Selenium is running

    if driver is None:

        start_selenium()


    print(
        "\n" + "=" * 80
    )

    print(
        f"Scraping: {nse_code}"
    )

    print(
        "=" * 80
    )


    # --------------------------------------------------
    # Open company page
    # --------------------------------------------------

    url = SCREENER_COMPANY_URL.format(
        nse_code
    )

    driver.get(url)


    # --------------------------------------------------
    # Get company name
    # --------------------------------------------------

    company_name = (
        driver.title
        .split(" share price")[0]
        .strip()
    )


    print(
        f"Company Name: {company_name}"
    )


    # --------------------------------------------------
    # Find yearly insights
    # --------------------------------------------------

    insights = driver.find_element(
        By.ID,
        "yearly-insights"
    )


    table = insights.find_element(
        By.TAG_NAME,
        "table"
    )


    rows = table.find_elements(
        By.TAG_NAME,
        "tr"
    )


    data = []


    # --------------------------------------------------
    # Extract table
    # --------------------------------------------------

    for row in rows:

        cells = row.find_elements(
            By.CSS_SELECTOR,
            "th, td"
        )


        row_data = [
            cell.text.strip()
            for cell in cells
        ]


        data.append(row_data)


    if not data:

        raise ValueError(
            f"No Insights data found for {nse_code}"
        )


    return (
        company_name,
        data
    )


# --------------------------------------------------
# Close Selenium
# --------------------------------------------------

def close_selenium():

    global driver

    if driver is not None:

        try:

            driver.quit()

        except Exception:
            pass

        driver = None

        print(
            "Selenium closed."
        )