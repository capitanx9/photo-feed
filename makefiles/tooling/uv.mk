##@ uv

.PHONY: install lock info

install: ## Sync workspace dependencies
	$(UV) sync

lock: ## Refresh uv.lock
	$(UV) lock

info: ## Show uv + Python version info
	@$(UV) --version
	@$(UV) python list --only-installed
