# --------------------------------------------------
# PostgreSQL table definition
# --------------------------------------------------

TABLE_NAME = "insights"


CREATE_TABLE_QUERY = """
CREATE TABLE IF NOT EXISTS insights (

    id SERIAL PRIMARY KEY,

    nse_code VARCHAR(20) NOT NULL,

    company_name TEXT NOT NULL,

    metric TEXT NOT NULL,

    period VARCHAR(50) NOT NULL,

    value TEXT,

    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (
        nse_code,
        metric,
        period
    )
);
"""


CREATE_INDEX_QUERY = """
CREATE INDEX IF NOT EXISTS idx_insights_nse_code
ON insights(nse_code);
"""