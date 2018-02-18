.PHONY: lint
lint:
	shellcheck $(wildcard *.sh)
	mypy $(wildcard *.py)
