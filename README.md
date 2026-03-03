# Lean TTS (PDF-to-Audio)

Open-source web app to convert PDFs into audiobooks using TTS.

## Features
- PDF upload and chapter segmentation
- Local Coqui TTS integration
- Dockerized deployment

## Current Priority
- As of 2026-03-01, background processing (Celery worker for PDF parsing and long-running jobs) is Phase 1 priority.
- This work was previously planned for a later phase and has been moved up to avoid upload-time timeouts and frontend errors.

## Project Structure
```plaintext
lean-tts/
├── frontend/    # SvelteKit app
├── backend/     # FastAPI
├── infra/       # Docker, MinIO configs
└── docs/        # Documentation
```

## Async Processing Stack (Task 4.1)
- `celery` service runs a worker from `worker.celery_app:celery_app`.
- `redis` service is configured as broker/result backend for Celery.
- Celery routing includes separate queues for PDF and TTS processing.

## Run With Docker
```bash
cd infra
docker compose up --build
```

## Run Backend Tests (Docker)
Run all commands from the `infra/` directory:

```bash
cd infra
docker compose build backend
docker compose up -d --force-recreate backend
docker exec -it tts-backend python3 -m pytest -q
```
