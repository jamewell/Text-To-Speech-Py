# Lean TTS (PDF-to-Audio)  

**Open-source web app to convert PDFs into audiobooks using TTS.**  

## Features  
- PDF upload & chapter segmentation  
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
├── docs/        # Documentation  
