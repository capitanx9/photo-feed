##@ Demo data

.PHONY: seed-users seed-posts seed-orders seed-all flush-demo reset-demo

seed-users: ## Create the 10 demo users (idempotent)
	$(COMPOSE) exec web python manage.py seed_users

seed-posts: ## Create 5 posts per demo user (idempotent)
	$(COMPOSE) exec web python manage.py seed_posts

seed-orders: ## Create sample orders between demo users (idempotent)
	$(COMPOSE) exec web python manage.py seed_orders

seed-all: ## Run all seed commands in order
	$(COMPOSE) exec web python manage.py seed_all

flush-demo: ## Delete every @photo-feed.local user (CASCADE removes their data)
	$(COMPOSE) exec web python manage.py flush_demo

reset-demo: flush-demo seed-all ## Wipe demo data and reseed from scratch
