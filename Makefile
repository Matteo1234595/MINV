.PHONY: dev dev-web dev-api test test-web test-api

DEV_WEB_CMD = npm --prefix apps/web run dev
DEV_API_CMD = uvicorn app.main:app --reload --app-dir apps/api

TEST_WEB_CMD = npm --prefix apps/web run lint
TEST_API_CMD = python -m pytest apps/api

dev: dev-web

dev-web:
	$(DEV_WEB_CMD)

dev-api:
	$(DEV_API_CMD)

test: test-web test-api

test-web:
	$(TEST_WEB_CMD)

test-api:
	$(TEST_API_CMD)
