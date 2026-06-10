##@ OpenAPI

.PHONY: gen-api gen-api-check openapi-types swagger-up

gen-api: ## Regenerate schemas/openapi.yaml from current code
	cd $(API) && POSTGRES_HOST=localhost $(UV) run python manage.py spectacular \
		--file $(CURDIR)/schemas/openapi.yaml

gen-api-check: ## Fail if schemas/openapi.yaml drifts from current code
	cd $(API) && POSTGRES_HOST=localhost $(UV) run python manage.py spectacular \
		--file /tmp/openapi.yaml
	diff schemas/openapi.yaml /tmp/openapi.yaml

openapi-types: ## Regenerate web TS types from schemas/openapi.yaml
	cd packages/web && npx --yes openapi-typescript ../../schemas/openapi.yaml -o src/lib/api/schema.d.ts

swagger-up: ## Open Swagger UI in the browser (needs `make up`)
	open http://localhost:8000/api/schema/swagger-ui/
