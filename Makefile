.PHONY: check
check:
	shellcheck $(wildcard *.sh)
