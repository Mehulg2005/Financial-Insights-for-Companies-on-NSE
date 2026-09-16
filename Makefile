# ==================================================
# Screener Project V2 - Makefile
#
# Run these from the repo root (same folder as api.py).
# ==================================================

VENV_ACTIVATE := ~/.venv/bin/activate


.PHONY: install run


# --------------------------------------------------
# NOTE
#
# Each line `make` runs happens in its own throwaway
# subshell that exits as soon as that command finishes -
# so venv activation only persists for the rest of THAT
# line, not into your terminal or into other `make`
# targets. Both commands below activate the venv and do
# their actual work in the same line, for that reason.
# --------------------------------------------------

install:
	source $(VENV_ACTIVATE) && pip install -r requirements.txt


run:
	source $(VENV_ACTIVATE) && uvicorn api:app --reload --host 127.0.0.1 --port 8000