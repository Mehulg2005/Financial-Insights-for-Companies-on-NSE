# Financial Insights for Companies on NSE — V2

A FastAPI application for retrieving, storing, and analyzing financial data for NSE-listed companies, sourced from Screener via Selenium and stored in PostgreSQL.

V2 builds on the original scraping + storage pipeline by adding structured financial statements (Profit & Loss, Balance Sheet, Cash Flow) and a derived **Features** engine that computes profitability, growth, leverage, and cash-flow-quality ratios from that data.

> V1 (the original single-table Insights scraper) is preserved as the [`v1.0` release](../../releases/tag/v1.0).

---

## What's new in V2

- **Structured financial statements** — dedicated models/routes for Profit & Loss, Balance Sheet, and Cash Flow (previously only generic "Insights" existed)
- **Computed Features** — an analysis layer (`utils/features.py`) that derives:
  - **Profitability**: Operating Margin, Net Profit Margin, Effective Tax Rate
  - **Growth**: Sales Growth, Net Profit Growth, EPS Growth (period-over-period)
  - **Leverage**: Debt to Equity, Total Liabilities to Equity
  - **Cash Flow Quality**: Cash Conversion (CFO / Net Profit), Operating Cash Margin
- **Pivoted period views** — `utils/pivot.py` reshapes raw metric rows into one row per reporting period for easier consumption
- **Service layer** — `services/company_service.py` centralizes the "fetch from DB, else scrape" logic previously spread across routes
- **Lazy Selenium session** — the scraper only launches on first use (a missing company search or an explicit update), and the session is reused across requests until shutdown
- **Refreshed frontend** — updated `static/app.js` / `static/style.css` and `templates/index.html`

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
                    ┌────────┴─────────┐
                    │                  │
                    ▼                  ▼
             ┌──────────────┐   ┌──────────────┐
             │ PostgreSQL   │   │   Selenium   │
             │   Database   │   │   Scraper    │
             └──────────────┘   └──────┬───────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │    Screener     │
                              └─────────────────┘
```

## Project structure

```
Screener Project V2/
│
├── routes/
│   ├── company.py         # GET /company/{nse_code}, POST /company/{nse_code}/update
│   ├── insights.py        # GET /company/{nse_code}/insights
│   ├── profit_loss.py     # GET /company/{nse_code}/profit-loss
│   ├── balance_sheet.py   # GET /company/{nse_code}/balance-sheet
│   ├── cash_flow.py       # GET /company/{nse_code}/cash-flow
│   └── features.py        # GET /company/{nse_code}/features
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
│   ├── features.py        # Computes profitability/growth/leverage/cash-flow ratios
│   └── company_data.py
│
├── templates/
│   └── index.html
│
├── static/
│   ├── app.js
│   └── style.css
│
├── test_parser.py
├── api.py
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
| GET | `/company/{nse_code}/features` | Computed ratios: profitability, growth, leverage, cash flow quality. |

Interactive docs available at `/docs` (Swagger UI) once the app is running.

---

## Technologies Used

- **Backend**: Python, FastAPI, Uvicorn
- **Web Scraping**: Selenium, Google Chrome / ChromeDriver
- **Data Processing**: Pandas
- **Database**: PostgreSQL, Psycopg
- **Frontend**: HTML, JavaScript, CSS

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
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
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

```bash
uvicorn api:app --reload
```

- App: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`

---

## How it works

1. A user searches by NSE code (e.g. `RELIANCE`) via the web interface or API.
2. FastAPI checks PostgreSQL first.
3. If the company exists, stored data is returned directly.
4. If not, a Selenium session (started lazily on first need) scrapes the company's Screener page.
5. Scraped data is parsed (`utils/parser.py`) and stored in PostgreSQL.
6. `utils/pivot.py` reshapes statement data by period for display; `utils/features.py` computes derived ratios on demand.
7. The `/update` endpoint re-scrapes on request, reusing the same Selenium session for efficiency.

---

## Security

- Database credentials are stored using environment variables, never hardcoded.
- `.env` is excluded from Git via `.gitignore`.
- No Screener login credentials are stored in source code — authentication (when required) is done manually through the Selenium-controlled browser.
- `.venv` and Python cache files are excluded from version control.
- `.env.example` contains placeholder values only.

---

## Future Improvements

- Automated scheduled data updates
- Additional financial data sources
- More advanced filtering and cross-company comparison
- Data visualization / trend charts
- User authentication
- Cloud deployment
- Automated testing (expand on `test_parser.py`)
- Containerization using Docker

---

## Author

**Mehul Gupta**
GitHub: [https://github.com/Mehulg2005](https://github.com/Mehulg2005)
