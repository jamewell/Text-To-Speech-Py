## [Unreleased]  
### Added  
- [2025-08-18] Initialized project structure (Task 1.1).  
- [2025-08-18] Added baseline `.gitignore`, `README.md`, `LICENSE`.
- chore: Project structure initialized
- build: `.gitignore` for Python/Node
- docs: README and CHANGELOG baseline
- build: Dockerfiles for FastAPI backend and SvelteKit frontend
- infra: docker-compose.yml with all core services
- build: Backend Python dependencies
- infra: add .env template for environment variables
- refactor: migrate hardcoded values to .env variables
- chore: exclude .env from version control


### Fixed
- fix(docker): resolve frontend build errors by initializing SvelteKit project structure
- fix(docker): correct Dockerfile paths and build context for frontend/backend