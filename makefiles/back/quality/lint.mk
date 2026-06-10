##@ Lint & format

.PHONY: lint format mypy

lint: ## Run ruff check + format check
	$(UV) run ruff check .
	$(UV) run ruff format --check .

format: ## Auto-format code with ruff
	$(UV) run ruff format .
	$(UV) run ruff check --fix .

mypy: ## Run mypy on api package
	$(UV) run mypy $(API_SRC)
