##@ Demo data

.PHONY: seed-users seed-posts seed-orders seed-all reset

seed-users: ## Create the 10 demo users (idempotent)
	$(COMPOSE) exec web python manage.py seed_users

seed-posts: ## Create 5 posts per demo user (idempotent)
	$(COMPOSE) exec web python manage.py seed_posts

seed-orders: ## Create sample orders between demo users (idempotent)
	$(COMPOSE) exec web python manage.py seed_orders

seed-all: ## Run all seed commands in order
	$(COMPOSE) exec web python manage.py seed_all

reset: ## Delete every user (CASCADE removes posts, media, orders)
	$(COMPOSE) exec web python manage.py reset_all
