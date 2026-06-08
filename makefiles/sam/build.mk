##@ SAM

.PHONY: sam-validate sam-validate-euc1 sam-validate-usw2 \
        sam-build sam-build-euc1 sam-build-usw2 \
        sam-invoke-cut sam-invoke-generate

EUC1_TEMPLATE := infra/template-euc1.yaml
USW2_TEMPLATE := infra/template-usw2.yaml

sam-validate-euc1: ## Validate the eu-central-1 SAM template
	cd infra && sam validate --lint --template-file $(notdir $(EUC1_TEMPLATE)) --region eu-central-1

sam-validate-usw2: ## Validate the us-west-2 SAM template
	cd infra && sam validate --lint --template-file $(notdir $(USW2_TEMPLATE)) --region us-west-2

sam-validate: sam-validate-euc1 sam-validate-usw2  ## Validate both SAM templates

sam-build-euc1: ## Build cut_image Lambda artifacts (eu-central-1)
	cd infra && sam build --template-file $(notdir $(EUC1_TEMPLATE))

sam-build-usw2: ## Build generate_image Lambda artifacts (us-west-2)
	cd infra && sam build --template-file $(notdir $(USW2_TEMPLATE))

sam-build: sam-build-euc1 sam-build-usw2  ## Build both Lambda stacks

sam-invoke-cut: ## Run cut_image Lambda locally with the sample S3 event
	cd infra && sam local invoke CutImageFunction \
		--template-file $(notdir $(EUC1_TEMPLATE)) \
		--event ../packages/cut_image/events/s3-put.json \
		--parameter-overrides \
			DjangoURL=http://host.docker.internal:8000 \
			WebhookSharedSecret=local-dev-secret

sam-invoke-generate: ## Run generate_image Lambda locally (real Bedrock, sample payload)
	cd infra && sam local invoke GenerateImageFunction \
		--template-file $(notdir $(USW2_TEMPLATE)) \
		--region us-west-2 \
		--event ../packages/generate_image/events/lambda-invoke.json
