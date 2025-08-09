PY ?= python
VENV ?= .venv
ACT = . $(VENV)/bin/activate

.PHONY: venv deps build test smoke test-gpu lint format clean

venv:
	$(PY) -m venv $(VENV)

deps: venv
	$(ACT) && pip install -r requirements.txt -q

build:
	@mkdir -p build
	cd build && cmake ../src >/dev/null && cmake --build . >/dev/null || true
	@echo "Build attempted (kernels may be skipped if no CUDA toolchain is present)."

test:
	$(ACT) && pytest -q

# CPU-only quick path; uses a tiny sim config to finish fast.
smoke: deps
	$(ACT) && ./scripts/codex.setup.sh
	$(ACT) && python main.py --features configs/features.yaml --sim configs/sim_config.smoke.yaml

# Optional: mark GPU tests with -m gpu if you add pytest markers later.
test-gpu:
	$(ACT) && pytest -q -m gpu

lint:
	$(ACT) && ruff check . || true

format:
	$(ACT) && ruff format . || true

clean:
	rm -rf build .venv __pycache__ .pytest_cache
