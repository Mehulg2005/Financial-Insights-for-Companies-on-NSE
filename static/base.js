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


// Update re-scrapes the CURRENT page's company, then reloads
// this same page so all sections re-fetch fresh data.

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