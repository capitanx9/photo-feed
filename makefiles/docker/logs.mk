##@ Logs

.PHONY: logs logs-web logs-db logs-redis

logs: ## Tail logs of every service
	$(COMPOSE) logs -f

logs-web: ## Tail web (Django) logs
	$(COMPOSE) logs -f web

logs-db: ## Tail Postgres logs
	$(COMPOSE) logs -f db

logs-redis: ## Tail Redis logs
	$(COMPOSE) logs -f redis
