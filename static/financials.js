/* =========================================
   FINANCIALS PAGE

   Fetches the full company record once, then renders one
   FULL-history statement table at a time (no truncation,
   unlike Overview's 4-period preview), switched via the
   same toggle pattern used on Overview.
========================================= */

let financialsData = null;
let activeFinancialsTable = "profit_loss";

const FINANCIALS_TABLE_KEYS = {
    profit_loss: "profit_loss",
    balance_sheet: "balance_sheet",
    cash_flow: "cash_flow",
    quarterly_insights: "quarterly_insights",
};


async function loadFinancials(nseCode) {

    try {

        const response = await fetch(`/company/${nseCode}`);

        if (!response.ok) {
            throw new Error("Company not found");
        }

        financialsData = await response.json();

        renderTitleCard(financialsData);

        const asOfLabel = document.getElementById("financialsAsOfLabel");

        if (asOfLabel) {
            asOfLabel.textContent = formatSyncDateLabel();
        }

        renderFinancialsTable(activeFinancialsTable);

    }

    catch (error) {

        console.error("loadFinancials failed:", error);

        const errorMessage = document.getElementById("errorMessage");

        if (errorMessage) {
            errorMessage.textContent = error.message;
        }

    }

}


function renderFinancialsTable(tableKey) {

    if (!financialsData) {
        return;
    }

    activeFinancialsTable = tableKey;

    document.querySelectorAll(".preview-table-toggle").forEach(button => {
        button.classList.toggle("active", button.dataset.table === tableKey);
    });

    const dataKey = FINANCIALS_TABLE_KEYS[tableKey];

    renderPivotTable(
        "financialsTableHead",
        "financialsTableBody",
        financialsData[dataKey]
    );

}


document.querySelectorAll(".preview-table-toggle").forEach(button => {

    button.addEventListener("click", () => {
        renderFinancialsTable(button.dataset.table);
    });

});


if (CURRENT_NSE_CODE) {
    loadFinancials(CURRENT_NSE_CODE);
}