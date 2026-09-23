import os
import random
import time

from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from models.concall_documents import get_latest_documents


# ==================================================
# Environment / credentials
# ==================================================

load_dotenv()

SCREENER_EMAIL = os.getenv("SCREENER_EMAIL", "")
SCREENER_PASSWORD = os.getenv("SCREENER_PASSWORD", "")

# Set SELENIUM_HEADLESS=false in .env to see the browser window.
SELENIUM_HEADLESS = (
    os.getenv("SELENIUM_HEADLESS", "true").strip().lower() != "false"
)


# ==================================================
# Screener URLs
# ==================================================

SCREENER_LOGIN_URL = "https://www.screener.in/login/"

SCREENER_COMPANY_URL = (
    "https://www.screener.in/company/{}/"
)

SCREENER_COMPANY_URL = (
    "https://www.screener.in/company/{}/consolidated/"
)

SCREENER_CONCALL_SUMMARY_URL = (
    "https://www.screener.in/concalls/summary/{}/"
)

# How many concall summary pages to load back-to-back before
# pausing. A short burst is fine; it's long unbroken bursts that
# trigger Screener/Cloudflare's bot-detection blocks.
CONCALL_BATCH_SIZE = 3
CONCALL_BATCH_GAP = (2.0, 3.0)

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


def _login_to_screener():
    """
    Fill in and submit Screener's login form using the
    credentials configured in .env, then wait until the
    browser has navigated away from the login page.

    No manual keyboard interaction is required.
    """

    if not SCREENER_EMAIL or not SCREENER_PASSWORD:
        raise ValueError(
            "SCREENER_EMAIL and SCREENER_PASSWORD must be set "
            "in .env for automated login."
        )

    wait = WebDriverWait(driver, 20)

    email_field = wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[name='username']")
        )
    )

    password_field = driver.find_element(
        By.CSS_SELECTOR,
        "input[name='password']"
    )

    email_field.clear()
    email_field.send_keys(SCREENER_EMAIL)

    password_field.clear()
    password_field.send_keys(SCREENER_PASSWORD)

    submit_button = driver.find_element(
        By.CSS_SELECTOR,
        "button[type='submit']"
    )

    driver.execute_script(
        "arguments[0].click();",
        submit_button
    )

    # Screener redirects away from /login/ once authenticated.
    wait.until(
        lambda current_driver: "/login/" not in current_driver.current_url
    )


def start_selenium():
    """
    Start Selenium only if it is not already running.

    Once started, Selenium remains alive until
    close_selenium() is explicitly called.

    Login is automated using SCREENER_EMAIL / SCREENER_PASSWORD
    from .env - no manual browser interaction is required.
    """

    global driver

    if driver is not None:

        try:
            driver.current_url

            print(
                "Selenium already running. "
                "Reusing existing session."
            )

            return driver

        except Exception:
            driver = None

    print("\nStarting Selenium...")

    options = Options()

    options.add_argument(
        "--start-maximized"
    )

    if SELENIUM_HEADLESS:

        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")

    # Reduce obvious automation fingerprints (helps avoid
    # bot-detection blocks when navigating several pages quickly).
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    )
    options.add_experimental_option(
        "excludeSwitches",
        ["enable-automation"]
    )
    options.add_experimental_option(
        "useAutomationExtension",
        False
    )

    driver = webdriver.Chrome(
        options=options
    )

    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": (
                "Object.defineProperty(navigator, 'webdriver', "
                "{get: () => undefined});"
            )
        }
    )

    driver.get(
        SCREENER_LOGIN_URL
    )

    _login_to_screener()

    print(
        "Screener login completed."
    )

    print(
        "Selenium is ready."
    )

    return driver


# ==================================================
# Read visible table
# ==================================================


def _read_table(table):
    """
    Read a Selenium table into the same raw matrix format
    expected by the existing parser.
    """

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

    return data


# ==================================================
# Find company ID and fetch schedule data
# ==================================================


def _fetch_schedule_data(section_id, parents, periods):
    """
    Fetch Screener's hidden schedule rows through the
    authenticated Selenium browser session.

    Screener returns an object shaped like:

        {
            "Trade receivables": {
                "Mar 2025": "42,121",
                "Mar 2026": "58,491"
            }
        }

    The result is converted into raw table rows such as:

        [
            [
                "Trade receivables",
                "42,121",
                "58,491"
            ]
        ]
    """

    global driver

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

            const allElements = document.querySelectorAll("*");

            for (const element of allElements) {
                for (const attribute of element.attributes) {
                    const match = attribute.value.match(
                        /(?:company|screener)[_-]?id[^0-9]+(\\d+)/i
                    );

                    if (match) {
                        return match[1];
                    }
                }
            }

            return null;
        }

        async function loadSchedules() {
            const companyId = findCompanyId();

            if (!companyId) {
                throw new Error(
                    "Could not find Screener company ID."
                );
            }

            const schedules = {};

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

                schedules[parent] = await response.json();
            }

            return schedules;
        }

        loadSchedules()
            .then(schedules => {
                done({
                    ok: true,
                    schedules: schedules
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

    if not schedule_result:
        raise ValueError(
            "Screener schedule request returned no result."
        )

    if not schedule_result.get("ok"):
        raise ValueError(
            "Could not fetch Screener schedule rows: "
            f"{schedule_result.get('error', 'Unknown error')}"
        )

    schedules = schedule_result.get(
        "schedules",
        {}
    )

    child_rows = []

    for parent in parents:

        payload = schedules.get(parent)

        if not isinstance(payload, dict):
            print(
                f"No dictionary schedule returned for "
                f"'{parent}'."
            )

            continue

        for metric_name, values_by_period in payload.items():

            if not isinstance(values_by_period, dict):
                continue

            row = [metric_name]

            for period in periods:
                row.append(
                    values_by_period.get(
                        period,
                        ""
                    )
                )

            child_rows.append(row)

    return child_rows


# ==================================================
# Extract table from a section
# ==================================================


def extract_table(section_id):
    """
    Extract a Screener statement table.

    For the Profit & Loss and Balance Sheet sections,
    fetch hidden child metrics through Screener's schedule API.
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
            f"No data table found inside section "
            f"'{section_id}'."
        )

    table = tables[0]

    data = _read_table(table)

    if not data:
        raise ValueError(
            f"No data found inside section "
            f"'{section_id}'."
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

    if len(data[0]) < 2:
        raise ValueError(
            f"Could not identify periods in section "
            f"'{section_id}'."
        )

    periods = [
        str(period).strip()
        for period in data[0][1:]
    ]

    child_rows = _fetch_schedule_data(
        section_id,
        parents,
        periods
    )

    existing_metrics = {
        row[0].strip().lower()
        for row in data[1:]
        if row and row[0].strip()
    }

    imported_metrics = []

    for child_row in child_rows:

        if not child_row:
            continue

        metric_name = child_row[0].strip()

        if not metric_name:
            continue

        metric_key = metric_name.lower()

        if metric_key in existing_metrics:
            continue

        data.append(child_row)
        existing_metrics.add(metric_key)
        imported_metrics.append(metric_name)

    print(
        f"Schedule metrics imported for {section_id}: "
        f"{imported_metrics}"
    )

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

    except Exception as error:
        raise ValueError(
            "Quarterly Insights button "
            "was not found."
        ) from error

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

    except Exception as error:
        raise ValueError(
            "Quarterly Insights table "
            "did not load."
        ) from error

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

    Selenium is not closed here.
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

    url = SCREENER_COMPANY_URL.format(
        nse_code
    )

    driver.get(url)

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

    print(
        "\n" + "=" * 80
    )

    print(
        f"Finished scraping: {nse_code}"
    )

    print(
        "=" * 80
    )

    return {
        "company_name": company_name,
        "quarterly_insights": quarterly_insights,
        "profit_loss": profit_loss,
        "balance_sheet": balance_sheet,
        "cash_flow": cash_flow,
    }

# ==================================================
# Concall summaries
# ==================================================

def _concall_content():
    """
    Extract the authenticated concall-summary page content.
    """

    selectors = (
        "article",
        ".concalls-summary",
        "[class*='summary']",
        "#content",
        "main",
        ".card",
    )

    candidates = []
    seen_text = set()

    for selector in selectors:
        elements = driver.find_elements(
            By.CSS_SELECTOR,
            selector,
        )

        for element in elements:
            text = element.text.strip()

            if text and text not in seen_text:
                seen_text.add(text)
                candidates.append(text)

    if candidates:
        return max(candidates, key=len)

    return driver.find_element(
        By.TAG_NAME,
        "body",
    ).text.strip()


def _load_concall_summary(document_no, wait):
    """
    Load a single concall summary page and return its content.

    Returns None (rather than raising) if the page was blocked
    (e.g. a 403 / bot-detection interstitial), so the caller can
    back off, retry, or skip just this one document. A genuine
    logged-out session (redirect to /login/) still raises, since
    that affects every remaining document too.
    """

    global driver

    summary_url = SCREENER_CONCALL_SUMMARY_URL.format(
        document_no
    )

    driver.get(summary_url)

    wait.until(
        EC.presence_of_element_located(
            (By.TAG_NAME, "body")
        )
    )

    if "/login/" in driver.current_url:
        raise ValueError(
            "Screener login is required to access concall summaries."
        )

    title = (driver.title or "").lower()
    body_preview = driver.find_element(
        By.TAG_NAME,
        "body"
    ).text[:300].lower()

    blocked_markers = (
        "403",
        "forbidden",
        "access denied",
        "just a moment",
        "attention required",
    )

    if any(marker in title for marker in blocked_markers):
        return None

    if any(marker in body_preview for marker in blocked_markers):
        return None

    content = _concall_content()

    return content or None


def fetch_latest_concall_summaries(nse_code, limit=6):
    """
    Fetch the latest available Screener concall summaries.

    Document numbers are read from the manually-populated
    concall_documents table (see models/concall_documents.py)
    instead of being scraped off Screener's company page, since
    that page's markup for locating summary links is unreliable.

    Data is returned in memory only.
    Nothing is stored in PostgreSQL.
    """

    if limit <= 0:
        return []

    global driver

    if driver is None:
        start_selenium()

    nse_code = nse_code.upper().strip()

    documents = get_latest_documents(
        nse_code,
        limit=limit
    )

    if not documents:
        raise ValueError(
            f"No concall documents found for {nse_code} in "
            "concall_documents. Add rows for this company first."
        )

    wait = WebDriverWait(driver, 20)

    summaries = []
    failed_periods = []

    total_batches = -(-len(documents) // CONCALL_BATCH_SIZE)  # ceil div

    for batch_index in range(total_batches):

        batch_start = batch_index * CONCALL_BATCH_SIZE
        batch = documents[batch_start:batch_start + CONCALL_BATCH_SIZE]

        for document in batch:

            document_no = document["document_no"]
            period = document["period"]

            content = _load_concall_summary(document_no, wait)

            if content is None:
                # First attempt was blocked (403) - back off and
                # retry once before giving up on this document.
                time.sleep(random.uniform(3.0, 5.0))
                content = _load_concall_summary(document_no, wait)

            if content is None:
                print(
                    f"Skipping concall summary {document_no} "
                    f"({period}): blocked after retry."
                )
                failed_periods.append(period)
                continue

            summary_url = SCREENER_CONCALL_SUMMARY_URL.format(
                document_no
            )

            summaries.append(
                {
                    "id": document_no,
                    "period": period,
                    "url": summary_url,
                    "content": content,
                }
            )

        # Pause between batches (not after the last one) so the
        # whole run doesn't look like one long unbroken burst.
        if batch_index < total_batches - 1:
            time.sleep(random.uniform(*CONCALL_BATCH_GAP))

    if failed_periods:
        print(
            "Concall summaries could not be fetched for: "
            f"{', '.join(failed_periods)}"
        )

    return summaries

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