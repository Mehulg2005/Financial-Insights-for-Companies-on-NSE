import os

from dotenv import load_dotenv


load_dotenv()


# --------------------------------------------------
# PostgreSQL configuration
# --------------------------------------------------

DB_NAME = os.getenv("DB_NAME")

DB_USER = os.getenv("DB_USER")

DB_PASSWORD = os.getenv("DB_PASSWORD")

DB_HOST = os.getenv("DB_HOST")

DB_PORT = os.getenv("DB_PORT")


# --------------------------------------------------
# Screener configuration
# --------------------------------------------------

SCREENER_LOGIN_URL = (
    "https://www.screener.in/login/"
)

SCREENER_COMPANY_URL = (
    "https://www.screener.in/company/{}/"
)