/* =========================================
   SHARED FORMATTERS + CHART HELPERS

   Loaded on every page (via base.html), before base.js
   and any page-specific script. Anything reused across
   Overview / Fundamentals / Financials lives here so it's
   written once, not duplicated per page.
========================================= */

const chartInstances = {};

const CHART_PALETTE = [
    "#FF5722", // primary
    "#818cf8",
    "#34d399",
    "#f4735a",
    "#38bdf8",
    "#c084fc",
];


function formatNumber(value) {

    if (value === null || value === undefined) {
        return "-";
    }

    return Number(value).toLocaleString(
        "en-IN",
        { maximumFractionDigits: 2 }
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

    if (value === null || value === undefined) {
        return "-";
    }

    return `${(Number(value) * 100).toFixed(2)}%`;

}


function formatMultiple(value) {

    if (value === null || value === undefined) {
        return "-";
    }

    return `${Number(value).toFixed(2)}x`;

}


function formatPrice(value) {

    if (value === null || value === undefined) {
        return "-";
    }

    return `₹${Number(value).toLocaleString("en-IN", { maximumFractionDigits: 2 })}`;

}


function formatChartDate(epochSeconds) {

    const date = new Date(epochSeconds * 1000);

    return date.toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
    });

}


function formatChartDateFull(epochSeconds) {

    const date = new Date(epochSeconds * 1000);

    return date.toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
    });

}


function formatChartTime(epochSeconds) {

    const date = new Date(epochSeconds * 1000);

    return date.toLocaleTimeString("en-IN", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
    });

}


function formatChartDateTime(epochSeconds) {

    const date = new Date(epochSeconds * 1000);

    return date.toLocaleString("en-IN", {
        day: "2-digit",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
    });

}


/* =========================================
   PIVOT TABLE HELPER

   Renders flat { period, metric, value } records into a
   metric-rows x period-columns table, into a plain <table>
   with the given thead/tbody element IDs. Used for the
   statement tables on Overview and Financials.
========================================= */

function renderPivotTable(
    theadId,
    tbodyId,
    records,
    formatter = formatNumber
) {

    const thead = document.getElementById(theadId);
    const tbody = document.getElementById(tbodyId);

    if (!thead || !tbody) {
        return;
    }

    thead.innerHTML = "";
    tbody.innerHTML = "";

    if (!records || records.length === 0) {
        return;
    }

    const periods = [];
    const periodSeen = new Set();

    const metrics = [];
    const metricSeen = new Set();

    const valuesByMetric = {};

    records.forEach(record => {

        const { period, metric, value } = record;

        if (period !== null && period !== undefined && !periodSeen.has(period)) {
            periodSeen.add(period);
            periods.push(period);
        }

        if (metric !== null && metric !== undefined && !metricSeen.has(metric)) {
            metricSeen.add(metric);
            metrics.push(metric);
        }

        if (!valuesByMetric[metric]) {
            valuesByMetric[metric] = {};
        }

        valuesByMetric[metric][period] = value;

    });

    const headerRow = document.createElement("tr");

    const metricHeader = document.createElement("th");
    metricHeader.className = "text-left px-4 py-3 text-text-medium font-mono text-xs uppercase tracking-wider";
    metricHeader.textContent = "Metric";
    headerRow.appendChild(metricHeader);

    periods.forEach(period => {

        const th = document.createElement("th");
        th.className = "text-right px-4 py-3 text-text-medium font-mono text-xs uppercase tracking-wider whitespace-nowrap";
        th.textContent = period;
        headerRow.appendChild(th);

    });

    thead.appendChild(headerRow);

    metrics.forEach(metric => {

        const row = document.createElement("tr");
        row.className = "border-t border-border hover:bg-surface-raised";

        const metricCell = document.createElement("td");
        metricCell.className = "px-4 py-3 text-text-medium whitespace-nowrap";
        metricCell.textContent = metric;
        row.appendChild(metricCell);

        periods.forEach(period => {

            const cell = document.createElement("td");
            cell.className = "px-4 py-3 text-right font-mono text-text-high whitespace-nowrap";

            const value = valuesByMetric[metric]?.[period];
            cell.textContent = formatter(value);

            row.appendChild(cell);

        });

        tbody.appendChild(row);

    });
}



function formatSyncTimestamp(date = new Date()) {

    const time = date.toLocaleTimeString("en-IN", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false,
        timeZone: "Asia/Kolkata",
    });

    return `Last synced ${time} IST`;

}