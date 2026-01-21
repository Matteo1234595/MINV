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
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Dashboard

Set the API URL and launch Next.js:

```bash
cd apps/web
export NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Open `http://localhost:3000/dashboard` and provide an organization UUID plus JWT token if needed.

### Migrations

```bash
export DATABASE_URL=postgresql+psycopg2://aion:aion@localhost:5432/aion
make db-migrate
make db-seed
```

### CSV Ingestion

CSV templates live in `packages/shared/samples`. Uploads expect ISO-8601 timestamps
for date fields.

```bash
curl -F "organization_id=<ORG_UUID>" -F "file=@packages/shared/samples/bank_transactions.csv" \\
  http://localhost:8000/uploads/bank-transactions

curl -F "organization_id=<ORG_UUID>" -F "file=@packages/shared/samples/invoices.csv" \\
  http://localhost:8000/uploads/invoices
```

### KPI Computation

Recompute monthly KPI snapshots for an organization:

```bash
curl -X POST http://localhost:8000/kpis/recompute \
  -H "Content-Type: application/json" \
  -d '{"organization_id":"<ORG_UUID>"}'
```

Fetch the latest KPI snapshot set:

```bash
curl "http://localhost:8000/kpis/latest?organization_id=<ORG_UUID>"
```

### Authentication

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"organization_id":"<ORG_UUID>","email":"user@example.com","password":"changeme"}'

curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"changeme"}'
```

### AION Copilot

```bash
curl -X POST http://localhost:8000/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"organization_id":"<ORG_UUID>","message":"Summarize our latest financial risks."}'
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
- `JWT_SECRET` configures the JWT signing secret for auth.
- `JWT_ISSUER` configures the JWT issuer (default: `aion`).
- `ACCESS_TTL_MIN` sets the access token TTL in minutes (default: `15`).
- `REFRESH_TTL_DAYS` sets the refresh token TTL in days (default: `30`).
- `OPENAI_API_KEY` configures the OpenAI API key for Copilot.
- `OPENAI_MODEL` sets the Copilot model (default: `gpt-4o-mini`).
- `OPENAI_BASE_URL` optionally overrides the OpenAI API base URL.
