# ==================================================
# Screener Project V2 - Makefile
#
# Run these from the repo root (same folder as api.py).
# ==================================================

VENV_ACTIVATE := ~/.venv/bin/activate


.PHONY: activate run deactivate


# --------------------------------------------------
# NOTE ON activate / deactivate
#
# Each line `make` runs happens in its OWN throwaway
# subshell that exits as soon as that command finishes.
# That means `make activate` cannot leave your venv
# activated in the terminal you're typing in - the
# activation would only exist inside make's subshell,
# which is already gone by the time make returns control
# to you. This is a property of how `make` and shells
# work, not something a Makefile can work around.
#
# So `activate` and `deactivate` below just print the
# exact command to run - you still need to type (or
# copy-paste) it into your own terminal yourself, not run
# it via `make`, for it to actually take effect there.
#
# `make run`, on the other hand, DOES work end-to-end via
# make, because it activates the venv and starts uvicorn
# in the same subshell, on the same line.
# --------------------------------------------------

activate:
	@echo "Run this directly in your terminal (not via make):"
	@echo "  source $(VENV_ACTIVATE)"


run:
	source $(VENV_ACTIVATE) && uvicorn api:app --reload --host 127.0.0.1 --port 8000


deactivate:
	@echo "Run this directly in your terminal (not via make):"
	@echo "  deactivate"