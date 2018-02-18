.PHONY: lint
lint:
	shellcheck $(wildcard *.sh)
	flake8 $(wildcard *.py)
	mypy --ignore-missing-imports $(wildcard *.py)
