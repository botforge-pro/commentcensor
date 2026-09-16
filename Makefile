.DEFAULT_GOAL := build

.PHONY: install format lint comments test-build test build

install:
	python -m pip install -e ".[dev]"

format:
	python -m ruff check --fix src tests
	python -m ruff format src tests

comments:
	commentcensor .

lint: comments
	python -m ruff check src tests
	python -m ruff format --check src tests

test-build:
	python -m compileall -q src tests

test:
	python -m pytest -q

build: lint test-build test
	python -m build
