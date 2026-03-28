.PHONY: install dev test lint evals evals-p0 evals-p1 evals-p2

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
