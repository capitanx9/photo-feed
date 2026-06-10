##@ Front (quality)

.PHONY: lint-js

lint-js: ## Run ESLint on the Next.js project (packages/web)
	cd $(WEB) && npm run lint
