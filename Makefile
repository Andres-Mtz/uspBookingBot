.PHONY: help install test lint format type-check run docker-build docker-up docker-down clean

help:
	@echo "Available commands:"
	@echo "  make install       Install dependencies"
	@echo "  make test          Run tests with coverage"
	@echo "  make lint          Run flake8 linter"
	@echo "  make format        Format code with black"
	@echo "  make type-check    Run mypy type checker"
	@echo "  make run           Run the booking bot"
	@echo "  make docker-build  Build Docker image"
	@echo "  make docker-up     Start Docker container"
	@echo "  make docker-down   Stop Docker container"
	@echo "  make clean         Clean up generated files"

install:
	pip install -r requirements.txt

test:
	pytest --cov=src/usp_booking_bot --cov-report=html --cov-report=term tests/

lint:
	flake8 src/ tests/

format:
	black src/ tests/

type-check:
	mypy src/

run:
	python -m src.usp_booking_bot.main

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
