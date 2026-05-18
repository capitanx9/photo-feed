##@ Tests

.PHONY: test test-cov

test: ## Run pytest across the workspace
	$(UV) run pytest -v --disable-warnings

test-cov: ## Run pytest with coverage report
	$(UV) run pytest --cov=$(API_SRC) --cov-report=term-missing
