.PHONY: dev dev-web dev-api test test-web test-api db-migrate db-seed

DEV_WEB_CMD = npm --prefix apps/web run dev
DEV_API_CMD = uvicorn app.main:app --reload --app-dir apps/api

TEST_WEB_CMD = npm --prefix apps/web run lint
TEST_API_CMD = python -m pytest apps/api

DB_MIGRATE_CMD = alembic -c apps/api/alembic.ini upgrade head
DB_SEED_CMD = python apps/api/scripts/seed_demo.py

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

db-migrate:
	$(DB_MIGRATE_CMD)

db-seed:
	$(DB_SEED_CMD)
