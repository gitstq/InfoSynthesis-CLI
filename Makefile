.PHONY: help install install-dev test lint format clean build dist upload

help:
	@echo "InfoSynthesis-CLI Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  install      Install the package"
	@echo "  install-dev  Install with development dependencies"
	@echo "  test         Run tests"
	@echo "  lint         Run linters"
	@echo "  format       Format code with black"
	@echo "  clean        Clean build artifacts"
	@echo "  build        Build distribution packages"
	@echo "  dist         Build and check distribution"
	@echo "  upload       Upload to PyPI"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	pip install pytest pytest-cov black flake8 mypy

test:
	python -m pytest tests/ -v --cov=infosynthesis_cli --cov-report=term-missing

lint:
	flake8 infosynthesis_cli/ --max-line-length=120
	mypy infosynthesis_cli/ --ignore-missing-imports

format:
	black infosynthesis_cli/ --line-length=120

clean:
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

build: clean
	python setup.py sdist bdist_wheel

dist: build
	twine check dist/*

upload: dist
	twine upload dist/*
