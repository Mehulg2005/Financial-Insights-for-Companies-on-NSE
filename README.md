# Financial Insights for Companies on NSE — V4

A FastAPI application for retrieving, storing, and analyzing financial data for NSE-listed companies, sourced from Screener (via Selenium) and Groww (for price charts), stored in PostgreSQL.

V4 is a full redesign of the web interface, plus two new pillars on top of V3's Fundamental Analysis engine: a **Distress Scores** module (Altman Z-Score, Beneish M-Score, Piotroski F-Score, Ohlson O-Score, Springate, Zmijewski) and a manually-curated **Concall Summaries** feature. It also lays the first groundwork for the planned Technical Analysis aspect via a new Market tab.

> **Internal tool, not for external/customer distribution.** Screener login is now fully automated using credentials configured in `.env` (see [Security](#security)) — this tradeoff is intentional for internal use only and should not be shipped to end users as-is.

> V1 (the original single-table Insights scraper) is preserved as the [`v1.0` release](../../releases/tag/v1.0).
> V2 (structured statements + computed ratios) is preserved as the [`v2.0` release](../../releases/tag/v2.0).
> V3 (Features tab redesign + Fundamental Analysis engine) is preserved as the [`v3.0` release](../../releases/tag/v3.0).

---

## What's new in V4

- **Redesigned web interface** — the old single-page `index.html` / `app.js` / `style.css` frontend is gone, replaced by a multi-page, Tailwind-styled interface: a shared `templates/base.html` shell (sidebar nav, top bar, shared title header) extended by per-tab templates (`overview.html`, `fundamentals.html`, `financials.html`, `market.html`), each with its own JS file, plus `static/shared.js` for cross-page helpers (chart palette, formatting, sync-timestamp rendering)
- **Collapsible sidebar** — persisted per-browser via `localStorage`, collapses to an icon-only rail
- **Fundamentals tab redesign** — the old Features tab's charts were restyled per-metric (clustered column + line for Sales/Net Profit, plain bar for CFO, stacked bar for Reserves/Equity Capital, stacked area for Total Liabilities/Total Assets, clustered bar for Effective Tax Rate/Operating Margin) and the "Fundamental Analysis" verdict card now renders as a plain heading instead of a bordered card
- **Distress Scores module** (`utils/distress_scores.py`, `routes/distress.py`) — computes six classic financial-distress/fraud-risk models (Altman Z-Score, Beneish M-Score, Piotroski F-Score, Ohlson O-Score, Springate, Zmijewski) from stored Profit & Loss, Balance Sheet, and Cash Flow data, with severity-colored cards and hover tooltips explaining each score's methodology
- **Concall Summaries** (`models/concall_documents.py`, `routes/concalls.py`) — rather than scraping Screener's company page for concall document links (unreliable markup), summaries are looked up from a manually-populated `concall_documents` table (`nse_code`, `period`, `document_no`) and fetched from `https://www.screener.in/concalls/summary/{document_no}/` directly. Fetched summaries are cached back into the same table (`summary` column) so repeat requests for the same document don't hit Screener again
- **Automated, headless Screener login** — Selenium now logs into Screener itself using `SCREENER_EMAIL` / `SCREENER_PASSWORD` from `.env`, with no manual browser interaction, and runs headless by default (`SELENIUM_HEADLESS=true`). Requests are paced in small batches with randomized delays and automatic retry-then-skip on a single blocked document, to avoid Cloudflare/bot-detection blocks. See [Security](#security) for the tradeoffs this introduces
- **Market tab (early stage)** — `templates/market.html` / `static/market.js`, the first piece of the planned Technical Analysis aspect
- **Price chart data source** — `services/price_service.py` / `routes/price.py` fetch price charts from Groww rather than Screener

---

## Architecture

```
                ┌─────────────────────────────────────────┐
                │              Web Interface              │
                │  base.html + overview/fundamentals/     │
                │  financials/market.html (Tailwind)      │
                └────────────────────┬────────────────────┘
                                     │
                                     ▼
                ┌───────────────────────────┐
                │          FastAPI          │
                │           Routes          │
                └───────────────────┬───────┘
                                    │
        ┌─────────────┬──────────────┼───────────────┬───────────────┐
        │             │              │               │               │
        ▼             ▼              ▼               ▼               ▼
 ┌────────────┐ ┌──────────┐ ┌────────────────┐ ┌─────────────┐ ┌─────────────┐
 │ PostgreSQL │ │ Selenium │ │ Fundamental    │ │  Distress   │ │    Groww    │
 │  Database  │ │ Scraper  │ │ Analysis       │ │  Scores     │ │ (price data)│
 └─────┬──────┘ └────┬─────┘ │ (trend_        │ │ (distress_  │ └─────────────┘
       │             │       │  analyzer.py)  │ │  scores.py) │
       │              ▼      └───────┬────────┘ └───────┬─────┘
       │      ┌──────────────┐       │                  │
       │      │   Screener   │◄──────┴──────────────────┘
       │      │ (statements, │   reads stored statements from DB
       │      │  concalls)   │
       │      └──────────────┘
       │
       └── concall_documents (nse_code, period, document_no, summary)
           manually populated; document_no drives direct concall
           summary fetches instead of scraping company-page links
```

## Project structure

```
├── routes/
│   ├── company.py         # GET /company/{nse_code}, POST /company/{nse_code}/update
│   ├── insights.py        # GET /company/{nse_code}/insights
│   ├── profit_loss.py     # GET /company/{nse_code}/profit-loss
│   ├── balance_sheet.py   # GET /company/{nse_code}/balance-sheet
│   ├── cash_flow.py       # GET /company/{nse_code}/cash-flow
│   ├── features.py        # GET /company/{nse_code}/features
│   │                       # GET /company/{nse_code}/fundamental-analysis
│   ├── distress.py        # GET /company/{nse_code}/distress-scores
│   ├── price.py           # GET /company/{nse_code}/price-chart
│   └── concalls.py        # GET /company/{nse_code}/concall-summaries
│
├── services/
│   ├── company_service.py # DB-first, scrape-if-missing orchestration
│   └── price_service.py   # Groww price chart fetching (range + intraday)
│
├── models/
│   ├── company.py
│   ├── qres_insights.py
│   ├── profit_loss.py
│   ├── balance_sheet.py
│   ├── cash_flow.py
│   └── concall_documents.py   # manually-populated document_no lookup + summary cache
│
├── utils/
│   ├── scraper.py           # Selenium session mgmt, automated login, scraping, concall fetch
│   ├── database.py          # PostgreSQL connection & queries
│   ├── parser.py            # Parses scraped Screener data
│   ├── pivot.py             # Pivots period-metric rows into per-period dicts
│   ├── features.py          # Computes profitability/cash-flow/growth-trend/other metrics
│   ├── trend_analyzer.py    # Rule-based Fundamental Analysis engine
│   ├── distress_scores.py   # Altman Z / Beneish M / Piotroski / Ohlson / Springate / Zmijewski
│   └── company_data.py
│
├── templates/
│   ├── base.html            # Shared shell: sidebar, top bar, title header
│   ├── landing.html
│   ├── overview.html
│   ├── fundamentals.html
│   ├── financials.html
│   └── market.html
│
├── static/
│   ├── base.js               # Sidebar/search/nav shell behavior
│   ├── shared.js              # Cross-page helpers (chart palette, formatting, sync label)
│   ├── overview.js
│   ├── fundamentals.js        # Charts + distress score cards + trend verdicts
│   ├── financials.js
│   └── market.js
│
├── test_parser.py
├── api.py
├── Makefile
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/company/{nse_code}` | Full company record — company info, quarterly insights, P&L, balance sheet, cash flow. Scrapes automatically if not in DB. |
| POST | `/company/{nse_code}/update` | Force a fresh scrape from Screener and update stored data. |
| GET | `/company/{nse_code}/insights` | Quarterly insights only. |
| GET | `/company/{nse_code}/profit-loss` | Profit & Loss statement, pivoted by period. |
| GET | `/company/{nse_code}/balance-sheet` | Balance Sheet, pivoted by period. |
| GET | `/company/{nse_code}/cash-flow` | Cash Flow statement, pivoted by period. |
| GET | `/company/{nse_code}/features` | Computed metrics: Profitability, Cash Flow Quality, Growth Trends, Other Metrics. |
| GET | `/company/{nse_code}/fundamental-analysis` | Rule-based trend analysis: per-category and overall POSITIVE / NEGATIVE / MIXED verdicts with explainable reasons. |
| GET | `/company/{nse_code}/distress-scores` | Altman Z, Beneish M, Piotroski F, Ohlson O, Springate, and Zmijewski scores, computed from stored statements (+ latest price from Groww for Altman Z's X4 term). |
| GET | `/company/{nse_code}/price-chart?mode=range\|live` | Price chart data from Groww — `range` (historical) or `live` (intraday polling). |
| GET | `/company/{nse_code}/concall-summaries` | Latest 6 concall summaries, resolved via the manually-populated `concall_documents` table; cached in DB after first fetch. |

Interactive docs available at `/docs` (Swagger UI) once the app is running.

---

## Technologies Used

- **Backend**: Python, FastAPI, Uvicorn
- **Web Scraping**: Selenium, Google Chrome / ChromeDriver
- **Data Processing**: Pandas
- **Database**: PostgreSQL, Psycopg
- **Frontend**: Jinja2 templates, Tailwind (CDN), vanilla JavaScript, Chart.js (CDN)

---

## Installation

1. Clone the repository
```bash
   git clone https://github.com/Mehulg2005/Financial-Insights-for-Companies-on-NSE.git
   cd Financial-Insights-for-Companies-on-NSE
```

2. Create a virtual environment
```bash
   python3 -m venv .venv
```

3. Install dependencies
Option 1:
```bash
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
```

Option 2:
```bash
   make install
```

4. Configure environment variables — copy `.env.example` to `.env` and fill in your PostgreSQL credentials and Screener credentials:
```
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=your_database_name
   DB_USER=your_database_user
   DB_PASSWORD=your_database_password

   SCREENER_EMAIL=your_screener_email
   SCREENER_PASSWORD=your_screener_password

   SELENIUM_HEADLESS=true
```
   `.env` is gitignored and should never be committed. See [Security](#security) before filling in Screener credentials.

5. Create the PostgreSQL database and required tables. The application does **not** auto-create its schema on startup — run these once:
```sql
   CREATE DATABASE screener_db;

   -- company, qres_insights, profit_loss, balance_sheet, cash_flow:
   -- see models/*.py for the exact columns each expects.

   CREATE TABLE concall_documents (
       id SERIAL PRIMARY KEY,
       nse_code TEXT NOT NULL,
       period TEXT NOT NULL,
       document_no TEXT NOT NULL,
       summary TEXT,
       last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
       UNIQUE (nse_code, period)
   );
```
   `concall_documents` rows are added manually — find a company's concall document number on Screener and insert `(nse_code, period, document_no)`; `summary` fills in automatically on first fetch.

## Running the application

Either directly:
```bash
uvicorn api:app --reload
```

Or via the Makefile:
```bash
make install   # first time only, or whenever requirements.txt changes
make run
```
Both targets activate the venv internally before running their command, so no separate activation step is needed — see the comments in `Makefile` for why this only works within a single line of a recipe, not as a standalone `activate` target.

- App: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`

---

## How it works

1. A user searches by NSE code (e.g. `RELIANCE`) via the web interface or API.
2. FastAPI checks PostgreSQL first.
3. If the company exists, stored data is returned directly.
4. If not, a Selenium session (started lazily, logging into Screener automatically via `.env` credentials) scrapes the company's Screener page.
5. Scraped data is parsed (`utils/parser.py`) and stored in PostgreSQL.
6. `utils/pivot.py` reshapes statement data by period for display; `utils/features.py` computes derived metrics on demand.
7. `utils/trend_analyzer.py` reads those same statements, classifies each key metric's trend over the trailing window, and rolls the results up into explainable category and overall Fundamental Analysis verdicts.
8. `utils/distress_scores.py` reads the same statements (plus latest price from Groww) to compute the six distress/fraud-risk scores.
9. For concalls: `models/concall_documents.py` is checked for cached document numbers/summaries for a company; anything not yet cached is fetched from Screener (in small paced batches, with retry-then-skip on a blocked document) and written back to the same table.
10. The `/update` endpoint re-scrapes on request, reusing the same Selenium session for efficiency.

---

## Security

- Database credentials are stored using environment variables, never hardcoded.
- **Screener login is automated for this internal tool.** `SCREENER_EMAIL` / `SCREENER_PASSWORD` are read from `.env` at startup and used to log Selenium into Screener with no manual step. This is a deliberate tradeoff for internal convenience — **do not** reuse this pattern for a tool that will be distributed outside the team, and treat the Screener account used here as a shared credential, not a personal one.
- `.env` is excluded from Git via `.gitignore`, and `.env.example` contains placeholder values only — never commit real values into either file or into any script.
- No secrets have been committed to this repository's history (checked before every version tag); if that ever changes, the affected credential must be rotated immediately, since removing a file from a later commit does **not** remove it from earlier commits still reachable in history.
- `.venv` and Python cache files are excluded from version control.
- `SELENIUM_HEADLESS=true` by default; set to `false` only for local debugging, since it makes the automated-login browser window visible.

---

## Future Improvements

- **Technical Analysis aspect** — the Market tab is the first step; price/volume pattern analysis is still to come, to be combined with the existing Fundamental Analysis aspect via AND logic into one final "good to trade?" verdict
- **LLM-generated narrative summaries** — a locally-run model (via llamafile) to turn the structured Fundamental Analysis output, Distress Scores, and Concall Summaries into readable prose, without taking over the underlying decision logic
- Validation of Fundamental Analysis and Distress Score thresholds across a larger set of companies
- A lighter-weight way to populate `concall_documents` (currently manual) — e.g. a small admin form instead of direct SQL inserts
- Automated scheduled data updates
- Additional financial data sources
- More advanced filtering and cross-company comparison
- User authentication
- Cloud deployment
- Automated testing (expand on `test_parser.py`)
- Containerization using Docker

---

## Author

**Mehul Gupta**
GitHub: [https://github.com/Mehulg2005](https://github.com/Mehulg2005)