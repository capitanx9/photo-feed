##@ Tests

.PHONY: test test-cov test-lambdas

API_TEST_ENV := \
	DJANGO_SETTINGS_MODULE=api.settings.dev \
	POSTGRES_HOST=localhost \
	DJANGO_SECRET_KEY=test-secret \
	ALLOWED_HOSTS=testserver \
	POSTGRES_DB=api \
	POSTGRES_USER=api \
	POSTGRES_PASSWORD=api \
	AWS_ACCESS_KEY_ID=testing \
	AWS_SECRET_ACCESS_KEY=testing \
	AWS_DEFAULT_REGION=eu-west-1 \
	RATELIMIT_ENABLE=False \
	CELERY_TASK_ALWAYS_EAGER=1

test: ## Run api pytest suite (Postgres on localhost, Django settings)
	$(API_TEST_ENV) $(UV) run pytest -v --disable-warnings packages/api/tests

test-cov: ## Run api pytest with coverage report
	$(API_TEST_ENV) $(UV) run pytest --cov=$(API_SRC) --cov-report=term-missing packages/api/tests

test-lambdas: ## Run lambda pytest suites (no Django, moto-backed)
	$(UV) run pytest packages/cut_image/tests packages/generate_image/tests \
		-p no:django -v --disable-warnings
