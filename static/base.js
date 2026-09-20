const searchButton = document.getElementById("searchButton");
const updateButton = document.getElementById("updateButton");
const nseInput = document.getElementById("nseInput");
const errorMessage = document.getElementById("errorMessage");


function goToCompany(rawNseCode) {

    const code = rawNseCode.trim().toUpperCase();

    if (!code) {

        if (errorMessage) {
            errorMessage.textContent = "Please enter an NSE code.";
        }

        return;

    }

    window.location.href = `/${code}`;

}


if (searchButton) {

    searchButton.addEventListener("click", () => {
        goToCompany(nseInput.value);
    });

}

if (nseInput) {

    nseInput.addEventListener("keydown", event => {

        if (event.key === "Enter") {
            goToCompany(nseInput.value);
        }

    });

}


if (updateButton && CURRENT_NSE_CODE) {

    updateButton.addEventListener("click", async () => {

        updateButton.disabled = true;
        updateButton.textContent = "Updating...";

        try {

            const response = await fetch(`/company/${CURRENT_NSE_CODE}/update`, {
                method: "POST"
            });

            if (!response.ok) {
                throw new Error("Unable to update company");
            }

            window.location.reload();

        }

        catch (error) {

            if (errorMessage) {
                errorMessage.textContent = error.message;
            }

            updateButton.disabled = false;
            updateButton.textContent = "Update";

        }

    });

}


/* =========================================
   PRICE TRACKER

   Markup lives in base.html (the shared shell), so this
   wiring runs on every page that has a company loaded.
   Defaults to Live mode on every page load, polling every
   1 minute.
========================================= */

let currentPriceMode = "live";
let priceRefreshIntervalId = null;

const LIVE_REFRESH_INTERVAL_MS = 60000; // 1 minute


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
    }, LIVE_REFRESH_INTERVAL_MS);

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
            ? "Live · updates every 1m"
            : "Delayed price · last 3 months";
    }

}


function setPriceMode(mode) {

    currentPriceMode = mode;

    updatePriceModeUI(mode);

    if (!CURRENT_NSE_CODE) {
        return;
    }

    if (mode === "live") {

        loadPriceChart(CURRENT_NSE_CODE, "live");
        startLivePriceRefresh(CURRENT_NSE_CODE);

    }

    else {

        stopLivePriceRefresh();
        loadPriceChart(CURRENT_NSE_CODE, "range");

    }

}


async function loadPriceChart(nseCode, mode) {

    const currentValueEl = document.getElementById("priceCurrentValue");
    const changeValueEl = document.getElementById("priceChangeValue");
    const canvas = document.getElementById("priceChart");

    // No early return on missing canvas: the title card's
    // price number should keep updating even on pages that
    // don't show the chart card (e.g. Financials). Only the
    // chart-drawing code below is skipped when canvas is null.

    try {

        const response = await fetch(`/company/${nseCode}/price-chart?mode=${mode}`);

        if (!response.ok) {
            throw new Error("Unable to load price data");
        }

        const data = await response.json();
        const candles = data.candles || [];

        if (candles.length === 0) {
            throw new Error("No price data returned");
        }

        const latestPrice = candles[candles.length - 1].price;

        if (currentValueEl) {
            currentValueEl.textContent = formatPrice(latestPrice);
        }

        if (changeValueEl) {

            changeValueEl.classList.remove("text-success", "text-primary");

            const changeValue = data.change_value;
            const changePercent = data.change_percent;

            if (changeValue !== null && changeValue !== undefined) {

                const isUp = changeValue >= 0;

                changeValueEl.classList.add(isUp ? "text-success" : "text-primary");

                changeValueEl.textContent =
                    `${isUp ? "+" : ""}${formatPrice(changeValue)} ` +
                    `(${isUp ? "+" : ""}${Number(changePercent).toFixed(2)}%)`;

            } else {

                changeValueEl.textContent = "";

            }

        }

        const labelFormatter = mode === "live" ? formatChartTime : formatChartDate;
        const titleFormatter = mode === "live" ? formatChartDateTime : formatChartDateFull;

        const labels = candles.map(candle => labelFormatter(candle.timestamp));
        const prices = candles.map(candle => candle.price);
        const fullLabels = candles.map(candle => titleFormatter(candle.timestamp));

        if (!canvas) {
            return;
        }

        if (chartInstances["priceChart"]) {
            chartInstances["priceChart"].destroy();
            delete chartInstances["priceChart"];
        }

        chartInstances["priceChart"] = new Chart(canvas, {

            type: "line",

            data: {
                labels: labels,
                datasets: [{
                    label: "Price",
                    data: prices,
                    borderColor: "#FF5722",
                    backgroundColor: "rgba(255, 87, 34, 0.1)",
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    borderWidth: 2,
                    tension: 0.25,
                    fill: true,
                }]
            },

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
                            title: context => fullLabels[context[0].dataIndex],
                            label: context => ` ${formatPrice(context.parsed.y)}`
                        }
                    },
                },
                scales: {
                    x: {
                        grid: { color: "#28282C", drawTicks: false },
                        ticks: {
                            color: "#636366",
                            font: { family: "JetBrains Mono", size: 10 },
                            autoSkip: true,
                            maxTicksLimit: 10,
                            maxRotation: 0,
                        },
                    },
                    y: {
                        grid: { color: "#28282C", drawTicks: false },
                        ticks: {
                            color: "#636366",
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


const priceModeLiveButton = document.getElementById("priceModeLiveButton");
const priceModeRangeButton = document.getElementById("priceModeRangeButton");

if (priceModeLiveButton) {
    priceModeLiveButton.addEventListener("click", () => setPriceMode("live"));
}

if (priceModeRangeButton) {
    priceModeRangeButton.addEventListener("click", () => setPriceMode("range"));
}


if (CURRENT_NSE_CODE) {

    updatePriceModeUI("live");
    loadPriceChart(CURRENT_NSE_CODE, "live");
    startLivePriceRefresh(CURRENT_NSE_CODE);

}