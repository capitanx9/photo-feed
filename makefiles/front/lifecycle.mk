##@ Front (Next.js)

.PHONY: front-install front-dev front-build front-start

front-install: ## Install web deps (npm install in packages/web)
	cd $(WEB) && npm install

front-dev: ## Run the Next.js dev server (packages/web)
	cd $(WEB) && npm run dev

front-build: ## Production build of the Next.js app
	cd $(WEB) && npm run build

front-start: ## Serve the production build (after front-build)
	cd $(WEB) && npm run start
