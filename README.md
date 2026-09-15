# Bastion

![CI](https://github.com/vikhayatrana0110-crypto/BASTION---Secure-AI-Assistant/actions/workflows/ci.yml/badge.svg)

A secure internal knowledge assistant. Employees ask questions about company documents and get cited answers, but only from documents their clearance level and department allow. Access rules are enforced by Postgres row-level security, not by the AI.

> **Status:** early development. The project skeleton, local database and CI are in place. Access control, retrieval and the chat interface are next.

## Planned features

- **Database-enforced access control** by clearance level and department (Postgres row-level security)
- **Hybrid retrieval**: vector search (pgvector) plus keyword search, fused and reranked
- **Guardrails**: PII redaction, prompt-injection scanning, citation and groundedness checks
- **Evaluation**: golden test sets and access-leak tests run in CI

## Tech stack

Python 3.12 · uv · FastAPI · Postgres 17 + pgvector · Docker · GitHub Actions

## Run it locally

Requirements: [uv](https://docs.astral.sh/uv/) and [Docker](https://www.docker.com/).

```bash
uv sync --extra web
docker compose up -d --wait
uv run uvicorn bastion.main:create_app --factory --reload
```

Then open http://127.0.0.1:8000/healthz or http://127.0.0.1:8000/docs.

## Tests

```bash
uv run pytest                        # all tests (needs the database running)
uv run pytest -m "not integration"   # fast tests only
uv run ruff check .                  # lint
```