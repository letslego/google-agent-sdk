PYTHON ?= python3

.PHONY: venv install ingest run-api run-adk lint test

venv:
	$(PYTHON) -m venv .venv

install:
	. .venv/bin/activate && pip install --upgrade pip && pip install -e ".[dev]"

ingest:
	. .venv/bin/activate && python scripts/ingest.py

run-api:
	. .venv/bin/activate && uvicorn enterprise_rag.app:app --reload

run-adk:
	. .venv/bin/activate && adk run src/enterprise_rag/adk_agent

lint:
	. .venv/bin/activate && ruff check src scripts

test:
	. .venv/bin/activate && pytest
