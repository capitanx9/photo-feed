##@ Django · Users

.PHONY: superuser

superuser: ## Create a Django superuser
	$(COMPOSE) exec web python manage.py createsuperuser
