from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import json


# ==================================================
# Screener URLs
# ==================================================

SCREENER_LOGIN_URL = "https://www.screener.in/login/"

SCREENER_COMPANY_URL = (
    "https://www.screener.in/company/{}/"
)


# ==================================================
# Selenium driver
# ==================================================

driver = None


# ==================================================
# Section IDs
# ==================================================

SECTION_IDS = {
    "quarterly_insights": "quarterly-insights",
    "profit_loss": "profit-loss",
    "balance_sheet": "balance-sheet",
    "cash_flow": "cash-flow",
}


# ==================================================
# Start Selenium
# ==================================================

def start_selenium():
    """
    Start Selenium only if it is not already running.

    Once started, Selenium remains alive until
    close_selenium() is explicitly called.
    """

    global driver

    # --------------------------------------------------
    # Check whether Selenium is already running
    # --------------------------------------------------

    if driver is not None:

        try:
            driver.current_url

            print("Selenium already running. Reusing existing session.")

            return driver

        except Exception:
            driver = None

    # --------------------------------------------------
    # Start Selenium
    # --------------------------------------------------

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


# ==================================================
# Extract table from a section
# ==================================================

def extract_table(section_id):
    """
    Extract a Screener statement table and fetch hidden schedule
    rows through Screener's schedule API.
    """

    global driver

    if driver is None:
        start_selenium()

    try:
        section = driver.find_element(
            By.ID,
            section_id
        )

    except Exception as error:
        raise ValueError(
            f"Section '{section_id}' was not found."
        ) from error

    tables = section.find_elements(
        By.CSS_SELECTOR,
        "table.data-table"
    )

    if not tables:
        raise ValueError(
            f"No data table found inside section '{section_id}'."
        )

    table = tables[0]

    rows = table.find_elements(
        By.TAG_NAME,
        "tr"
    )

    data = []

    for row in rows:
        cells = row.find_elements(
            By.CSS_SELECTOR,
            "th, td"
        )

        row_data = [
            cell.text.strip()
            for cell in cells
        ]

        if any(row_data):
            data.append(row_data)

    if not data:
        raise ValueError(
            f"No data found inside section '{section_id}'."
        )

    schedule_parents = {
        "profit-loss": [
            "Expenses",
        ],
        "balance-sheet": [
            "Other Assets",
        ],
    }

    parents = schedule_parents.get(
        section_id,
        []
    )

    if not parents:
        return data

    schedule_result = driver.execute_async_script(
        """
        const sectionId = arguments[0];
        const parents = arguments[1];
        const done = arguments[arguments.length - 1];

        function findCompanyId() {
            const html = document.documentElement.innerHTML;

            const patterns = [
                /\\/company\\/actions\\/(\\d+)/,
                /\\/api\\/company\\/(\\d+)/,
                /company[_-]?id[^0-9]+(\\d+)/i
            ];

            for (const pattern of patterns) {
                const match = html.match(pattern);

                if (match) {
                    return match[1];
                }
            }

            return null;
        }

        function parseRows(html) {
            const wrapper = document.createElement("div");
            wrapper.innerHTML = html;

            const rows = wrapper.querySelectorAll("tr");
            const result = [];

            rows.forEach(row => {
                const cells = row.querySelectorAll("th, td");

                const rowData = Array.from(cells).map(
                    cell => cell.textContent.trim()
                );

                if (rowData.some(value => value.length > 0)) {
                    result.push(rowData);
                }
            });

            return result;
        }

        function parsePayload(payload) {
            if (!payload) {
                return [];
            }

            if (typeof payload === "string") {
                return parseRows(payload);
            }

            if (typeof payload.html === "string") {
                return parseRows(payload.html);
            }

            if (Array.isArray(payload.rows)) {
                return payload.rows;
            }

            return [];
        }

        async function loadSchedules() {
            const companyId = findCompanyId();

            if (!companyId) {
                throw new Error(
                    "Could not find Screener company ID."
                );
            }

            const result = [];

            for (const parent of parents) {
                const params = new URLSearchParams({
                    parent: parent,
                    section: sectionId,
                    consolidated: ""
                });

                const response = await fetch(
                    `/api/company/${companyId}/schedules/?${params.toString()}`,
                    {
                        credentials: "same-origin",
                        headers: {
                            "X-Requested-With": "XMLHttpRequest"
                        }
                    }
                );

                if (!response.ok) {
                    throw new Error(
                        `Schedule request failed for ${parent}: ${response.status}`
                    );
                }

                const payload = await response.json();
                const rows = parsePayload(payload);

                result.push(...rows);
            }

            return result;
        }

        loadSchedules()
            .then(rows => {
                done({
                    ok: true,
                    rows: rows
                });
            })
            .catch(error => {
                done({
                    ok: false,
                    error: error.message
                });
            });
        """,
        section_id,
        parents
    )

    if not schedule_result or not schedule_result.get("ok"):
        error_message = (
            schedule_result.get("error")
            if schedule_result
            else "Unknown schedule API error"
        )

        raise ValueError(
            f"Could not load Screener schedule rows for "
            f"section '{section_id}': {error_message}"
        )

    child_rows = schedule_result.get(
        "rows",
        []
    )

    existing_metrics = {
        row[0].strip().lower()
        for row in data[1:]
        if row and row[0].strip()
    }

    for child_row in child_rows:
        if not child_row:
            continue

        metric_name = child_row[0].strip().lower()

        if not metric_name:
            continue

        if metric_name not in existing_metrics:
            data.append(child_row)
            existing_metrics.add(metric_name)

    return data


# ==================================================
# Load Quarterly Insights
# ==================================================

def load_quarterly_insights():
    """
    Switch Screener from Yearly Insights
    to Quarterly Insights.
    """

    global driver

    print(
        "\nSwitching to Quarterly Insights..."
    )

    try:

        quarterly_button = driver.find_element(
            By.CSS_SELECTOR,
            'button[data-tab-id="quarterly-insights"]'
        )

    except Exception as e:

        raise ValueError(
            "Quarterly Insights button "
            "was not found."
        ) from e

    driver.execute_script(
        "arguments[0].click();",
        quarterly_button
    )

    wait = WebDriverWait(
        driver,
        15
    )

    try:

        wait.until(
            EC.visibility_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "#quarterly-insights "
                    "table.data-table"
                )
            )
        )

    except Exception as e:

        raise ValueError(
            "Quarterly Insights table "
            "did not load."
        ) from e

    print(
        "Quarterly Insights loaded."
    )


# ==================================================
# Scrape Company
# ==================================================

def scrape_company(nse_code):
    """
    Scrape all required financial data
    for a company.

    Selenium is NOT closed here.
    """

    global driver

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

    # ==================================================
    # Open Company Page
    # ==================================================

    url = SCREENER_COMPANY_URL.format(
        nse_code
    )

    driver.get(url)

    # ==================================================
    # Get Company Name
    # ==================================================

    company_name = (
        driver.title
        .split(" share price")[0]
        .strip()
    )

    print(
        f"Company Name: {company_name}"
    )

    # ==================================================
    # Quarterly Insights
    # ==================================================

    load_quarterly_insights()

    quarterly_insights = extract_table(
        SECTION_IDS["quarterly_insights"]
    )

    print(
        f"Quarterly Insights: "
        f"{len(quarterly_insights)} rows"
    )

    # ==================================================
    # Profit & Loss
    # ==================================================

    print(
        "\nExtracting Profit & Loss..."
    )

    profit_loss = extract_table(
        SECTION_IDS["profit_loss"]
    )

    print(
        f"Profit & Loss: "
        f"{len(profit_loss)} rows"
    )

    # ==================================================
    # Balance Sheet
    # ==================================================

    print(
        "\nExtracting Balance Sheet..."
    )

    balance_sheet = extract_table(
        SECTION_IDS["balance_sheet"]
    )

    print(
        f"Balance Sheet: "
        f"{len(balance_sheet)} rows"
    )

    # ==================================================
    # Cash Flow
    # ==================================================

    print(
        "\nExtracting Cash Flow..."
    )

    cash_flow = extract_table(
        SECTION_IDS["cash_flow"]
    )

    print(
        f"Cash Flow: "
        f"{len(cash_flow)} rows"
    )

    # ==================================================
    # Finished
    # ==================================================

    print(
        "\n" + "=" * 80
    )

    print(
        f"Finished scraping: {nse_code}"
    )

    print(
        "=" * 80
    )

    # ==================================================
    # Return Data
    # ==================================================

    return {
        "company_name": company_name,
        "quarterly_insights": quarterly_insights,
        "profit_loss": profit_loss,
        "balance_sheet": balance_sheet,
        "cash_flow": cash_flow,
    }


# ==================================================
# Close Selenium
# ==================================================

def close_selenium():
    """
    Close Selenium.

    This should only be called when the API
    application shuts down.
    """

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