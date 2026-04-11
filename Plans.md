# Plans.md

## Summary

This file tracks implementation status against the original project documents:

- PDR: `/home/jamewell/Documents/Lean PDR TTS Solo.pdf`
- Development plan: `/home/jamewell/Documents/Lean TTS Solo development plan.pdf`

Status values used here:

- `Done`
- `Partial`
- `Not Started`
- `Out of Scope / Future`

Assessment is based on the current repository state and git history through commit `fa2f733`.

## Status By Epic

### Epic 1: Project Setup & Environment

| Task | Status | Notes |
| --- | --- | --- |
| 1.1 Initialize Project Structure | Done | Monorepo layout, README, license, backend/frontend/infra structure are present. |
| 1.2 Docker Compose Setup | Done | Compose stack and Dockerfiles exist for backend/frontend plus supporting services. |
| 1.3 Basic CI/CD Pipeline | Done | GitHub Actions workflow exists for tests, linting, and frontend build checks. |

### Epic 2: Frontend (SvelteKit)

| Task | Status | Notes |
| --- | --- | --- |
| 2.1 SvelteKit Project Setup | Done | SvelteKit app, routing, layout, and styling foundation exist. |
| 2.2 Authentication UI | Done | Login/register flows, validation, auth store, and route handling are implemented. |
| 2.3 File Upload UI | Done | Upload page supports PDF selection, drag-and-drop, validation, retries, and progress. |
| 2.4 Audio Player UI | Not Started | No real player UI, playback controls, or chapter navigation UI exists yet. |
| 2.5 Dashboard UI | Partial | Dashboard/profile routes exist, but they are mostly placeholder UX and are not wired to the backend file/history capabilities. |

### Epic 3: Backend (FastAPI)

| Task | Status | Notes |
| --- | --- | --- |
| 3.1 Backend Project Setup | Done | FastAPI app structure, health endpoints, and configuration are present. |
| 3.2 Authentication | Done | Registration, login, logout, password hashing, and session cookies are implemented. |
| 3.3 File Upload API | Done | PDF upload API stores files, saves metadata, and queues background processing. |
| 3.4 PDF Parsing Service | Done | PDF parsing service exists and stores chapter data. |
| 3.5 TTS Integration | Done | Coqui TTS integration exists and worker tasks generate/upload audio artifacts. |
| 3.6 File & Chapter APIs | Done | File listing/detail, visibility updates, delete flow, and chapter audio endpoint are implemented. |
| 3.7 Reading History API | Done | History upsert and paginated history listing are implemented with validation. |

### Epic 4: Async Processing (Celery + Redis)

| Task | Status | Notes |
| --- | --- | --- |
| 4.1 Setup Celery Workers | Done | Celery worker and Redis broker are configured and tested. |
| 4.2 Background Job: PDF Processing | Done | Uploads enqueue PDF parsing; worker fetches from MinIO, parses, and updates status. |
| 4.3 Background Job: TTS Conversion | Done | Chapter-level TTS jobs are enqueued, upload audio to MinIO, and complete file status flow. |

### Epic 5: Database (PostgreSQL)

| Task | Status | Notes |
| --- | --- | --- |
| 5.1 Define Schema | Partial | `users`, `files`, `chapters`, and `reading_history` exist, but planned `saved_files` is missing. |
| 5.2 Migration Setup | Partial | Alembic is listed as a dependency, but the repo uses startup-time schema logic instead of a normal checked-in Alembic migration workflow. |

### Epic 6: Storage (MinIO)

| Task | Status | Notes |
| --- | --- | --- |
| 6.1 MinIO Setup | Done | MinIO is part of the Docker Compose stack with persistent volume configuration. |
| 6.2 MinIO Integration | Done | Backend stores PDFs and chapter audio in MinIO and uses presigned URLs for audio access. |

### Epic 7: Testing

| Task | Status | Notes |
| --- | --- | --- |
| 7.1 Backend Unit Tests | Done | Backend test coverage exists for upload, parsing, TTS, chapter audio, Celery setup, and history. |
| 7.2 Integration Tests | Partial | Backend workflow tests exist, but full end-to-end production-style pipeline coverage is still limited. |
| 7.3 Frontend Tests | Not Started | No frontend component or user-flow test suite is present. |

### Epic 8: Deployment

| Task | Status | Notes |
| --- | --- | --- |
| 8.1 VPS Setup | Not Started | No VPS provisioning or runbook exists in the repo. |
| 8.2 Deploy Application | Not Started | Compose-based runtime exists locally, but deployment instructions/work are not implemented. |
| 8.3 Domain & SSL | Not Started | No reverse proxy, domain, or TLS configuration exists. |

### Epic 9: Future Enhancements

| Task | Status | Notes |
| --- | --- | --- |
| OpenAI TTS integration | Out of Scope / Future | Mentioned in the PDR as a future option only. |
| Social login | Out of Scope / Future | Not started and not part of MVP. |
| Advanced search | Out of Scope / Future | Not started and not part of MVP. |
| Offline support | Out of Scope / Future | Not started and not part of MVP. |

## What Is Actually Delivered

The project already has more backend functionality than some older docs suggest.

Delivered in code and/or tests:

- Auth and session handling
- Upload API and upload UI
- PDF parsing and chapter persistence
- Async worker flow for parsing and TTS
- Coqui TTS integration
- Chapter audio delivery via presigned URL
- Public/private file visibility handling
- Reading history APIs
- CI pipeline

Still materially incomplete:

- Audio player UI
- Dashboard/library UX wired to backend data
- Saved-files feature from the original plan
- Proper migration discipline with checked-in Alembic workflow
- Frontend tests
- Deployment readiness and operations docs

## Next Implementation Priorities

1. Build the audio player UI with play/pause/skip, progress, and chapter navigation, then connect it to the chapter audio endpoint and reading history API.
2. Replace dashboard/profile placeholder content with real file-library, processing-status, visibility, and history views.
3. Decide whether `saved_files` remains in scope; if yes, implement it, and in either case move schema management to real Alembic migrations.
4. Add frontend test coverage for auth, upload, and playback flows.
5. Add deployment readiness work: VPS setup guidance, persistent volumes, reverse proxy, domain, and TLS.

## Assumptions

- The authoritative planning sources are the two PDFs in `/home/jamewell/Documents`.
- Git history is used to distinguish completed work from stale documentation.
- This file should be updated whenever major plan items move from `Partial` or `Not Started` to `Done`.
