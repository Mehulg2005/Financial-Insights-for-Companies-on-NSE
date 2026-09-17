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

        currentPriceNseCode = nseCode;
        currentPriceMode = "live";
        updatePriceModeUI("live");
        loadPriceChart(nseCode, "live");
        startLivePriceRefresh(nseCode);

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
        currentPriceNseCode = nseCode;
        currentPriceMode = "live";
        updatePriceModeUI("live");
        loadPriceChart(nseCode, "live");
        startLivePriceRefresh(nseCode);

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

    // ----------------------------------------------------
    // Chart.js draws charts at their canvas's size at the
    // moment they're created. Charts built while this tab
    // was hidden (display:none) get created at 0 width and
    // stay blank forever unless explicitly resized once the
    // tab becomes visible.
    // ----------------------------------------------------

    if (tabName === "features") {

        Object.values(chartInstances).forEach(chart => {
            chart.resize();
        });

    }

}


/* =========================================
   FEATURES

   Fetches computed metrics (profitability, cash flow
   quality, growth trends) and renders each category as
   a set of smooth line charts (Chart.js), split into
   multiple graphs per category so metrics with very
   different scales don't flatten each other out. Each
   graph has click-to-toggle legend chips beneath it -
   similar to Screener's own price/volume chart.

   Other Metrics (Total Liabilities vs Total Assets,
   Borrowings vs Total Assets) are rendered separately
   as scatter charts, one point per period.
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

// --------------------------------------------------
// Per-metric formatter, used for tooltips and for a
// chart's y-axis ticks when metrics share one axis.
// --------------------------------------------------

const FEATURE_METRIC_CONFIG = {
    "Effective Tax Rate": { formatter: formatRatioAsPercent },
    "Operating Margin": { formatter: formatRatioAsPercent },
    "Sales": { formatter: formatNumber },
    "Net Profit": { formatter: formatNumber },
    "Profit before Tax": { formatter: formatNumber },
    "Profit After Tax": { formatter: formatNumber },

    "Cash from Operating Activity (CFO)": { formatter: formatNumber },
    "CFO Contribution": { formatter: formatRatioAsPercent },
    "Cash Conversion (CFO / Net Profit)": { formatter: formatRatioAsPercent },

    "Reserves": { formatter: formatNumber },
    "Equity Capital": { formatter: formatNumber },
    "Investment Migration": { formatter: formatRatioAsPercent },
    "Borrowings to Net Worth Ratio": { formatter: formatRatio },
    "Interest Coverage Ratio": { formatter: formatMultiple },

    "EPS": { formatter: formatNumber },
};


function getMetricConfig(metric) {

    return FEATURE_METRIC_CONFIG[metric] || {
        formatter: formatNumber
    };

}


// --------------------------------------------------
// Which graphs each category is split into, and which
// metrics (in display order) belong on each graph.
// dualAxis:true puts the first present metric on the
// left axis and the second on the right axis, so metrics
// of very different magnitude ("scaled down" pairs) each
// get their own visual range instead of flattening the
// smaller one.
// --------------------------------------------------

const FEATURE_CHART_GROUPS = {

    profitability: [
        {
            canvas: "profitabilityChart1",
            toggles: "profitabilityToggles1",
            metrics: ["Effective Tax Rate", "Operating Margin"],
            dualAxis: false
        },
        {
            canvas: "profitabilityChart2",
            toggles: "profitabilityToggles2",
            metrics: ["Sales", "Net Profit"],
            dualAxis: false
        },
        {
            canvas: "profitabilityChart3",
            toggles: "profitabilityToggles3",
            metrics: ["Profit before Tax", "Profit After Tax"],
            dualAxis: false
        },
        {
            canvas: "profitabilityChart4",
            toggles: "profitabilityToggles4",
            metrics: ["EPS"],
            dualAxis: false
        },
    ],

    cash_flow_quality: [
        {
            canvas: "cashflowChart1",
            toggles: "cashflowToggles1",
            metrics: ["Cash Conversion (CFO / Net Profit)", "CFO Contribution"],
            dualAxis: false
        },
        {
            canvas: "cashflowChart2",
            toggles: "cashflowToggles2",
            metrics: ["Cash from Operating Activity (CFO)"],
            dualAxis: false
        },
    ],

    growth_trends: [
        {
            canvas: "growthTrendsChart1",
            toggles: "growthTrendsToggles1",
            metrics: ["Investment Migration", "Borrowings to Net Worth Ratio"],
            dualAxis: false
        },
        {
            canvas: "growthTrendsChart2",
            toggles: "growthTrendsToggles2",
            metrics: ["Reserves", "Equity Capital"],
            dualAxis: false
        },
        {
            canvas: "growthTrendsChart3",
            toggles: "growthTrendsToggles3",
            metrics: ["Interest Coverage Ratio"],
            dualAxis: false
        },
    ],

};


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

        FEATURE_CHART_GROUPS.profitability.forEach(group => {
            renderMetricLineChart(group, data.profitability);
        });

        FEATURE_CHART_GROUPS.cash_flow_quality.forEach(group => {
            renderMetricLineChart(group, data.cash_flow_quality);
        });

        FEATURE_CHART_GROUPS.growth_trends.forEach(group => {
            renderMetricLineChart(group, data.growth_trends);
        });

                renderOtherMetricsCharts(data.other_metrics);

        loadFundamentalAnalysis(nseCode);

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
   FUNDAMENTAL ANALYSIS

   Fetches the trend-based fundamental verdict (Phase 1
   of the "Is this company good to trade?" pipeline) and
   renders an overall badge plus one explainable card per
   category (Profitability, Growth, Cash Flow, Leverage,
   Capital Allocation).
========================================= */

async function loadFundamentalAnalysis(nseCode) {

    const overallContainer =
        document.getElementById("fundamentalOverallVerdict");

    const cardsContainer =
        document.getElementById("fundamentalAnalysisCards");

    if (!overallContainer || !cardsContainer) {
        return;
    }

    overallContainer.innerHTML = "";
    cardsContainer.innerHTML = "";

    try {

        const response = await fetch(
            `${API_BASE}/company/${nseCode}/fundamental-analysis`
        );

        if (!response.ok) {
            throw new Error("Unable to load fundamental analysis");
        }

        const data = await response.json();

        renderOverallVerdict(overallContainer, data.overall_verdict);

        data.categories.forEach(category => {
            cardsContainer.appendChild(buildAnalysisCard(category));
        });

    }

    catch (error) {

        console.error("loadFundamentalAnalysis failed:", error);

    }

}


function renderOverallVerdict(container, verdict) {

    const badge = document.createElement("div");

    badge.className = `verdict-badge overall verdict-${verdict.toLowerCase()}`;
    badge.textContent = `Fundamental Aspect: ${verdict}`;

    container.appendChild(badge);

}


function buildAnalysisCard(category) {

    const card = document.createElement("div");
    card.className = "analysis-card";

    const header = document.createElement("div");
    header.className = "analysis-card-header";

    const title = document.createElement("h3");
    title.textContent = category.category;

    const badge = document.createElement("span");
    badge.className = `verdict-badge verdict-${category.verdict.toLowerCase()}`;
    badge.textContent = category.verdict;

    header.appendChild(title);
    header.appendChild(badge);

    const bulletList = document.createElement("ul");
    bulletList.className = "analysis-bullets";

    category.bullets.forEach(bulletText => {

        const item = document.createElement("li");
        item.textContent = bulletText;
        bulletList.appendChild(item);

    });

    card.appendChild(header);
    card.appendChild(bulletList);

    return card;

}


/* =========================================
   FEATURE LINE CHART RENDERER

   Filters flat { period, metric, value } records down
   to just the metrics in this graph, pivots them into
   one Chart.js line dataset per metric, then draws a
   dark-themed line chart. When dualAxis is true, the
   first present metric goes on the left y-axis and the
   second on the right, so two differently-scaled series
   can share one chart without one flattening the other.
========================================= */

function renderMetricLineChart(group, records) {

    const canvas = document.getElementById(group.canvas);
    const togglesContainer = document.getElementById(group.toggles);

    if (!canvas || !togglesContainer) {
        return;
    }

    togglesContainer.innerHTML = "";

    if (chartInstances[group.canvas]) {
        chartInstances[group.canvas].destroy();
        delete chartInstances[group.canvas];
    }

    const filtered = (records || []).filter(
        record => group.metrics.includes(record.metric)
    );

    if (filtered.length === 0) {
        return;
    }

    // --------------------------------------------------
    // Pivot: unique periods (x-axis), values per metric.
    // Metric order follows group.metrics (not first-seen
    // order in the data), so the spec'd ordering holds.
    // --------------------------------------------------

    const periods = [];
    const periodSeen = new Set();

    const valuesByMetric = {};

    filtered.forEach(record => {

        const { period, metric, value } = record;

        if (!periodSeen.has(period)) {
            periodSeen.add(period);
            periods.push(period);
        }

        if (!valuesByMetric[metric]) {
            valuesByMetric[metric] = {};
        }

        valuesByMetric[metric][period] = value;

    });

    const presentMetrics = group.metrics.filter(
        metric => valuesByMetric[metric]
    );

    if (presentMetrics.length === 0) {
        return;
    }

    // --------------------------------------------------
    // Build one dataset per metric
    // --------------------------------------------------

    const usesRightAxis = group.dualAxis && presentMetrics.length > 1;

    const datasets = presentMetrics.map((metric, index) => {

        const color = CHART_PALETTE[index % CHART_PALETTE.length];

        const axisId = group.dualAxis
            ? (index === 0 ? "yLeft" : "yRight")
            : "yShared";

        return {
            label: metric,
            data: periods.map(
                period => valuesByMetric[metric][period] ?? null
            ),
            borderColor: color,
            backgroundColor: color,
            pointRadius: 2,
            pointHoverRadius: 4,
            borderWidth: 2,
            tension: 0.35,
            spanGaps: true,
            yAxisID: axisId,
        };

    });

    // --------------------------------------------------
    // Axis config
    // --------------------------------------------------

    const tickFontConfig = {
        color: "#58585e",
        font: { family: "JetBrains Mono", size: 11 },
    };

    const scales = {
        x: {
            grid: { color: "#232326", drawTicks: false },
            ticks: tickFontConfig,
        },
    };

    if (group.dualAxis) {

        const leftFormatter = getMetricConfig(presentMetrics[0]).formatter;
        const rightFormatter = presentMetrics[1]
            ? getMetricConfig(presentMetrics[1]).formatter
            : leftFormatter;

        scales.yLeft = {
            position: "left",
            display: true,
            grid: { color: "#232326", drawTicks: false },
            ticks: {
                ...tickFontConfig,
                callback: value => leftFormatter(value),
            },
        };

        scales.yRight = {
            position: "right",
            display: usesRightAxis,
            grid: { drawOnChartArea: false },
            ticks: {
                ...tickFontConfig,
                callback: value => rightFormatter(value),
            },
        };

    } else {

        const sharedFormatter = getMetricConfig(presentMetrics[0]).formatter;

        scales.yShared = {
            position: "left",
            grid: { color: "#232326", drawTicks: false },
            ticks: {
                ...tickFontConfig,
                callback: value => sharedFormatter(value),
            },
        };

    }

    // --------------------------------------------------
    // Draw chart
    // --------------------------------------------------

    chartInstances[group.canvas] = new Chart(canvas, {

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
                        label: context => {
                            const metric = context.dataset.label;
                            const formatter = getMetricConfig(metric).formatter;
                            return ` ${metric}: ${formatter(context.parsed.y)}`;
                        }
                    }
                },

            },

            scales: scales,

        },

    });

    // --------------------------------------------------
    // Toggle chips (one per metric), click to show/hide
    // that line - mirrors the "Price on NSE / 50 DMA /
    // 200 DMA / Volume" checkboxes on Screener's chart.
    // --------------------------------------------------

    presentMetrics.forEach((metric, index) => {

        const color = CHART_PALETTE[index % CHART_PALETTE.length];

        const chip = document.createElement("label");
        chip.className = "chart-toggle";

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.checked = true;
        checkbox.style.setProperty("--toggle-color", color);

        checkbox.addEventListener("change", () => {

            const chart = chartInstances[group.canvas];

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
   OTHER METRICS CHARTS

   Two scatter charts, each plotting one point per
   period: (Total Assets, Total Liabilities) and
   (Total Assets, Borrowings).
========================================= */
// --------------------------------------------------
// Converts a hex color like "#efbf04" into an rgba()
// string at a given opacity, used to fade older points.
// --------------------------------------------------

function hexToRgba(hex, alpha) {

    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);

    return `rgba(${r}, ${g}, ${b}, ${alpha})`;

}


// --------------------------------------------------
// Draws an arrowhead at the newest point (showing the
// direction of travel across periods) and labels the
// oldest and newest points with their period, so the
// trend direction is readable without hovering.
// --------------------------------------------------

const TREND_DIRECTION_PLUGIN = {

    id: "trendDirection",

    afterDatasetsDraw(chart) {

        const { ctx } = chart;
        const meta = chart.getDatasetMeta(0);
        const points = meta.data;

        if (!points || points.length < 2) {
            return;
        }

        const first = points[0];
        const last = points[points.length - 1];
        const secondLast = points[points.length - 2];

        // ----------------------------------------------
        // Arrowhead pointing from the second-last point
        // toward the newest (last) point.
        // ----------------------------------------------

        const angle = Math.atan2(
            last.y - secondLast.y,
            last.x - secondLast.x
        );

        const arrowLength = 9;

        ctx.save();

        ctx.fillStyle = "#efbf04";

        ctx.beginPath();
        ctx.moveTo(last.x, last.y);
        ctx.lineTo(
            last.x - arrowLength * Math.cos(angle - Math.PI / 6),
            last.y - arrowLength * Math.sin(angle - Math.PI / 6)
        );
        ctx.lineTo(
            last.x - arrowLength * Math.cos(angle + Math.PI / 6),
            last.y - arrowLength * Math.sin(angle + Math.PI / 6)
        );
        ctx.closePath();
        ctx.fill();

        ctx.restore();

        // ----------------------------------------------
        // Period labels at the start and end of the path
        // ----------------------------------------------

        const rawData = chart.data.datasets[0].data;
        const firstPeriod = rawData[0]?.period;
        const lastPeriod = rawData[rawData.length - 1]?.period;

        ctx.save();
        ctx.font = "11px 'JetBrains Mono', monospace";
        ctx.textAlign = "center";

        if (firstPeriod) {
            ctx.fillStyle = "#8b8b91";
            ctx.fillText(firstPeriod, first.x, first.y - 14);
        }

        if (lastPeriod) {
            ctx.fillStyle = "#efbf04";
            ctx.font = "bold 11px 'JetBrains Mono', monospace";
            ctx.fillText(lastPeriod, last.x, last.y - 14);
        }

        ctx.restore();

    }

};

function renderOtherMetricsCharts(otherMetrics) {

    if (!otherMetrics) {
        return;
    }

    renderScatterChart(
        "totalLiabilitiesVsAssetsChart",
        otherMetrics.total_liabilities_vs_total_assets,
        "Total Liabilities",
        "Total Assets"
    );

    renderScatterChart(
        "borrowingsVsAssetsChart",
        otherMetrics.borrowings_vs_total_assets,
        "Borrowings",
        "Total Assets"
    );

}


function renderScatterChart(
    canvasId,
    points,
    yLabel,
    xLabel
) {

    const canvas = document.getElementById(canvasId);

    if (!canvas) {
        return;
    }

    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
        delete chartInstances[canvasId];
    }

    if (!points || points.length === 0) {
        return;
    }

    const chartData = points.map(point => ({
        x: point.x,
        y: point.y,
        period: point.period
    }));

    // --------------------------------------------------
    // Oldest points render small and faint, newest points
    // render bigger and solid gold, so the direction of
    // travel is visible at a glance along the path itself.
    // --------------------------------------------------

    const pointBackgroundColors = chartData.map((_, index) => {

        const progress = chartData.length > 1
            ? index / (chartData.length - 1)
            : 1;

        const alpha = 0.3 + progress * 0.7;

        return hexToRgba("#efbf04", alpha);

    });

    const pointRadii = chartData.map((_, index) => {

        const progress = chartData.length > 1
            ? index / (chartData.length - 1)
            : 1;

        return 3 + progress * 4;

    });

    chartInstances[canvasId] = new Chart(canvas, {

        type: "scatter",

        data: {
            datasets: [
                {
                    label: `${yLabel} vs ${xLabel}`,
                    data: chartData,
                    showLine: true,
                    borderColor: "#efbf04",
                    backgroundColor: "#efbf04",
                    pointBackgroundColor: pointBackgroundColors,
                    pointBorderColor: "transparent",
                    pointRadius: pointRadii,
                    pointHoverRadius: pointRadii.map(radius => radius + 2),
                    borderWidth: 2,
                    tension: 0.15,
                }
            ]
        },

        options: {

            responsive: true,
            maintainAspectRatio: false,

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
                        label: context => {
                            const point = context.raw;
                            return ` ${point.period}: ${xLabel} ${formatNumber(point.x)}, ${yLabel} ${formatNumber(point.y)}`;
                        }
                    }
                },

            },

            scales: {

                x: {
                    title: {
                        display: true,
                        text: xLabel,
                        color: "#8b8b91",
                    },
                    grid: {
                        color: "#232326",
                        drawTicks: false,
                    },
                    ticks: {
                        color: "#58585e",
                        font: { family: "JetBrains Mono", size: 11 },
                        callback: value => formatNumber(value),
                    },
                },

                y: {
                    title: {
                        display: true,
                        text: yLabel,
                        color: "#8b8b91",
                    },
                    grid: {
                        color: "#232326",
                        drawTicks: false,
                    },
                    ticks: {
                        color: "#58585e",
                        font: { family: "JetBrains Mono", size: 11 },
                        callback: value => formatNumber(value),
                    },
                },

            },

        },

        plugins: [TREND_DIRECTION_PLUGIN],

    });

}

/* =========================================
   PRICE TRACKER

   Fetches price data from Groww and renders it as a line
   chart. Always visible above the tab bar, independent of
   which tab (Overview / Fundamentals) is active.

   Two modes:
     - "live"  : per-minute candles for today, polled every
                 10 seconds. Default mode on every new search.
     - "range" : daily closes over the last 3 months.
========================================= */

let currentPriceNseCode = null;
let currentPriceMode = "live";
let priceRefreshIntervalId = null;


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


function stopLivePriceRefresh() {

    if (priceRefreshIntervalId) {
        clearInterval(priceRefreshIntervalId);
        priceRefreshIntervalId = null;
    }

}


function startLivePriceRefresh(nseCode) {

    stopLivePriceRefresh();

    priceRefreshIntervalId = setInterval(() => {
        loadPriceChart(nseCode, "live");
    }, 60000);

}


function updatePriceModeUI(mode) {

    const liveButton = document.getElementById("priceModeLiveButton");
    const rangeButton = document.getElementById("priceModeRangeButton");
    const labelEl = document.getElementById("priceTrackerLabel");

    if (liveButton) {
        liveButton.classList.toggle("active", mode === "live");
    }

    if (rangeButton) {
        rangeButton.classList.toggle("active", mode === "range");
    }

    if (labelEl) {
        labelEl.textContent = mode === "live"
            ? "Live price · today"
            : "Delayed price · last 3 months";
    }

}


function setPriceMode(mode) {

    currentPriceMode = mode;

    updatePriceModeUI(mode);

    if (!currentPriceNseCode) {
        return;
    }

    if (mode === "live") {

        loadPriceChart(currentPriceNseCode, "live");
        startLivePriceRefresh(currentPriceNseCode);

    }

    else {

        stopLivePriceRefresh();
        loadPriceChart(currentPriceNseCode, "range");

    }

}


const priceModeLiveButton = document.getElementById("priceModeLiveButton");
const priceModeRangeButton = document.getElementById("priceModeRangeButton");

if (priceModeLiveButton) {
    priceModeLiveButton.addEventListener("click", () => setPriceMode("live"));
}

if (priceModeRangeButton) {
    priceModeRangeButton.addEventListener("click", () => setPriceMode("range"));
}


async function loadPriceChart(nseCode, mode) {

    const currentValueEl = document.getElementById("priceCurrentValue");
    const changeValueEl = document.getElementById("priceChangeValue");
    const canvas = document.getElementById("priceChart");

    if (!canvas) {
        return;
    }

    try {

        const response = await fetch(
            `${API_BASE}/company/${nseCode}/price-chart?mode=${mode}`
        );

        if (!response.ok) {
            throw new Error("Unable to load price data");
        }

        const data = await response.json();
        const candles = data.candles || [];

        if (candles.length === 0) {
            throw new Error("No price data returned");
        }

        // ----------------------------------------------
        // Current price + change badge
        // ----------------------------------------------

        const latestPrice = candles[candles.length - 1].price;

        if (currentValueEl) {
            currentValueEl.textContent = formatPrice(latestPrice);
        }

        if (changeValueEl) {

            changeValueEl.classList.remove("price-up", "price-down");

            const changeValue = data.change_value;
            const changePercent = data.change_percent;

            if (changeValue !== null && changeValue !== undefined) {

                const isUp = changeValue >= 0;

                changeValueEl.classList.add(isUp ? "price-up" : "price-down");

                changeValueEl.textContent =
                    `${isUp ? "+" : ""}${formatPrice(changeValue)} ` +
                    `(${isUp ? "+" : ""}${Number(changePercent).toFixed(2)}%)`;

            } else {

                changeValueEl.textContent = "";

            }

        }

        // ----------------------------------------------
        // Chart - labels/tooltip formatting differ by mode
        // (time-of-day for live, date for range)
        // ----------------------------------------------

        const labelFormatter = mode === "live" ? formatChartTime : formatChartDate;
        const titleFormatter = mode === "live" ? formatChartDateTime : formatChartDateFull;

        const labels = candles.map(candle => labelFormatter(candle.timestamp));
        const prices = candles.map(candle => candle.price);
        const fullLabels = candles.map(candle => titleFormatter(candle.timestamp));

        // Only replace the chart once new data has successfully
        // arrived and parsed - keeps the last good chart visible
        // through a transient failure instead of flickering,
        // which matters a lot at a 10-second live refresh rate.

        if (chartInstances["priceChart"]) {
            chartInstances["priceChart"].destroy();
            delete chartInstances["priceChart"];
        }

        chartInstances["priceChart"] = new Chart(canvas, {

            type: "line",

            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Price",
                        data: prices,
                        borderColor: "#efbf04",
                        backgroundColor: "rgba(239, 191, 4, 0.1)",
                        pointRadius: 0,
                        pointHoverRadius: 4,
                        borderWidth: 2,
                        tension: 0.25,
                        fill: true,
                    }
                ]
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
                            title: context => fullLabels[context[0].dataIndex],
                            label: context => ` ${formatPrice(context.parsed.y)}`
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
                            font: { family: "JetBrains Mono", size: 10 },
                            autoSkip: true,
                            maxTicksLimit: 10,
                            maxRotation: 0,
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
                            callback: value => formatPrice(value),
                        },
                    },

                },

            },

        });

    }

    catch (error) {

        console.error("loadPriceChart failed:", error);

        // Only show "unavailable" if there was never a
        // successful chart - a failed refresh tick on an
        // already-showing chart just logs and keeps the
        // last good data visible.

        if (!chartInstances["priceChart"]) {

            if (currentValueEl) {
                currentValueEl.textContent = "Price unavailable";
            }

            if (changeValueEl) {
                changeValueEl.textContent = "";
            }

        }

    }

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


function formatMultiple(value) {

    if (value === null || value === undefined) {
        return "-";
    }

    return `${Number(value).toFixed(2)}x`;

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