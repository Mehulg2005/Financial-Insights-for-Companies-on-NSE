const API_BASE = "http://127.0.0.1:8000";


const searchButton = document.getElementById("searchButton");
const updateButton = document.getElementById("updateButton");
const nseInput = document.getElementById("nseInput");

const companySection = document.getElementById("companySection");
const errorMessage = document.getElementById("errorMessage");


/* =========================================
   SEARCH
========================================= */

searchButton.addEventListener("click", searchCompany);


nseInput.addEventListener("keydown", function (event) {

    if (event.key === "Enter") {
        searchCompany();
    }

});


async function searchCompany() {

    const nseCode = nseInput.value.trim().toUpperCase();

    if (!nseCode) {
        showError("Please enter an NSE code.");
        return;
    }

    clearError();

    setLoading(searchButton, true, "Loading...");
    updateButton.disabled = true;
    try {

        const response = await fetch(
            `${API_BASE}/company/${nseCode}`
        );


        if (!response.ok) {

            const error = await response.json();

            throw new Error(
                error.detail || "Company not found"
            );

        }


        const data = await response.json();

        displayCompany(data);

        loadFeatures(nseCode);

    }

    catch (error) {

        companySection.classList.add("hidden");

        showError(error.message);

    }

    finally {
        setLoading(searchButton, false, "Search");
        updateButton.disabled = false;
    }

}


/* =========================================
   UPDATE
   Always-available action: re-scrapes Screener for
   whatever NSE code is currently in the search box
   (whether or not it's already in the database) and
   stores + displays the refreshed data. Reuses an
   already-open Selenium/Screener session if present.
========================================= */

updateButton.addEventListener("click", updateCompany);


async function updateCompany() {

    const nseCode = nseInput.value.trim().toUpperCase();

    if (!nseCode) {
        showError("Please enter an NSE code.");
        return;
    }

    clearError();

    setLoading(updateButton, true, "Updating...");
    searchButton.disabled = true;
    try {

        const response = await fetch(
            `${API_BASE}/company/${nseCode}/update`,
            {
                method: "POST"
            }
        );

        if (!response.ok) {

            const error = await response.json();

            throw new Error(
                error.detail || "Unable to update company"
            );

        }

        const data = await response.json();

        displayCompany(data);

        loadFeatures(nseCode);

    }

    catch (error) {

        showError(error.message);

    }

    finally {
        setLoading(updateButton, false, "Update");
        searchButton.disabled = false;
    }

}


/* =========================================
   BUTTON LOADING HELPER
========================================= */

function setLoading(button, isLoading, label) {

    button.disabled = isLoading;
    button.textContent = label;

}

/* =========================================
   TABS
========================================= */

const tabButtons = document.querySelectorAll(".tab-button");

tabButtons.forEach(button => {

    button.addEventListener("click", () => {
        switchTab(button.dataset.tab);
    });

});


function switchTab(tabName) {

    document.querySelectorAll(".tab-panel").forEach(panel => {
        panel.classList.add("hidden");
    });

    document.querySelectorAll(".tab-button").forEach(button => {
        button.classList.remove("active");
        button.setAttribute("aria-selected", "false");
    });

    document.getElementById(`${tabName}Tab`).classList.remove("hidden");

    const activeButton = document.getElementById(`${tabName}TabButton`);
    activeButton.classList.add("active");
    activeButton.setAttribute("aria-selected", "true");

}


/* =========================================
   FEATURES

   Fetches computed ratios (profitability, growth,
   leverage, cash flow quality) and renders each
   category as a smooth line chart (Chart.js), with
   click-to-toggle legend chips beneath each chart -
   similar to Screener's own price/volume chart.
========================================= */

const chartInstances = {};

const CHART_PALETTE = [
    "#efbf04", // gold
    "#818cf8", // periwinkle
    "#34d399", // green
    "#f4735a", // coral
    "#38bdf8", // sky
    "#c084fc", // violet
];

async function loadFeatures(nseCode) {

    const featuresTabButton =
        document.getElementById("featuresTabButton");

    try {

        const response = await fetch(
            `${API_BASE}/company/${nseCode}/features`
        );

        if (!response.ok) {
            throw new Error("Unable to load features");
        }

        const data = await response.json();

        if (featuresTabButton) {
            featuresTabButton.classList.remove("hidden");
        }

        renderFeatureChart(
            "profitabilityChart",
            "profitabilityToggles",
            data.profitability,
            { asPercent: true }
        );

        renderFeatureChart(
            "growthChart",
            "growthToggles",
            data.growth,
            { asPercent: true }
        );

        renderFeatureChart(
            "leverageChart",
            "leverageToggles",
            data.leverage,
            { asPercent: false }
        );

        renderFeatureChart(
            "cashflowChart",
            "cashflowToggles",
            data.cash_flow_quality,
            { asPercent: true }
        );

    }

    catch (error) {

        // Features are a bonus tab - don't let a failure
        // here block the rest of the page. Just hide the
        // tab since there's nothing to show.

        if (featuresTabButton) {
            featuresTabButton.classList.add("hidden");
        }

        console.error("loadFeatures failed:", error);

    }

}


/* =========================================
   FEATURE CHART RENDERER

   Pivots flat { period, metric, value } records into
   one Chart.js line dataset per metric, then draws a
   dark-themed line chart with custom toggle chips
   (instead of Chart.js's canvas-drawn legend, so the
   toggles can be styled with real CSS to match the
   rest of the UI).
========================================= */

function renderFeatureChart(
    canvasId,
    togglesId,
    records,
    { asPercent }
) {

    const canvas = document.getElementById(canvasId);
    const togglesContainer = document.getElementById(togglesId);

    togglesContainer.innerHTML = "";

    // --------------------------------------------------
    // Destroy any previous chart on this canvas before
    // redrawing (Chart.js throws if you don't).
    // --------------------------------------------------

    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
        delete chartInstances[canvasId];
    }

    if (!records || records.length === 0) {
        return;
    }

    // --------------------------------------------------
    // Pivot: unique periods (x-axis) and unique metrics
    // (one line series each), preserving first-seen order.
    // --------------------------------------------------

    const periods = [];
    const periodSeen = new Set();

    const metrics = [];
    const metricSeen = new Set();

    const valuesByMetric = {};

    records.forEach(record => {

        const { period, metric, value } = record;

        if (!periodSeen.has(period)) {
            periodSeen.add(period);
            periods.push(period);
        }

        if (!metricSeen.has(metric)) {
            metricSeen.add(metric);
            metrics.push(metric);
        }

        if (!valuesByMetric[metric]) {
            valuesByMetric[metric] = {};
        }

        valuesByMetric[metric][period] = value;

    });

    // --------------------------------------------------
    // Build one dataset per metric
    // --------------------------------------------------

    const datasets = metrics.map((metric, index) => {

        const color = CHART_PALETTE[index % CHART_PALETTE.length];

        return {
            label: metric,
            data: periods.map(
                period => valuesByMetric[metric][period] ?? null
            ),
            borderColor: color,
            backgroundColor: color,
            pointRadius: 0,
            pointHoverRadius: 4,
            borderWidth: 2,
            tension: 0.35,
            spanGaps: true,
        };

    });

    // --------------------------------------------------
    // Draw chart
    // --------------------------------------------------

    const formatValue = asPercent
        ? formatRatioAsPercent
        : formatRatio;

    chartInstances[canvasId] = new Chart(canvas, {

        type: "line",

        data: {
            labels: periods,
            datasets: datasets,
        },

        options: {

            responsive: true,
            maintainAspectRatio: false,

            interaction: {
                mode: "index",
                intersect: false,
            },

            plugins: {

                legend: {
                    display: false,
                },

                tooltip: {
                    backgroundColor: "#1c1c1f",
                    borderColor: "#2a2a2e",
                    borderWidth: 1,
                    titleColor: "#8b8b91",
                    bodyColor: "#f2f1ec",
                    padding: 10,
                    callbacks: {
                        label: context =>
                            ` ${context.dataset.label}: ${formatValue(context.parsed.y)}`
                    }
                },

            },

            scales: {

                x: {
                    grid: {
                        color: "#232326",
                        drawTicks: false,
                    },
                    ticks: {
                        color: "#58585e",
                        font: { family: "JetBrains Mono", size: 11 },
                    },
                },

                y: {
                    grid: {
                        color: "#232326",
                        drawTicks: false,
                    },
                    ticks: {
                        color: "#58585e",
                        font: { family: "JetBrains Mono", size: 11 },
                        callback: value => formatValue(value),
                    },
                },

            },

        },

    });

    // --------------------------------------------------
    // Toggle chips (one per metric), click to show/hide
    // that line - mirrors the "Price on NSE / 50 DMA /
    // 200 DMA / Volume" checkboxes on Screener's chart.
    // --------------------------------------------------

    metrics.forEach((metric, index) => {

        const color = CHART_PALETTE[index % CHART_PALETTE.length];

        const chip = document.createElement("label");
        chip.className = "chart-toggle";

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.checked = true;
        checkbox.style.setProperty("--toggle-color", color);

        checkbox.addEventListener("change", () => {

            const chart = chartInstances[canvasId];

            if (!chart) {
                return;
            }

            chart.setDatasetVisibility(
                index,
                checkbox.checked
            );

            chart.update();

        });

        const text = document.createElement("span");
        text.textContent = metric;

        chip.appendChild(checkbox);
        chip.appendChild(text);

        togglesContainer.appendChild(chip);

    });

}


/* =========================================
   DISPLAY COMPANY
========================================= */

function displayCompany(data) {

    companySection.classList.remove("hidden");

    switchTab("overview");


    const company = data.company;

    document.getElementById("companyName").textContent =
        company.company_name;

    document.getElementById("nseCode").textContent =
        company.nse_code;


    displaySummary(data);

    displayProfitLoss(data.profit_loss);

    displayBalanceSheet(data.balance_sheet);

    displayCashFlow(data.cash_flow);

    displayInsights(data.quarterly_insights);

}


/* =========================================
   SUMMARY
========================================= */

function displaySummary(data) {

    const profitLoss = data.profit_loss;

    if (!profitLoss || profitLoss.length === 0) {
        return;
    }

    // --------------------------------------------------
    // profit_loss arrives as flat records:
    //   [{ period, metric, value }, ...]
    // Find the latest period, then look up each metric
    // by name for that period.
    // --------------------------------------------------

    const latestPeriod =
        profitLoss[profitLoss.length - 1].period;

    const latestRecords = profitLoss.filter(
        record => record.period === latestPeriod
    );

    function getMetric(names) {

        const record = latestRecords.find(
            r => names.includes(r.metric)
        );

        return record ? record.value : null;

    }

    document.getElementById("sales").textContent =
        formatNumber(getMetric(["Sales", "Revenue"]));

    document.getElementById("netProfit").textContent =
        formatNumber(getMetric(["Net Profit", "Net profit"]));

    document.getElementById("eps").textContent =
        formatNumber(getMetric(["EPS in Rs", "EPS"]));

    document.getElementById("opm").textContent =
        formatPercent(getMetric(["OPM %"]));

}


/* =========================================
   PIVOT TABLE HELPER

   Used by Profit & Loss, Balance Sheet, and Cash Flow.
   Each of these arrives as one record per period, e.g.:

       [{ period: "Mar 2026", sales: 100, ... }, ...]

   This renders them the same way as Quarterly
   Insights: line items as rows, periods as columns.

              Mar 2026   Jun 2026
       Sales     100        140
       ...
========================================= */

function renderPivotTable(
    theadId,
    tbodyId,
    records,
    formatter = formatNumber
) {

    const thead = document.getElementById(theadId);
    const tbody = document.getElementById(tbodyId);

    thead.innerHTML = "";
    tbody.innerHTML = "";

    if (!records || records.length === 0) {
        return;
    }


    // ==================================================
    // COLLECT UNIQUE PERIODS AND METRICS
    // ==================================================

    const periods = [];
    const periodSeen = new Set();

    const metrics = [];
    const metricSeen = new Set();

    const valuesByMetric = {};


    records.forEach(record => {

        const period = record.period;
        const metric = record.metric;
        const value = record.value;


        // ----------------------------------------------
        // Period
        // ----------------------------------------------

        if (
            period !== null &&
            period !== undefined &&
            !periodSeen.has(period)
        ) {

            periodSeen.add(period);
            periods.push(period);

        }


        // ----------------------------------------------
        // Metric
        // ----------------------------------------------

        if (
            metric !== null &&
            metric !== undefined &&
            !metricSeen.has(metric)
        ) {

            metricSeen.add(metric);
            metrics.push(metric);

        }


        // ----------------------------------------------
        // Store value
        // ----------------------------------------------

        if (!valuesByMetric[metric]) {
            valuesByMetric[metric] = {};
        }

        valuesByMetric[metric][period] = value;

    });


    // ==================================================
    // HEADER
    // ==================================================

    const headerRow = document.createElement("tr");


    const metricHeader = document.createElement("th");

    metricHeader.textContent = "Metric";

    headerRow.appendChild(metricHeader);


    periods.forEach(period => {

        const th = document.createElement("th");

        th.textContent = period;

        headerRow.appendChild(th);

    });


    thead.appendChild(headerRow);


    // ==================================================
    // BODY
    // ==================================================

    metrics.forEach(metric => {

        const row = document.createElement("tr");


        // ----------------------------------------------
        // Metric name
        // ----------------------------------------------

        const metricCell = document.createElement("td");

        metricCell.textContent = metric;

        row.appendChild(metricCell);


        // ----------------------------------------------
        // Values
        // ----------------------------------------------

        periods.forEach(period => {

            const cell = document.createElement("td");

            const value =
                valuesByMetric[metric]?.[period];


            cell.textContent =
                formatter(value);


            row.appendChild(cell);

        });


        tbody.appendChild(row);

    });

}


/* =========================================
   PROFIT & LOSS
========================================= */


function displayProfitLoss(records) {

    renderPivotTable(
        "profitLossHead",
        "profitLossTable",
        records,
    );

}


/* =========================================
   BALANCE SHEET
========================================= */


function displayBalanceSheet(records) {

    renderPivotTable(
        "balanceSheetHead",
        "balanceSheetTable",
        records,
    );

}


/* =========================================
   CASH FLOW
========================================= */


function displayCashFlow(records) {

    renderPivotTable(
        "cashFlowHead",
        "cashFlowTable",
        records,
    );

}


/* =========================================
   QUARTERLY INSIGHTS

   Records arrive as a flat list:
       [{ metric, period, value }, ...]

   They are pivoted here into a metric x period grid,
   matching how Screener itself displays this table:

              Mar 2026   Jun 2026
       ABC       324        410
       XYZ       782        690
========================================= */

function displayInsights(records) {

    const thead =
        document.getElementById("insightsHead");

    const tbody =
        document.getElementById("insightsTable");

    thead.innerHTML = "";
    tbody.innerHTML = "";

    if (!records || records.length === 0) {
        return;
    }

    // --------------------------------------------------
    // Collect unique periods (columns) and metrics (rows),
    // preserving the order they first appear in.
    // --------------------------------------------------

    const periods = [];
    const periodSeen = new Set();

    const metrics = [];
    const metricSeen = new Set();

    const valuesByMetric = {};

    records.forEach(record => {

        const metric = record.metric;
        const period = record.period;

        if (!periodSeen.has(period)) {
            periodSeen.add(period);
            periods.push(period);
        }

        if (!metricSeen.has(metric)) {
            metricSeen.add(metric);
            metrics.push(metric);
        }

        if (!valuesByMetric[metric]) {
            valuesByMetric[metric] = {};
        }

        valuesByMetric[metric][period] = record.value;

    });

    // --------------------------------------------------
    // Header row: one blank corner cell + one per period
    // --------------------------------------------------

    const headerRow = document.createElement("tr");

    const cornerCell = document.createElement("th");
    cornerCell.textContent = "Metric";
    headerRow.appendChild(cornerCell);

    periods.forEach(period => {

        const th = document.createElement("th");
        th.textContent = period;
        headerRow.appendChild(th);

    });

    thead.appendChild(headerRow);

    // --------------------------------------------------
    // One row per metric, one value per period column
    // --------------------------------------------------

    metrics.forEach(metric => {

        const row = document.createElement("tr");

        const metricCell = document.createElement("td");
        metricCell.textContent = metric;
        row.appendChild(metricCell);

        periods.forEach(period => {

            const cell = document.createElement("td");

            const value = valuesByMetric[metric][period];

            cell.textContent = formatNumber(value);

            row.appendChild(cell);

        });

        tbody.appendChild(row);

    });

}

/* =========================================
   FORMATTING
========================================= */

function formatNumber(value) {

    if (value === null || value === undefined) {
        return "-";
    }

    return Number(value).toLocaleString(
        "en-IN",
        {
            maximumFractionDigits: 2
        }
    );

}


function formatPercent(value) {

    if (value === null || value === undefined) {
        return "-";
    }

    return `${Number(value).toFixed(2)}%`;

}


function formatRatio(value) {

    if (value === null || value === undefined) {
        return "-";
    }

    return Number(value).toFixed(2);

}


function formatRatioAsPercent(value) {
    // Features come back as decimals (e.g. 0.18 for +18%),
    // unlike the raw Screener fields which are already
    // percentages (e.g. 18.0). This converts before formatting.

    if (value === null || value === undefined) {
        return "-";
    }

    return `${(Number(value) * 100).toFixed(2)}%`;

}


/* =========================================
   ERRORS
========================================= */

function showError(message) {

    errorMessage.textContent = message;

}


function clearError() {

    errorMessage.textContent = "";

}