# PROJECT STATE

Last updated: 2026-08-27 11:41

## Current Phase
Phase 3: LLM router and dataset understanding (Next)

## Completed Phases
- [x] Phase 0: Repository scaffolding
- [x] Phase 1: File upload and ingestion
- [x] Phase 2: Dataset profiling and quality checking
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
- **Deterministic Profiling & Quality Engine**:
  - `DatasetProfiler` computes distributions, semantic types (`numeric`, `categorical`, `datetime`, `boolean`, `identifier`), moments (mean, std, skewness), quantiles (Q1, median, Q3, IQR), and frequency distributions deterministically without LLM calls.
  - `QualityChecker` audits completeness, uniqueness, and consistency, classifying findings into `confirmed_issue` (deduplication needed, empty columns, negative domain values), `suspicious_issue` (extreme outliers >3.0*IQR, inconsistent categorical casing/abbreviations), and `informational` (mild IQR tail values, high cardinality identifiers).
  - Overall quality score calculated on a 0-100 scale with Grade assigned (A: >=90, B: 80-89, C: 70-79, D: 60-69, F: <60).
- **Frontend Quality Inspection**:
  - `DatasetProfileView` displays score gauge, severity counters, issue remedies, column schemas, and interactive frequency distributions.

## Known Issues / Limitations
- None in Phase 2.

## Environment Variables Required
- `APP_ENV`: Application environment (development/production) [Backend]
- `LOG_LEVEL`: Logging level (INFO/DEBUG) [Backend]
- `PORT`: Backend port (8000 default) [Backend]
- `CORS_ORIGINS`: Allowed origins list [Backend]
- `MAX_UPLOAD_SIZE_MB`: Max upload file size limit (10MB default) [Backend]
- `MAX_DATASET_ROWS`: Max rows per dataset (500,000 default) [Backend]
- `MAX_DATASET_COLUMNS`: Max columns per dataset (500 default) [Backend]
- `GROQ_API_KEY_1`, `GROQ_API_KEY_2`, `GROQ_MODEL`: Groq provider configuration [Backend]
- `GEMINI_API_KEY_1`, `GEMINI_API_KEY_2`, `GEMINI_MODEL`: Gemini provider configuration [Backend]
- `VITE_API_BASE_URL`: Base backend URL (http://localhost:8000) [Frontend]

## Test Status
- Backend test suite (`backend/tests/`): 19 passed in 4.41s (`test_health.py`, `test_ingestion.py`, `test_profiling.py`, `test_quality.py`).
- Frontend production bundle (`npm run build`): Clean build in 11.45s.

## Next Phase Plan
- **Phase 3: LLM Router and Dataset Understanding**
  - Implement resilient LLM provider abstraction (`backend/app/llm/`):
    * Provider interface, Groq provider (`groq`), Gemini provider (`google-genai`), Mock provider for isolated testing.
    * Multi-credential configuration and round-robin/least-loaded selection.
    * Health tracking, rate-limit cooldown, retries, and automatic failover.
    * Structured output validation against Pydantic models with one correction retry.
  - Implement Dataset Understanding Agent (`backend/app/agents/understand_dataset.py`):
    * Ingests compact profile and quality metadata (never full raw dataset).
    * Infers dataset domain, business context, key candidate KPIs, potential relationships, and primary analytical questions.
  - Implement Analysis Planning Agent (`backend/app/agents/plan_analysis.py`):
    * Formulates structured analysis plan referencing strictly validated columns.
  - Comprehensive unit and mock tests for provider failover, rate limits, invalid JSON recovery, and agent outputs.
