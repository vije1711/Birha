.PHONY: qa-fast fmt help

qa-fast:
	bash scripts/qa.sh

fmt:
	@echo "No-op: formatting skipped (zero deps)"

help:
	@echo "Available targets:"
	@echo "  qa-fast  Run quick QA checks"
	@echo "  fmt      No-op formatting placeholder"
