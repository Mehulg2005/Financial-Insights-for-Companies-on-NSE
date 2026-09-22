from fastapi import APIRouter, HTTPException

from utils.scraper import fetch_latest_concall_summaries


router = APIRouter(
    prefix="/company",
    tags=["Concalls"],
)


@router.get("/{nse_code}/concall-summaries")
def get_concall_summaries(nse_code: str):
    nse_code = nse_code.upper().strip()

    try:
        summaries = fetch_latest_concall_summaries(
            nse_code=nse_code,
            limit=6,
        )

        return {
            "nse_code": nse_code,
            "summaries": summaries,
        }

    except Exception as error:
        print("\n" + "=" * 100)
        print("CONCALL SUMMARY FETCH FAILED")
        print("=" * 100)
        print(str(error))

        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve concall summaries from Screener.",
        ) from error