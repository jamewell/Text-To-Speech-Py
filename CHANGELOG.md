## [Unreleased]  
### Added  
- [2025-08-18] Initialized project structure (Task 1.1).  
- [2025-08-18] Added baseline `.gitignore`, `README.md`, `LICENSE`.
- [2026-03-01] Re-prioritized roadmap: moved background worker/PDF parsing to Phase 1 priority (previously planned for Phase 4).
- [2026-03-03] Completed task 4.1 setup validation by adding backend tests for Celery app configuration and Docker Compose Celery/Redis wiring.
- [2026-03-03] Documented Celery worker + Redis broker runtime stack in the root `README.md`.
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
