/* =========================================
   OVERVIEW PAGE

   Fetches the full company record once, populates the
   title card, renders the summary cards, and renders a
   single toggleable statement table limited to the most
   recent PREVIEW_PERIOD_LIMIT periods - full history
   lives on the Financials page instead.
========================================= */

let overviewData = null;
let activePreviewTable = "profit_loss";

const PREVIEW_PERIOD_LIMIT = 4;

const PREVIEW_TABLE_CONFIG = {
    profit_loss: { key: "profit_loss", head: "previewTableHead", body: "previewTableBody" },
    balance_sheet: { key: "balance_sheet", head: "previewTableHead", body: "previewTableBody" },
    cash_flow: { key: "cash_flow", head: "previewTableHead", body: "previewTableBody" },
    quarterly_insights: { key: "quarterly_insights", head: "previewTableHead", body: "previewTableBody" },
};


async function loadOverview(nseCode) {

    try {

        const response = await fetch(`/company/${nseCode}`);

        if (!response.ok) {
            throw new Error("Company not found");
        }

        overviewData = await response.json();

        renderTitleCard(overviewData);
        renderSummaryCards(overviewData);
        renderPreviewTable(activePreviewTable);

    }

    catch (error) {

        console.error("loadOverview failed:", error);

        const errorMessage = document.getElementById("errorMessage");

        if (errorMessage) {
            errorMessage.textContent = error.message;
        }

    }

}


function renderTitleCard(data) {

    const company = data.company || {};

    const nameEl = document.getElementById("titleCardCompanyName");
    const syncEl = document.getElementById("titleCardSyncLabel");

    if (nameEl && company.company_name) {
        nameEl.textContent = company.company_name;
    }

    if (syncEl) {
        syncEl.textContent = formatSyncTimestamp();
    }

}


function renderSummaryCards(data) {

    const profitLoss = data.profit_loss;

    if (!profitLoss || profitLoss.length === 0) {
        return;
    }

    const latestPeriod = profitLoss[profitLoss.length - 1].period;

    const latestRecords = profitLoss.filter(
        record => record.period === latestPeriod
    );

    function getMetric(names) {

        const record = latestRecords.find(r => names.includes(r.metric));

        return record ? record.value : null;

    }

    const salesEl = document.getElementById("cardRevenue");
    const netProfitEl = document.getElementById("cardNetProfit");
    const epsEl = document.getElementById("cardEPS");
    const opmEl = document.getElementById("cardOperatingMargin");

    if (salesEl) {
        salesEl.textContent = formatNumber(getMetric(["Sales", "Revenue"]));
    }

    if (netProfitEl) {
        netProfitEl.textContent = formatNumber(getMetric(["Net Profit", "Net profit"]));
    }

    if (epsEl) {
        epsEl.textContent = formatNumber(getMetric(["EPS in Rs", "EPS"]));
    }

    if (opmEl) {
        opmEl.textContent = formatPercent(getMetric(["OPM %"]));
    }

}


function limitToLastNPeriods(records, n) {

    if (!records || records.length === 0) {
        return records;
    }

    const periodsInOrder = [];
    const periodSeen = new Set();

    records.forEach(record => {

        if (!periodSeen.has(record.period)) {
            periodSeen.add(record.period);
            periodsInOrder.push(record.period);
        }

    });

    const lastPeriods = new Set(periodsInOrder.slice(-n));

    return records.filter(record => lastPeriods.has(record.period));

}


function renderPreviewTable(tableKey) {

    if (!overviewData) {
        return;
    }

    activePreviewTable = tableKey;

    document.querySelectorAll(".preview-table-toggle").forEach(button => {
        button.classList.toggle("active", button.dataset.table === tableKey);
    });

    const config = PREVIEW_TABLE_CONFIG[tableKey];

    const limitedRecords = limitToLastNPeriods(
        overviewData[config.key],
        PREVIEW_PERIOD_LIMIT
    );

    renderPivotTable(
        config.head,
        config.body,
        limitedRecords
    );

}


document.querySelectorAll(".preview-table-toggle").forEach(button => {

    button.addEventListener("click", () => {
        renderPreviewTable(button.dataset.table);
    });

});


if (CURRENT_NSE_CODE) {
    loadOverview(CURRENT_NSE_CODE);
}