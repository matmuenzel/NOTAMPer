.PHONY: install lint test validate generate smoke clean

PY ?= python

install:
	$(PY) -m pip install -e '.[dev]'

lint:
	ruff check src tests

test:
	pytest -q

validate:
	notamper validate --cases cases

generate:
	notamper generate --out cases/generated --seed 2026

smoke:
	notamper run --models mock:naive,mock:robust --defenses none,filter --reps 1 --limit 40 --out results/smoke
	notamper report results/smoke

clean:
	rm -rf results build dist .pytest_cache .ruff_cache src/*.egg-info
