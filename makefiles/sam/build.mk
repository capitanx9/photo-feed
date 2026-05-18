##@ SAM

.PHONY: sam-validate sam-build sam-invoke

sam-validate: ## Validate infra/template.yaml against SAM spec
	cd infra && sam validate --lint

sam-build: ## Build Lambda artifacts to .aws-sam/build
	cd infra && sam build

sam-invoke: ## Run cut_image Lambda locally with the sample S3 event
	cd infra && sam local invoke CutImageFunction \
		--event ../packages/cut_image/events/s3-put.json \
		--parameter-overrides \
			DjangoURL=http://host.docker.internal:8000 \
			WebhookSharedSecret=local-dev-secret
