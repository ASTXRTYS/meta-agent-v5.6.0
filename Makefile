.PHONY: install dev test lint evals evals-p0 evals-p1 evals-p2 test-fast test-contracts test-integration test-evals test-drift test-all test-collect test-legacy

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

lint:
	python -m py_compile meta_agent/state.py
	python -m py_compile meta_agent/configuration.py
	python -m py_compile meta_agent/model.py

evals:
	python -m meta_agent.evals.runner --all

evals-p0:
	python -m meta_agent.evals.runner --phase 0

evals-p1:
	python -m meta_agent.evals.runner --phase 1

evals-p2:
	python -m meta_agent.evals.runner --phase 2

test-fast:
	pytest tests/contracts/ -v -m contract

test-contracts:
	pytest tests/contracts/ -v

test-integration:
	pytest tests/integration/ -v

test-evals:
	pytest tests/evals/ -v -m eval

test-drift:
	pytest tests/drift/ -v

test-all:
	pytest tests/ -v --ignore=tests/unit

test-collect:
	pytest tests/ --co -q

test-legacy:
	pytest tests/unit/ -v
