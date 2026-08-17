# Financial Insights for Companies on NSE

A Python-based financial data application that retrieves company Insights data from Screener, stores it in PostgreSQL, and provides access to the data through a FastAPI backend and web interface.

The application uses Selenium to retrieve Insights data for NSE-listed companies when the required company data is not available in the database or when an update is requested.

---

## Features

- Search companies using their NSE code
- Retrieve existing company data from PostgreSQL
- Scrape company Insights data from Screener using Selenium
- Automatically add newly discovered company data to PostgreSQL
- Update existing company records through a dedicated update operation
- Track the last updated time for company data
- REST API built using FastAPI
- Interactive API documentation through Swagger UI
- HTML-based frontend for searching and updating company data
- Structured project architecture separating routes, utilities, database models, and configuration
- No CSV files are required for the application's data storage

---

## Architecture

```text
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
'''

Search workflow
When a user searches for an NSE code:

1. The frontend sends the NSE code to the FastAPI backend.
2. The backend checks PostgreSQL.
3. If the company exists, the stored information is returned.
4. If the company does not exist, Selenium accesses Screener.
5. The Insights data is extracted and processed.
6. The data is stored in PostgreSQL.
7. The newly stored data is returned to the user.

Update workflow
When the user requests an update:

1. The application checks whether Selenium is available.
2. Selenium accesses the company’s Screener page.
3. The latest Insights data is extracted.
4. The data is processed.
5. PostgreSQL is updated with new or changed records.
6. The company’s last updated timestamp is updated.

Database Design
The application uses PostgreSQL as its persistent data store.
The primary Insights table follows a normalized structure:

Column			|	Description
------------------------+--------------------------------------------------
nse_code		|	NSE code of the company
company_name		|	Name of the company
metric			|	Name of the financial/operational metric
period			|	Reporting period
value			|	Value recorded for the metric
last_updated		|	Timestamp of the latest update


Example:
nse_code    | company_name        | metric                      | period    | value
------------|---------------------|-----------------------------|-----------|-------
RELIANCE    | Reliance Industries | Reliance Retail Store Count | Mar 2025  | 19340


The normalized structure allows new reporting periods to be added as rows rather than requiring a new database column for every period.


Project Structure
Financial Insights for Companies on NSE/
│
├── routes/
│   ├── __init__.py
│   ├── search.py
│   └── update.py
│
├── utils/
│   ├── __init__.py
│   ├── data_processor.py
│   ├── database.py
│   └── selenium_scraper.py
│
├── models/
│   ├── __init__.py
│   └── screener_db.py
│
├── templates/
│   └── index.html
│
├── api.py
├── config.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md

routes/

Contains FastAPI route definitions.

* search.py — handles company search requests
* update.py — handles company data update requests

utils/

Contains reusable application functionality.

* selenium_scraper.py — handles Selenium-based data extraction
* database.py — handles PostgreSQL operations
* data_processor.py — processes and structures scraped data

models/

Contains database-related model definitions.

* screener_db.py — defines the database table structure

templates/

Contains the frontend HTML.

* index.html — web interface for searching and updating company information

config.py

Contains application configuration loaded from environment variables.

api.py

The main FastAPI application that connects the routes, database initialization, and frontend.

⸻

Technologies Used

Backend

* Python
* FastAPI
* Uvicorn

Web Scraping

* Selenium
* Google Chrome / ChromeDriver

Data Processing

* Pandas

Database

* PostgreSQL
* Psycopg

Frontend

* HTML
* JavaScript
* CSS

Development

* Python Virtual Environment
* Git
* GitHub

⸻

Installation

1. Clone the repository
git clone https://github.com/Mehulg2005/Financial-Insights-for-Companies-on-NSE.git

Navigate into the project:
cd "Financial-Insights-for-Companies-on-NSE"

2. Create a virtual environment
python3 -m venv .venv
Activate it on macOS/Linux:
source .venv/bin/activate
On Windows:
.venv\Scripts\activate

3. Install dependencies
pip install -r requirements.txt

Configuration

The application uses environment variables for database configuration.

Create a .env file in the project root:
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=5432

The .env file should not be committed to GitHub.

A .env.example file is included in the repository as a configuration template.

PostgreSQL Setup

Create the PostgreSQL database:
CREATE DATABASE screener_db;

The application initializes the required database table when it starts.

The main table is:
insights

The table stores company metrics in the following form:
NSE Code
Company Name
Metric
Period
Value
Last Updated

Running the Application

Make sure the virtual environment is activated:
source .venv/bin/activate

Start the FastAPI application:
uvicorn api:app --reload

The application will be available at:
http://127.0.0.1:8000

Open this address in a browser to access the web interface.

⸻

API Documentation

FastAPI automatically provides interactive API documentation.

Swagger UI:
http://127.0.0.1:8000/docs

OpenAPI documentation:
http://127.0.0.1:8000/openapi.json

Selenium Authentication

The application uses Selenium to access Screener.

Screener authentication is performed manually through the browser rather than storing Screener login credentials inside the source code.

When Selenium requires authentication, the browser can be used to complete the login before scraping begins.

⸻

Data Handling

The application does not use CSV files as its persistent storage layer.

Scraped data follows this process:
Screener
    ↓
Selenium
    ↓
Data Processing
    ↓
PostgreSQL

PostgreSQL serves as the central data store for all companies.

This allows data from multiple NSE-listed companies to be stored in a single database while maintaining a consistent schema.

⸻

Example Search

A user can search using an NSE code such as:
RELIANCE

If the company is already present:
User
 ↓
FastAPI
 ↓
PostgreSQL
 ↓
Company data

If the company is not present:
User
 ↓
FastAPI
 ↓
PostgreSQL
 ↓
Company not found
 ↓
Selenium
 ↓
Screener
 ↓
Data processing
 ↓
PostgreSQL
 ↓
Company data

Security

The project follows the following security practices:

* Database credentials are stored using environment variables.
* .env is excluded from Git using .gitignore.
* No Screener login credentials are stored in the source code.
* .venv and Python cache files are excluded from version control.
* .env.example contains only placeholder configuration values.

Never commit passwords, API keys, authentication tokens, or other secrets to the repository.

⸻

Future Improvements

Potential future improvements include:

* Automated scheduled data updates
* Improved authentication handling
* Additional financial data sources
* More advanced filtering and search
* Data visualization and financial trend analysis
* User authentication
* Deployment to a cloud environment
* Automated testing
* Containerization using Docker

⸻

Author

Mehul Gupta

GitHub:
https://github.com/Mehulg2005
