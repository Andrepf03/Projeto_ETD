.PHONY: setup extract transform load all dashboard test lint clean

setup:
	uv sync || pip install -e ".[dev]"

extract:
	python -m src.run extract

transform:
	python -m src.run transform

load:
	python -m src.run load

all:
	python -m src.run all

dashboard:
	streamlit run dashboard/app.py

test:
	pytest

lint:
	ruff check . && mypy src

clean:
	rm -rf data/staging/* data/curated/*
