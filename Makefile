PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
PYTEST ?= $(PYTHON) -m pytest
RUFF ?= $(PYTHON) -m ruff

.PHONY: help install lint test helm-lint helm-template ci legacy-demo stack-up schemas

help:
	@echo "Targets: install lint test helm-lint helm-template ci legacy-demo stack-up"

install:
	$(PIP) install -e ".[dev]"

lint:
	$(RUFF) check src tests controller scripts
	lint-imports

test:
	$(PYTEST)

helm-lint:
	helm lint charts/population
	helm lint charts/epik-operator

helm-template:
	helm template population charts/population --set strategy=clonal --set count=2
	helm template population charts/population --set strategy=transgenerational --set count=2
	helm template epik-operator charts/epik-operator

ci: lint test helm-lint helm-template

legacy-demo:
	PYTHONPATH=. $(PYTHON) scripts/legacy_demo.py

stack-up:
	docker compose -f deploy/docker/docker-compose.yaml up --build -d

schemas:
	PYTHONPATH=src $(PYTHON) -m epik.schema_dump
