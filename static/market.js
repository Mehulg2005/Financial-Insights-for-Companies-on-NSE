const concallContainer = document.getElementById(
    "concallSummaries"
);

const concallStatus = document.getElementById(
    "concallStatus"
);


function escapeHtml(value) {
    const element = document.createElement("div");

    element.textContent = value || "";

    return element.innerHTML;
}


function renderConcallSummaries(summaries) {
    if (!concallContainer) {
        return;
    }

    if (!summaries.length) {
        concallContainer.innerHTML = `
            <p class="text-text-medium text-sm">
                No concall summaries are available.
            </p>
        `;

        return;
    }

    concallContainer.innerHTML = summaries.map((summary) => `
        <details class="bg-surface-raised border border-border rounded-xl p-4">
            <summary class="cursor-pointer flex items-center justify-between gap-3">
                <span class="font-display font-semibold">
                    ${escapeHtml(summary.period)}
                </span>

                <span class="font-mono text-xs text-text-muted">
                    AI Summary
                </span>
            </summary>

            <div class="mt-4 pt-4 border-t border-border text-sm leading-6 text-text-medium whitespace-pre-line">
                ${escapeHtml(summary.content)}
            </div>
        </details>
    `).join("");
}


async function loadConcallSummaries() {
    if (!CURRENT_NSE_CODE || !concallContainer) {
        return;
    }

    try {
        const response = await fetch(
            `/company/${encodeURIComponent(CURRENT_NSE_CODE)}/concall-summaries`
        );

        if (!response.ok) {
            const payload = await response.json().catch(
                () => ({})
            );

            throw new Error(
                payload.detail ||
                "Unable to load concall summaries."
            );
        }

        const payload = await response.json();
        const summaries = payload.summaries || [];

        renderConcallSummaries(summaries);

        if (concallStatus) {
            concallStatus.textContent =
                `${summaries.length} latest available`;
        }

    } catch (error) {
        if (concallStatus) {
            concallStatus.textContent = "Unavailable";
        }

        concallContainer.innerHTML = `
            <p class="text-primary text-sm">
                ${escapeHtml(error.message)}
            </p>
        `;
    }
}


loadConcallSummaries();