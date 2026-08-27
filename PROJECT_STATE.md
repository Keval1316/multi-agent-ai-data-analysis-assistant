# PROJECT STATE

Last updated: 2026-08-27 11:20

## Current Phase
Phase 1: File upload and ingestion (Next)

## Completed Phases
- [x] Phase 0: Repository scaffolding
- [ ] Phase 1: File upload and ingestion
- [ ] Phase 2: Dataset profiling and quality checking
- [ ] Phase 3: LLM router and dataset understanding
- [ ] Phase 4: Statistical and SQL analysis
- [ ] Phase 5: Pattern detection and visualizations
- [ ] Phase 6: Insight generation and critic loop
- [ ] Phase 7: Report generation and PDF export
- [ ] Phase 8: Full LangGraph orchestration and SSE
- [ ] Phase 9: Complete frontend workflow
- [ ] Phase 10: End-to-end testing
- [ ] Phase 11: Deployment and documentation

## Key Decisions and Notes
- **Design Palette Tokens**: Implemented exact required design palette tokens in Tailwind & CSS variables:
  - Background: `#EDF1D6` (`--color-background`)
  - Surface: `#FFFFFF` (`--color-surface`)
  - Accent Surface: `#9DC08B` (`--color-surface-accent`)
  - Primary Text: `#40513B` (`--color-text-primary`)
  - Secondary Text: `#609966` (`--color-text-secondary`)
  - Primary / Button: `#609966` (`--color-primary`)
  - Primary Hover / Active: `#40513B` (`--color-primary-hover`)
  - Border: `#9DC08B` (`--color-border`)
- **Backend Architecture**: FastAPI with Pydantic v2 settings, modular routers, structured logging, centralized custom exceptions, and health endpoints.
- **Frontend Architecture**: React 18 + Vite 5 + Tailwind CSS 3 + Framer Motion. Production build verified.
- **Python Environment**: Configured Python 3.12 venv with LangGraph, DuckDB, pandas, numpy, scipy, statsmodels, plotly, jinja2, openpyxl, reportlab, httpx, pytest, groq, and google-genai.

## Known Issues / Limitations
- None in Phase 0 scaffolding.

## Environment Variables Required
- `APP_ENV`: Application environment (development/production) [Backend]
- `LOG_LEVEL`: Logging level (INFO/DEBUG) [Backend]
- `PORT`: Backend port (8000 default) [Backend]
- `CORS_ORIGINS`: Allowed origins list [Backend]
- `MAX_UPLOAD_SIZE_MB`: Max upload file size limit (10MB default) [Backend]
- `GROQ_API_KEY_1`, `GROQ_API_KEY_2`, `GROQ_MODEL`: Groq provider configuration [Backend]
- `GEMINI_API_KEY_1`, `GEMINI_API_KEY_2`, `GEMINI_MODEL`: Gemini provider configuration [Backend]
- `VITE_API_BASE_URL`: Base backend URL (http://localhost:8000) [Frontend]

## Test Status
- Backend health tests (`backend/tests/test_health.py`): 2 passed in 1.31s.
- Frontend build (`npm run build`): Clean production bundle compiled in 32s.

## Next Phase Plan
- **Phase 1: File Upload and Ingestion**
  - Implement file validation service (MIME/extension check, size limits, CSV/XLSX/XLS structure check, empty dataset rejection).
  - Implement dataset ingestion service with pandas encoding detection, safe sanitization, DuckDB in-memory database table registration.
  - Implement `/api/upload` endpoint returning dataset metadata (id, row count, column count, schema preview).
  - Add comprehensive unit tests for valid CSV, valid Excel, empty files, corrupt files, and oversized files.
  - Implement initial frontend drag-and-drop file upload component in React with validation feedback.
