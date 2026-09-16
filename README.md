# Financial Insights for Companies on NSE — V3

A FastAPI application for retrieving, storing, and analyzing financial data for NSE-listed companies, sourced from Screener via Selenium and stored in PostgreSQL.

V3 builds on V2's Features engine by turning raw ratios into visual trend charts, and adds a rule-based **Fundamental Analysis** engine that reads those trends and produces an explainable POSITIVE / NEGATIVE / MIXED verdict, per category and overall — the first half of a larger "Is this company good to trade?" pipeline (the second half, a Technical Analysis aspect based on price/volume patterns, is planned for a later version).

> V1 (the original single-table Insights scraper) is preserved as the [`v1.0` release](../../releases/tag/v1.0).
> V2 (structured statements + computed ratios) is preserved as the [`v2.0` release](../../releases/tag/v2.0).

---

## What's new in V3

- **Restructured Features tab** — reorganized into four sections that better separate what's being measured:
  - **Profitability**: Effective Tax Rate, Sales, Net Profit, Operating Margin, Profit before Tax, Profit After Tax, EPS
  - **Cash Flow Quality**: Cash from Operating Activity (CFO), CFO Contribution, Cash Conversion
  - **Growth Trends**: Reserves, Equity Capital, Investment Migration, Borrowings-to-Net-Worth Ratio, Interest Coverage Ratio
  - **Other Metrics**: Total Liabilities vs Total Assets and Borrowings vs Total Assets, plotted as scatter charts with a visible trend direction (fading/growing points plus an arrow toward the latest period)
- **Chart.js-powered charts** — the Features tab now renders interactive line and scatter charts (via Chart.js, loaded from CDN) instead of static tables, with click-to-toggle legend chips per metric and dual/shared y-axes chosen per chart so differently-scaled metrics don't flatten each other
- **Fundamental Analysis engine** (`utils/trend_analyzer.py`) — a deterministic, rule-based layer on top of the Features data that:
  - Classifies each key metric's trend over a trailing 7-period window as improving / declining / mixed (tolerant of up to 2 "blip" periods, with a majority-direction safeguard)
  - Rolls trends up into five category verdicts — Profitability, Growth, Cash Flow, Leverage, Capital Allocation — each POSITIVE / NEGATIVE / MIXED with plain-language, explainable bullet reasons. Profitability includes an EPS dilution check (flags PAT rising without EPS keeping pace); Leverage includes Interest Coverage Ratio alongside Borrowings-to-Net-Worth
  - Rolls the five category verdicts up into one overall Fundamental Aspect verdict
  - All thresholds and rollup rules live in one documented config block at the top of the file, intended to be reviewed and tuned by the team rather than treated as fixed
- **New endpoint** — `GET /company/{nse_code}/fundamental-analysis`
- **Makefile** — `make install` (installs dependencies from `requirements.txt`) and `make run` (activates the venv and starts the server) for a faster local dev loop

---

## Architecture

```
                ┌──────────────────┐
                │   Web Interface  │
                │   index.html     │
                └────────┬─────────┘
                         │
                         ▼
                ┌──────────────────┐
                │     FastAPI      │
                │     Routes       │
                └────────┬─────────┘
                         │
          ┌──────────────┼───────────────┐
          │              │               │
          ▼              ▼               ▼
   ┌──────────────┐ ┌──────────┐ ┌───────────────────┐
   │ PostgreSQL   │ │ Selenium │ │ Fundamental        │
   │   Database   │ │ Scraper  │ │ Analysis Engine     │
   └──────────────┘ └────┬─────┘ │ (trend_analyzer.py) │
                          │       └───────────┬─────────┘
                          ▼                   │
                 ┌─────────────────┐          │
                 │    Screener     │◄─────────┘
                 └─────────────────┘   reads stored
                                        statements from DB
```
## Project structure

```
├── routes/
│   ├── company.py         # GET /company/{nse_code}, POST /company/{nse_code}/update
│   ├── insights.py        # GET /company/{nse_code}/insights
│   ├── profit_loss.py     # GET /company/{nse_code}/profit-loss
│   ├── balance_sheet.py   # GET /company/{nse_code}/balance-sheet
│   ├── cash_flow.py       # GET /company/{nse_code}/cash-flow
│   └── features.py        # GET /company/{nse_code}/features
│                           # GET /company/{nse_code}/fundamental-analysis
│
├── services/
│   └── company_service.py # DB-first, scrape-if-missing orchestration
│
├── models/
│   ├── company.py
│   ├── qres_insights.py
│   ├── profit_loss.py
│   ├── balance_sheet.py
│   └── cash_flow.py
│
├── utils/
│   ├── scraper.py         # Selenium session management + scraping
│   ├── database.py        # PostgreSQL connection & queries
│   ├── parser.py          # Parses scraped Screener data
│   ├── pivot.py           # Pivots period-metric rows into per-period dicts
│   ├── features.py        # Computes profitability/cash-flow/growth-trend/other metrics
│   ├── trend_analyzer.py  # Rule-based Fundamental Analysis engine
│   └── company_data.py
│
├── templates/
│   └── index.html
│
├── static/
│   ├── app.js              # Chart.js-based rendering for Features + Fundamental Analysis
│   └── style.css
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

Interactive docs available at `/docs` (Swagger UI) once the app is running.

---

## Technologies Used

- **Backend**: Python, FastAPI, Uvicorn
- **Web Scraping**: Selenium, Google Chrome / ChromeDriver
- **Data Processing**: Pandas
- **Database**: PostgreSQL, Psycopg
- **Frontend**: HTML, JavaScript, CSS, Chart.js (CDN)

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


4. Configure environment variables — copy `.env.example` to `.env` and fill in your PostgreSQL credentials:
```
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=your_database_name
   DB_USER=your_database_user
   DB_PASSWORD=your_database_password
```
   `.env` is gitignored and should never be committed.
   
5. Create the PostgreSQL database (the application initializes required tables on startup):
```sql
   CREATE DATABASE screener_db;
```

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
4. If not, a Selenium session (started lazily on first need) scrapes the company's Screener page.
5. Scraped data is parsed (`utils/parser.py`) and stored in PostgreSQL.
6. `utils/pivot.py` reshapes statement data by period for display; `utils/features.py` computes derived metrics on demand.
7. `utils/trend_analyzer.py` reads those same statements, classifies each key metric's trend over the trailing window, and rolls the results up into explainable category and overall Fundamental Analysis verdicts.
8. The `/update` endpoint re-scrapes on request, reusing the same Selenium session for efficiency.

---

## Security

- Database credentials are stored using environment variables, never hardcoded.
- `.env` is excluded from Git via `.gitignore`.
- No Screener login credentials are stored in source code — authentication (when required) is done manually through the Selenium-controlled browser.
- `.venv` and Python cache files are excluded from version control.
- `.env.example` contains placeholder values only.

---

## Future Improvements

- **Technical Analysis aspect** — price/volume pattern analysis, to be combined with the existing Fundamental Analysis aspect via AND logic into one final "good to trade?" verdict
- **LLM-generated narrative summaries** — a locally-run model (via llamafile) to turn the structured Fundamental Analysis output into readable prose, without taking over the underlying decision logic
- Validation of Fundamental Analysis thresholds across a larger set of companies
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
