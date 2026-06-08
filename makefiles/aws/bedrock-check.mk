##@ AWS

.PHONY: bedrock-check

BEDROCK_PROFILE     ?= cx9-gmail
BEDROCK_REGION      ?= us-west-2
BEDROCK_MODEL_ID    ?= stability.stable-image-core-v1:1
BEDROCK_TMP_PAYLOAD := /tmp/sd-payload.json
BEDROCK_TMP_OUT     := /tmp/sd-out.json
BEDROCK_TMP_PNG     := /tmp/sd-out.png

bedrock-check: ## Smoke-test Bedrock access via real invoke (writes /tmp/sd-out.png)
	@printf '%s\n' '{"prompt":"a red apple on a white table, studio photo","mode":"text-to-image","aspect_ratio":"1:1","output_format":"png"}' > $(BEDROCK_TMP_PAYLOAD)
	aws bedrock-runtime invoke-model \
		--model-id "$(BEDROCK_MODEL_ID)" \
		--region $(BEDROCK_REGION) \
		--profile $(BEDROCK_PROFILE) \
		--content-type application/json \
		--accept application/json \
		--body fileb://$(BEDROCK_TMP_PAYLOAD) \
		$(BEDROCK_TMP_OUT)
	@$(UV) run python -c "import json, base64; d=json.load(open('$(BEDROCK_TMP_OUT)')); open('$(BEDROCK_TMP_PNG)','wb').write(base64.b64decode(d['images'][0])); print('seed:', d.get('seeds'), 'finish:', d.get('finish_reasons'))"
	@echo "Wrote $(BEDROCK_TMP_PNG)"
