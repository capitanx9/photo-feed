##@ OpenAPI

.PHONY: gen-api gen-api-check swagger-up

gen-api: ## Regenerate schemas/openapi.yaml from current code
	cd $(API) && POSTGRES_HOST=localhost $(UV) run python manage.py spectacular \
		--file $(CURDIR)/schemas/openapi.yaml

gen-api-check: ## Fail if schemas/openapi.yaml drifts from current code
	cd $(API) && POSTGRES_HOST=localhost $(UV) run python manage.py spectacular \
		--file /tmp/openapi.yaml
	diff schemas/openapi.yaml /tmp/openapi.yaml

swagger-up: ## Open Swagger UI in the browser (needs `make up`)
	open http://localhost:8000/api/schema/swagger-ui/
