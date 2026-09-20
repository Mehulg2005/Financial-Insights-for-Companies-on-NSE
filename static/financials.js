/* =========================================
   FINANCIALS PAGE

   Fetches the full company record and renders all four
   statement tables with their FULL period history -
   unlike Overview's preview table, nothing here is
   truncated to a recent window.
========================================= */

async function loadFinancials(nseCode) {

    try {

        const response = await fetch(`/company/${nseCode}`);

        if (!response.ok) {
            throw new Error("Company not found");
        }

        const data = await response.json();

        renderTitleCard(data);

        renderPivotTable("plHead", "plBody", data.profit_loss);
        renderPivotTable("bsHead", "bsBody", data.balance_sheet);
        renderPivotTable("cfHead", "cfBody", data.cash_flow);
        renderPivotTable("qiHead", "qiBody", data.quarterly_insights);

    }

    catch (error) {

        console.error("loadFinancials failed:", error);

        const errorMessage = document.getElementById("errorMessage");

        if (errorMessage) {
            errorMessage.textContent = error.message;
        }

    }

}


if (CURRENT_NSE_CODE) {
    loadFinancials(CURRENT_NSE_CODE);
}