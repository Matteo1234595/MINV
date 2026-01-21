# AION OS Monorepo

AION OS is a monorepo containing the web control plane, API service, shared
schemas, and infrastructure manifests.

## Structure

```
apps/
  api/        FastAPI service
  web/        Next.js (TypeScript, App Router) + Tailwind
infra/        Docker Compose infrastructure
packages/
  shared/     Shared JSON schemas
```

## Prerequisites

- Node.js 18+
- Python 3.11+
- Docker (for Postgres)

## Setup

### Web

```bash
cd apps/web
npm install
npm run dev
```

### API

```bash

```bash
cd apps/web
npm install
npm run dev
```

### API

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Migrations

```bash
export DATABASE_URL=postgresql+psycopg2://aion:aion@localhost:5432/aion
make db-migrate
make db-seed
```

### Infrastructure

```bash
docker compose -f infra/docker-compose.yml up -d
```

## Makefile shortcuts

```bash
make dev-web     # run the Next.js dev server
make dev-api     # run the FastAPI server
make test        # run API tests and web lint
```

## Environment Variables

- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` are configured in
  `infra/docker-compose.yml` for local development.
- `DATABASE_URL` configures the API database connection (defaults to local
  Postgres).
