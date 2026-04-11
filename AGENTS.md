# AGENTS.md

## Overview

This repository contains a PDF-to-audio web application built by a solo developer. Users upload PDFs, the backend parses them into chapters, background workers generate chapter audio with Coqui TTS, and the frontend exposes authentication and upload flows.

This file is the primary agent-facing guide for the project.

- Implementation truth lives in the code and tests.
- Roadmap and delivery status live in `Plans.md`.
- `CLAUDE.md` is legacy reference material only. If it conflicts with the codebase or this file, prefer the codebase and this file.

## Current State

The backend foundation is substantially implemented:

- Email/password auth with session cookies
- PDF upload to MinIO
- Background PDF parsing with Celery + Redis
- Coqui TTS integration for chapter audio generation
- Chapter audio endpoint with presigned URLs
- File visibility controls
- Reading history API
- GitHub Actions CI

The frontend is only partially implemented:

- Login and registration flows exist
- Upload flow exists with progress feedback
- Dashboard and profile pages are still mostly placeholder UX
- Audio player UI is not implemented
- Library/history management UX is not implemented

## Repository Structure

```text
/
├── backend/   FastAPI app, services, models, worker tasks, tests
├── frontend/  SvelteKit app, routes, components, API client
├── infra/     Docker Compose stack
├── docs/      Additional project docs
├── AGENTS.md  Primary contributor and agent guidance
└── Plans.md   Current implementation status and roadmap
```

## Architecture

### Backend

- Framework: FastAPI
- Database: PostgreSQL
- ORM: SQLAlchemy async
- Background jobs: Celery with Redis
- Object storage: MinIO
- TTS engine: Coqui TTS over HTTP

Key backend areas:

- `backend/api/v1/endpoints/`: HTTP endpoints
- `backend/services/`: business logic
- `backend/models/`: ORM models
- `backend/worker/`: Celery app and tasks
- `backend/tests/`: backend and workflow tests

### Frontend

- Framework: SvelteKit
- Auth and API access are routed through central client code in `frontend/src/lib/api.ts`
- Current user-facing routes include home, auth, upload, dashboard, and profile

### Runtime Stack

`infra/docker-compose.yml` defines:

- `backend`
- `frontend`
- `postgres`
- `redis`
- `minio`
- `celery`
- `coqui-tts`

## Working Rules

### Source of truth

- Do not trust `CLAUDE.md` blindly. It still says Coqui TTS is not integrated, which is no longer true.
- When documenting or changing behavior, verify against current code and tests first.
- Use `Plans.md` to understand what is done, partial, or still missing from the original project plan.

### Backend conventions

- Keep router logic thin. HTTP concerns belong in endpoints; business logic belongs in `backend/services/`.
- Preserve authentication and authorization checks, especially file ownership and public/private visibility behavior.
- Continue using presigned MinIO URLs for audio delivery. Do not expose object storage credentials to the client.
- Prefer extending existing services instead of duplicating storage, parsing, or TTS logic.
- Be careful with status transitions on files and chapters; background processing depends on consistent state changes.

### Frontend conventions

- Use the shared API client in `frontend/src/lib/api.ts` for network calls.
- Match runtime schemas in `frontend/src/lib/schemas/api.ts` when adding new API integrations.
- Reuse existing auth and network stores instead of scattering duplicate state.
- Preserve the existing SvelteKit route structure unless there is a strong reason to reorganize it.

### Documentation conventions

- Keep docs aligned with the actual repo state, not with aspirational architecture.
- When changing delivery status, update `Plans.md`.
- When changing contributor workflow or architecture guidance, update `AGENTS.md`.

## Known Gaps And Hazards

- `CLAUDE.md` is stale in multiple places, especially around TTS integration and project status.
- The original PDR/dev plan includes `saved_files`, but there is no implemented `saved_files` model or feature in the current repo.
- Alembic is listed as a dependency, but the repo currently relies on startup-time schema logic in `backend/core/database.py` rather than a normal checked-in Alembic migration workflow.
- Health endpoints contain placeholder checks and metrics.
- Frontend product flows lag behind backend capabilities.

## Common Commands

Run commands from the repo root unless noted otherwise.

### Docker stack

```bash
cd infra
docker compose up --build
docker compose down
docker compose logs -f backend
docker compose logs -f celery
docker compose logs -f frontend
```

### Backend tests

```bash
cd infra
docker compose build backend
docker compose up -d --force-recreate backend
docker exec -it tts-backend python3 -m pytest -q
```

### Frontend checks

```bash
cd frontend
npm install
npm run check
npm run build
```

## Practical Guidance For Agents

- Before implementing a new feature, check whether the backend already supports it and the frontend simply has not wired it up.
- Before claiming something is missing, check git history and tests; several major features exist even where older docs still say otherwise.
- If adding a user-facing playback or dashboard feature, verify the existing endpoints first:
  - file list and detail endpoints
  - chapter audio endpoint
  - reading history endpoints
- If you change the project’s operating model, commands, or roadmap truth, update this file and `Plans.md` in the same change.
