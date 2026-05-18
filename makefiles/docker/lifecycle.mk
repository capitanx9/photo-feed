##@ Stack

.PHONY: up down

up: ## Start dev stack (web + db + redis + mailhog)
	$(COMPOSE) up -d --build

down: ## Stop dev stack
	$(COMPOSE) down
