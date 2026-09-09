from models.company import get_company_by_nse
from models.qres_insights import get_insights
from models.profit_loss import get_profit_loss
from models.balance_sheet import get_balance_sheet
from models.cash_flow import get_cash_flow


def get_company_data(nse_code):
    """
    Retrieve all stored financial data for a company.
    """

    company = get_company_by_nse(nse_code)

    if not company:
        return None

    return {
        "company": company,
        "quarterly_insights": get_insights(nse_code),
        "profit_loss": get_profit_loss(nse_code),
        "balance_sheet": get_balance_sheet(nse_code),
        "cash_flow": get_cash_flow(nse_code),
    }