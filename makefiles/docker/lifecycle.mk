##@ Stack

.PHONY: up down

up: ## Start dev stack (web + db + redis)
	$(COMPOSE) up -d --build

down: ## Stop dev stack
	$(COMPOSE) down
