##@ Prod (SSM)

.PHONY: prod-instance prod-shell prod-logs prod-status prod-redeploy

PROD_TAG_KEY     ?= Application
PROD_TAG_VALUE   ?= photo-feed-api
PROD_AWS_PROFILE ?= cx9-gmail
PROD_AWS_REGION  ?= eu-central-1

# Resolve the running EC2 by tag; prints the instance id.
prod-instance: ## Print the running prod EC2 instance id
	@aws ec2 describe-instances \
		--profile $(PROD_AWS_PROFILE) --region $(PROD_AWS_REGION) \
		--filters "Name=tag:$(PROD_TAG_KEY),Values=$(PROD_TAG_VALUE)" \
		          "Name=instance-state-name,Values=running" \
		--query 'Reservations[].Instances[].InstanceId' --output text

prod-shell: ## Open an interactive shell on the prod EC2 via SSM (no SSH port needed)
	@INSTANCE=$$($(MAKE) -s prod-instance) && \
	aws ssm start-session --target $$INSTANCE \
		--profile $(PROD_AWS_PROFILE) --region $(PROD_AWS_REGION)

prod-logs: ## Tail web container logs on the prod EC2 (Ctrl-C to stop)
	@INSTANCE=$$($(MAKE) -s prod-instance) && \
	aws ssm start-session --target $$INSTANCE \
		--profile $(PROD_AWS_PROFILE) --region $(PROD_AWS_REGION) \
		--document-name AWS-StartInteractiveCommand \
		--parameters 'command=["cd /srv/photo-feed && docker compose -f docker-compose.prod.yml logs -f --tail 100 web"]'

prod-status: ## Show compose ps on the prod EC2
	@INSTANCE=$$($(MAKE) -s prod-instance) && \
	aws ssm send-command --instance-ids $$INSTANCE \
		--profile $(PROD_AWS_PROFILE) --region $(PROD_AWS_REGION) \
		--document-name AWS-RunShellScript \
		--parameters 'commands=["cd /srv/photo-feed && docker compose -f docker-compose.prod.yml ps"]' \
		--query 'Command.CommandId' --output text \
		| xargs -I{} sh -c 'sleep 3 && aws ssm get-command-invocation --command-id {} --instance-id '"$$INSTANCE"' --profile $(PROD_AWS_PROFILE) --region $(PROD_AWS_REGION) --query StandardOutputContent --output text'

prod-redeploy: ## Trigger the cd-api workflow on main (forces a redeploy of the current tag)
	@gh workflow run cd-api.yml --ref main
