## [Unreleased]  
### Added  
- [2025-08-18] Initialized project structure (Task 1.1).  
- [2025-08-18] Added baseline `.gitignore`, `README.md`, `LICENSE`.
- [2026-03-01] Re-prioritized roadmap: moved background worker/PDF parsing to Phase 1 priority (previously planned for Phase 4).
- [2026-03-03] Completed task 4.1 setup validation by adding backend tests for Celery app configuration and Docker Compose Celery/Redis wiring.
- [2026-03-03] Documented Celery worker + Redis broker runtime stack in the root `README.md`.
- [2026-03-03] Implemented task 4.2: upload endpoint now enqueues background PDF parsing (`worker.tasks.process_pdf`) instead of parsing inline.
- [2026-03-03] Implemented task 4.2 worker flow: fetch PDF from MinIO, parse/store chapters, and persist `files.status` transitions (`pending` -> `processing` -> `completed`/`failed`).
- [2026-03-03] Added tests for async PDF queueing and worker processing status updates.
- [2026-03-03] Implemented task 4.3: `process_pdf` now enqueues chapter-level `process_tts(file_id, chapter_id)` jobs after parsing.
- [2026-03-03] Implemented task 4.3: chapter audio artifacts are uploaded to MinIO (`completed-files`) and persisted on `chapters.audio_bucket_name`/`chapters.audio_object_name`.
- [2026-03-03] Implemented task 4.3 completion flow: file is marked `completed` only after all chapter TTS jobs finish; worker failures mark file `failed`.
- [2026-03-15] Implemented Task 1.3: GitHub Actions CI/CD pipeline with test, lint-backend (ruff), build-frontend, and lint-frontend jobs triggered on push/PR to main.
- [2026-03-15] Implemented Task 3.6: `GET /chapters/{chapter_id}/audio` endpoint returning a MinIO presigned URL (3600s TTL) with owner/public visibility access control.
- [2026-03-15] Added `FileVisibility` enum (private/public) to the `files` table; visibility is set at upload time and updatable via `PATCH /files/{id}/visibility`.
- [2026-03-15] Invalid visibility values at upload now return 400 instead of 500; `FileVisibilityUpdate` schema enforces allowed values on the PATCH endpoint.
- [2026-03-15] Mutating file operations (delete, visibility update) restricted to file owner; public files are readable but not mutable by non-owners.
- [2026-03-15] `GET /files/{id}` and `GET /files/list` now eager-load chapters so the chapter list is available to the frontend player without a second request.
- chore: Project structure initialized
- build: `.gitignore` for Python/Node
- docs: README and CHANGELOG baseline
- build: Dockerfiles for FastAPI backend and SvelteKit frontend
- infra: docker-compose.yml with all core services
- build: Backend Python dependencies
- infra: add .env template for environment variables
- refactor: migrate hardcoded values to .env variables
- chore: exclude .env from version control
- frontend: added home page and account, dashboard, and upload pages with placeholder content 


### Fixed
- fix(docker): resolve frontend build errors by initializing SvelteKit project structure
- fix(docker): correct Dockerfile paths and build context for frontend/backend
