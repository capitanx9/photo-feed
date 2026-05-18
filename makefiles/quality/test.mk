##@ Tests

.PHONY: test test-cov

test: ## Run pytest across the workspace
	POSTGRES_HOST=localhost $(UV) run pytest -v --disable-warnings

test-cov: ## Run pytest with coverage report
	POSTGRES_HOST=localhost $(UV) run pytest --cov=$(API_SRC) --cov-report=term-missing
