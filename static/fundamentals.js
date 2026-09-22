/* =========================================
   FUNDAMENTALS PAGE
========================================= */

const FEATURE_METRIC_CONFIG = {
    "Effective Tax Rate": { formatter: formatRatioAsPercent },
    "Operating Margin": { formatter: formatRatioAsPercent },
    "Sales": { formatter: formatNumber },
    "Net Profit": { formatter: formatNumber },
    "Profit before Tax": { formatter: formatNumber },
    "Profit After Tax": { formatter: formatNumber },
    "EPS": { formatter: formatNumber },

    "Cash from Operating Activity (CFO)": { formatter: formatNumber },
    "CFO Contribution": { formatter: formatRatioAsPercent },
    "Cash Conversion (CFO / Net Profit)": { formatter: formatRatioAsPercent },

    "Reserves": { formatter: formatNumber },
    "Equity Capital": { formatter: formatNumber },
    "Investment Migration": { formatter: formatRatioAsPercent },
    "Borrowings to Net Worth Ratio": { formatter: formatRatio },
    "Interest Coverage Ratio": { formatter: formatMultiple },
};


function getMetricConfig(metric) {

    return FEATURE_METRIC_CONFIG[metric] || { formatter: formatNumber };

}


const FEATURE_CHART_GROUPS = {

    profitability: [
        { canvas: "profitabilityChart1", toggles: "profitabilityToggles1", metrics: ["Effective Tax Rate", "Operating Margin"], dualAxis: false },
        { canvas: "profitabilityChart2", toggles: "profitabilityToggles2", metrics: ["Sales", "Net Profit"], dualAxis: false },
        { canvas: "profitabilityChart3", toggles: "profitabilityToggles3", metrics: ["Profit before Tax", "Profit After Tax"], dualAxis: false },
        { canvas: "profitabilityChart4", toggles: "profitabilityToggles4", metrics: ["EPS"], dualAxis: false },
    ],

    cash_flow_quality: [
        { canvas: "cashflowChart1", toggles: "cashflowToggles1", metrics: ["Cash Conversion (CFO / Net Profit)", "CFO Contribution"], dualAxis: false },
        { canvas: "cashflowChart2", toggles: "cashflowToggles2", metrics: ["Cash from Operating Activity (CFO)"], dualAxis: false },
    ],

    growth_trends: [
        { canvas: "growthTrendsChart1", toggles: "growthTrendsToggles1", metrics: ["Investment Migration", "Borrowings to Net Worth Ratio"], dualAxis: false },
        { canvas: "growthTrendsChart2", toggles: "growthTrendsToggles2", metrics: ["Reserves", "Equity Capital"], dualAxis: false },
        { canvas: "growthTrendsChart3", toggles: "growthTrendsToggles3", metrics: ["Interest Coverage Ratio"], dualAxis: false },
    ],

};


/* =========================================
   HERO VERDICT
========================================= */

function renderHeroVerdict(analysisData) {

    const wordEl = document.getElementById("heroVerdictWord");
    const summaryEl = document.getElementById("heroVerdictSummary");

    const verdict = analysisData.overall_verdict;

    if (wordEl) {

        wordEl.textContent = verdict;
        wordEl.className = verdict === "POSITIVE" ? "text-success"
            : verdict === "NEGATIVE" ? "text-primary"
            : "text-warning";

    }

    if (summaryEl) {

        const positiveCount = analysisData.categories.filter(c => c.verdict === "POSITIVE").length;
        const negativeCount = analysisData.categories.filter(c => c.verdict === "NEGATIVE").length;
        const mixedCount = analysisData.categories.filter(c => c.verdict === "MIXED").length;

        summaryEl.textContent =
            `Based on trend analysis across the last periods: ${positiveCount} of 5 categories positive, ` +
            `${negativeCount} negative, ${mixedCount} mixed. See the breakdown below for the specific reasons behind each.`;

    }

}


/* =========================================
   DISTRESS SCORE CHIPS
========================================= */

const DISTRESS_SCORE_DISPLAY = {
    altman_z: {
        label: "Altman Z",
        format: data => data.score !== null && data.score !== undefined ? `${data.score}` : "—",
    },
    piotroski_f: {
        label: "Piotroski F",
        format: data => data.score !== null && data.score !== undefined ? `${data.score}/${data.max_score}` : "—",
    },
    beneish_m: {
        label: "Beneish M",
        format: () => "—",
    },
    ohlson_o: {
        label: "Ohlson O",
        format: data => data.probability !== null && data.probability !== undefined ? `${(data.probability * 100).toFixed(1)}%` : "—",
    },
    springate_s: {
        label: "Springate S",
        format: data => data.score !== null && data.score !== undefined ? `${data.score}` : "—",
    },
    zmijewski_x: {
        label: "Zmijewski X",
        format: data => data.score !== null && data.score !== undefined ? `${data.score}` : "—",
    },
};


const DISTRESS_SCORE_THEORY = {

    altman_z: "The Altman Z-score is a financial formula developed in 1968 by NYU professor Edward Altman to predict the probability that a company will go bankrupt within two years. By combining five key business ratios measuring liquidity, profitability, and leverage, it assesses a firm's overall financial health.\n\nA score above 2.99 places a company in the Safe Zone, while a score below 1.81 indicates the Distress Zone, signaling a high risk of failure. Scores between 1.81 and 2.99 fall into the Grey Zone, meaning the company's financial future is uncertain.",

    piotroski_f: "The Piotroski F-Score is a financial metric developed in 2000 by accounting professor Joseph Piotroski to evaluate the financial strength of value stocks. By combining nine binary criteria measuring profitability, leverage, and operating efficiency, it assesses whether a company's financial position is improving or worsening.\n\nA score of 8 to 9 places a company in the Strong Zone, indicating high quality and positive momentum. Scores of 0 to 3 indicate the Weak Zone, signaling poor financial health and high risk, while scores between 4 and 7 reflect an average baseline.",

    beneish_m: "The Beneish M-Score is a mathematical model developed in 1999 by Professor Messod Beneish to predict the probability that a company has manipulated its earnings. By combining eight financial ratios tracking anomalies in revenue, asset depreciation, and leverage, it uncovers aggressive accounting practices.\n\nA score above -1.78 (e.g., -1.50) places a company in the Distress Zone, signaling a high likelihood of financial manipulation. Conversely, a score below -1.78 (e.g., -2.50) indicates the Safe Zone, meaning the company is unlikely to be an earnings manipulator.",

    ohlson_o: "The Ohlson O-Score is a probabilistic model developed in 1980 by Dr. James Ohlson to estimate the likelihood of a company entering bankruptcy within one year. By combining nine financial factors - including size, total liabilities, net income, and working capital - it utilizes logistic regression to output a direct default probability.\n\nA score above 0.5 (corresponding to a high statistical probability) places a company in the Distress Zone, indicating a severe risk of default. A score below 0.5 represents the Safe Zone, where the company exhibits standard financial stability.",

    springate_s: "The Springate S-Score is a bankruptcy prediction model developed in 1978 by Gordon Springate at Simon Fraser University, building upon the foundations of the Altman Z-score. By combining four key financial ratios that measure working capital efficiency, profitability before interest and taxes, and asset utilization, it determines insolvency risks.\n\nA score below 0.862 places a company in the Distress Zone, flagging the firm as a high-risk candidate for failure. A score above 0.862 places the firm in the Safe Zone, indicating an acceptable standard of financial health.",

    zmijewski_x: "The Zmijewski X-Score is a financial distress model developed in 1984 by Kent Zmijewski to evaluate the probability of a company facing bankruptcy. By combining three core financial metrics that analyze return on assets, leverage, and liquidity, it provides a streamlined assessment of corporate solvency.\n\nA score above 0 (reflecting a predicted probability of bankruptcy greater than 50%) places a company in the Distress Zone, signaling imminent financial trouble. A score below 0 places it in the Safe Zone, indicating the firm is financially sound.",

};


const SEVERITY_COLORS = {
    positive: { background: "#0F291E", border: "rgba(16, 185, 129, 0.4)", text: "#10B981" },
    negative: { background: "#2C1714", border: "rgba(255, 87, 34, 0.4)", text: "#FF5722" },
    mixed:    { background: "#232018", border: "rgba(245, 158, 11, 0.4)", text: "#F59E0B" },
};


function buildDistressScoreChip(key, config, scoreData) {

    const severity = String(scoreData.severity || "").toLowerCase();
    const colors = SEVERITY_COLORS[severity] || null;

    const chip = document.createElement("div");
    chip.className = [
        "score-chip",
        "relative",
        "border",
        "rounded-xl",
        "p-3",
        severity ? `score-chip-${severity}` : "",
    ].filter(Boolean).join(" ");

    chip.style.backgroundColor = colors ? colors.background : "#1C1C1F";
    chip.style.borderColor = colors ? colors.border : "#28282C";

    const labelEl = document.createElement("div");
    labelEl.className = "font-mono text-[10px] uppercase tracking-widest text-text-muted mb-1";
    labelEl.textContent = config.label;

    const valueEl = document.createElement("div");
    valueEl.className = "score-chip-value font-mono text-lg font-semibold";
    valueEl.style.color = colors ? colors.text : "#FFFFFF";
    valueEl.textContent = config.format(scoreData);

    chip.appendChild(labelEl);
    chip.appendChild(valueEl);

    if (scoreData.note) {

        const noteEl = document.createElement("div");
        noteEl.className = "font-mono text-[10px] text-text-muted mt-0.5";
        noteEl.textContent = scoreData.note;
        chip.appendChild(noteEl);

    }

    const theoryText = DISTRESS_SCORE_THEORY[key];

    if (theoryText) {

        const tooltip = document.createElement("div");
        tooltip.className = "score-chip-tooltip";
        tooltip.textContent = theoryText;

        chip.appendChild(tooltip);

    }

    return chip;

}


function renderDistressScorePlaceholders() {

    const container = document.getElementById("distressScoresContainer");

    if (!container) {
        return;
    }

    container.innerHTML = "";

    Object.keys(DISTRESS_SCORE_DISPLAY).forEach(key => {

        const config = DISTRESS_SCORE_DISPLAY[key];

        container.appendChild(buildDistressScoreChip(key, config, { note: "Pending" }));

    });

}


function renderDistressScores(scores) {

    const container = document.getElementById("distressScoresContainer");

    if (!container) {
        return;
    }

    container.innerHTML = "";

    Object.keys(DISTRESS_SCORE_DISPLAY).forEach(key => {

        const config = DISTRESS_SCORE_DISPLAY[key];
        const scoreData = scores[key] || {};

        container.appendChild(buildDistressScoreChip(key, config, scoreData));

    });

}


async function loadDistressScores(nseCode) {

    try {

        const response = await fetch(`/company/${nseCode}/distress-scores`);

        if (!response.ok) {
            throw new Error("Unable to load distress scores");
        }

        const data = await response.json();

        renderDistressScores(data.scores);

    }

    catch (error) {

        console.error("loadDistressScores failed:", error);
        renderDistressScorePlaceholders();

    }

}


/* =========================================
   PILLAR CARDS
========================================= */

function buildAnalysisCard(category, index) {

    const verdict = String(category.verdict || "").toLowerCase();

    const card = document.createElement("div");
    card.className = [
        "pillar-card",
        "border",
        "rounded-2xl",
        "p-4",
        verdict ? `pillar-card-${verdict}` : "",
    ].filter(Boolean).join(" ");

    const eyebrow = document.createElement("div");
    eyebrow.className = "flex items-center justify-between mb-2";

    const pillarLabel = document.createElement("span");
    pillarLabel.className = "font-mono text-[10px] uppercase tracking-widest text-text-muted";
    pillarLabel.textContent = `Pillar 0${index + 1}`;

    const badge = document.createElement("span");
    badge.className = `verdict-badge verdict-${category.verdict.toLowerCase()}`;
    badge.textContent = category.verdict;

    eyebrow.appendChild(pillarLabel);
    eyebrow.appendChild(badge);

    const title = document.createElement("h3");
    title.className = "font-display font-semibold text-base mb-2";
    title.textContent = category.category;

    const list = document.createElement("ul");
    list.className = "space-y-1.5 text-xs text-text-medium";

    category.bullets.slice(0, 2).forEach(bulletText => {

        const item = document.createElement("li");
        item.className = "flex gap-1.5";

        const dash = document.createElement("span");
        dash.className = "text-text-muted shrink-0";
        dash.textContent = "—";

        const text = document.createElement("span");
        text.textContent = bulletText;

        item.appendChild(dash);
        item.appendChild(text);
        list.appendChild(item);

    });

    card.appendChild(eyebrow);
    card.appendChild(title);
    card.appendChild(list);

    return card;

}


/* =========================================
   METRIC LINE CHARTS
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

    const presentMetrics = group.metrics.filter(metric => valuesByMetric[metric]);

    if (presentMetrics.length === 0) {
        return;
    }

    const usesRightAxis = group.dualAxis && presentMetrics.length > 1;

    const datasets = presentMetrics.map((metric, index) => {

        const color = CHART_PALETTE[index % CHART_PALETTE.length];

        const axisId = group.dualAxis
            ? (index === 0 ? "yLeft" : "yRight")
            : "yShared";

        return {
            label: metric,
            data: periods.map(period => valuesByMetric[metric][period] ?? null),
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

    const tickFontConfig = {
        color: "#636366",
        font: { family: "JetBrains Mono", size: 11 },
    };

    const scales = {
        x: {
            grid: { color: "#28282C", drawTicks: false },
            ticks: tickFontConfig,
        },
    };

    if (group.dualAxis) {

        const leftFormatter = getMetricConfig(presentMetrics[0]).formatter;
        const rightFormatter = presentMetrics[1] ? getMetricConfig(presentMetrics[1]).formatter : leftFormatter;

        scales.yLeft = {
            position: "left",
            grid: { color: "#28282C", drawTicks: false },
            ticks: { ...tickFontConfig, callback: value => leftFormatter(value) },
        };

        scales.yRight = {
            position: "right",
            display: usesRightAxis,
            grid: { drawOnChartArea: false },
            ticks: { ...tickFontConfig, callback: value => rightFormatter(value) },
        };

    } else {

        const sharedFormatter = getMetricConfig(presentMetrics[0]).formatter;

        scales.yShared = {
            position: "left",
            grid: { color: "#28282C", drawTicks: false },
            ticks: { ...tickFontConfig, callback: value => sharedFormatter(value) },
        };

    }

    chartInstances[group.canvas] = new Chart(canvas, {

        type: "line",

        data: { labels: periods, datasets: datasets },

        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: "#1C1C1F",
                    borderColor: "#28282C",
                    borderWidth: 1,
                    titleColor: "#8E8E93",
                    bodyColor: "#FFFFFF",
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

            chart.setDatasetVisibility(index, checkbox.checked);
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
   OTHER METRICS SCATTER CHARTS
========================================= */

function hexToRgba(hex, alpha) {

    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);

    return `rgba(${r}, ${g}, ${b}, ${alpha})`;

}


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

        const angle = Math.atan2(last.y - secondLast.y, last.x - secondLast.x);
        const arrowLength = 9;

        ctx.save();
        ctx.fillStyle = "#FF5722";
        ctx.beginPath();
        ctx.moveTo(last.x, last.y);
        ctx.lineTo(last.x - arrowLength * Math.cos(angle - Math.PI / 6), last.y - arrowLength * Math.sin(angle - Math.PI / 6));
        ctx.lineTo(last.x - arrowLength * Math.cos(angle + Math.PI / 6), last.y - arrowLength * Math.sin(angle + Math.PI / 6));
        ctx.closePath();
        ctx.fill();
        ctx.restore();

        const rawData = chart.data.datasets[0].data;
        const firstPeriod = rawData[0]?.period;
        const lastPeriod = rawData[rawData.length - 1]?.period;

        ctx.save();
        ctx.font = "11px 'JetBrains Mono', monospace";
        ctx.textAlign = "center";

        if (firstPeriod) {
            ctx.fillStyle = "#8E8E93";
            ctx.fillText(firstPeriod, first.x, first.y - 14);
        }

        if (lastPeriod) {
            ctx.fillStyle = "#FF5722";
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

    renderScatterChart("totalLiabilitiesVsAssetsChart", otherMetrics.total_liabilities_vs_total_assets, "Total Liabilities", "Total Assets");
    renderScatterChart("borrowingsVsAssetsChart", otherMetrics.borrowings_vs_total_assets, "Borrowings", "Total Assets");

}


function renderScatterChart(canvasId, points, yLabel, xLabel) {

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

    const chartData = points.map(point => ({ x: point.x, y: point.y, period: point.period }));

    const pointBackgroundColors = chartData.map((_, index) => {
        const progress = chartData.length > 1 ? index / (chartData.length - 1) : 1;
        return hexToRgba("#FF5722", 0.3 + progress * 0.7);
    });

    const pointRadii = chartData.map((_, index) => {
        const progress = chartData.length > 1 ? index / (chartData.length - 1) : 1;
        return 3 + progress * 4;
    });

    chartInstances[canvasId] = new Chart(canvas, {

        type: "scatter",

        data: {
            datasets: [{
                label: `${yLabel} vs ${xLabel}`,
                data: chartData,
                showLine: true,
                borderColor: "#FF5722",
                backgroundColor: "#FF5722",
                pointBackgroundColor: pointBackgroundColors,
                pointBorderColor: "transparent",
                pointRadius: pointRadii,
                pointHoverRadius: pointRadii.map(r => r + 2),
                borderWidth: 2,
                tension: 0.15,
            }]
        },

        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: "#1C1C1F",
                    borderColor: "#28282C",
                    borderWidth: 1,
                    titleColor: "#8E8E93",
                    bodyColor: "#FFFFFF",
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
                    title: { display: true, text: xLabel, color: "#8E8E93" },
                    grid: { color: "#28282C", drawTicks: false },
                    ticks: { color: "#636366", font: { family: "JetBrains Mono", size: 11 }, callback: value => formatNumber(value) },
                },
                y: {
                    title: { display: true, text: yLabel, color: "#8E8E93" },
                    grid: { color: "#28282C", drawTicks: false },
                    ticks: { color: "#636366", font: { family: "JetBrains Mono", size: 11 }, callback: value => formatNumber(value) },
                },
            },
        },

        plugins: [TREND_DIRECTION_PLUGIN],

    });

}


/* =========================================
   LOAD
========================================= */

async function loadFundamentals(nseCode) {

    renderDistressScorePlaceholders();

    try {

        const [featuresResponse, analysisResponse] = await Promise.all([
            fetch(`/company/${nseCode}/features`),
            fetch(`/company/${nseCode}/fundamental-analysis`),
        ]);

        if (!featuresResponse.ok || !analysisResponse.ok) {
            throw new Error("Unable to load fundamentals data");
        }

        const featuresData = await featuresResponse.json();
        const analysisData = await analysisResponse.json();

        renderTitleCard(analysisData.company_name);

        renderHeroVerdict(analysisData);

        const cardsContainer = document.getElementById("analysisCardsContainer");

        if (cardsContainer) {

            cardsContainer.innerHTML = "";

            analysisData.categories.forEach((category, index) => {
                cardsContainer.appendChild(buildAnalysisCard(category, index));
            });

        }

        FEATURE_CHART_GROUPS.profitability.forEach(group => {
            renderMetricLineChart(group, featuresData.profitability);
        });

        FEATURE_CHART_GROUPS.cash_flow_quality.forEach(group => {
            renderMetricLineChart(group, featuresData.cash_flow_quality);
        });

        FEATURE_CHART_GROUPS.growth_trends.forEach(group => {
            renderMetricLineChart(group, featuresData.growth_trends);
        });

        renderOtherMetricsCharts(featuresData.other_metrics);

    }

    catch (error) {

        console.error("loadFundamentals failed:", error);

        const errorMessage = document.getElementById("errorMessage");

        if (errorMessage) {
            errorMessage.textContent = error.message;
        }

    }

    loadDistressScores(nseCode);

}
/* =========================================
   CATEGORY TOGGLE (Profitability / Cash Flow
   Quality / Growth Trends / Other Metrics)
========================================= */

const CATEGORY_CANVAS_IDS = {
    profitability: ["profitabilityChart1", "profitabilityChart2", "profitabilityChart3", "profitabilityChart4"],
    cash_flow_quality: ["cashflowChart1", "cashflowChart2"],
    growth_trends: ["growthTrendsChart1", "growthTrendsChart2", "growthTrendsChart3"],
    other_metrics: ["totalLiabilitiesVsAssetsChart", "borrowingsVsAssetsChart"],
};


function switchCategoryPanel(category) {

    Object.keys(CATEGORY_CANVAS_IDS).forEach(key => {

        const panel = document.getElementById(`categoryPanel-${key}`);
        const button = document.querySelector(`.category-toggle-button[data-category="${key}"]`);

        if (panel) {
            panel.classList.toggle("hidden", key !== category);
        }

        if (button) {
            button.classList.toggle("active", key === category);
        }

    });

    // All charts across all 4 categories are built up-front
    // during loadFundamentals(), while 3 of the 4 panels are
    // display:none - so their canvases render at 0 size.
    // Resizing on reveal is the same fix used for tab
    // switching earlier in this project.

    const canvasIds = CATEGORY_CANVAS_IDS[category] || [];

    canvasIds.forEach(id => {

        const chart = chartInstances[id];

        if (chart) {
            chart.resize();
        }

    });

}


document.querySelectorAll(".category-toggle-button").forEach(button => {

    button.addEventListener("click", () => {
        switchCategoryPanel(button.dataset.category);
    });

});

if (CURRENT_NSE_CODE) {
    loadFundamentals(CURRENT_NSE_CODE);
}