# PROJECT STATE

Last updated: 2026-08-27 11:27

## Current Phase
Phase 2: Dataset profiling and quality checking (Next)

## Completed Phases
- [x] Phase 0: Repository scaffolding
- [x] Phase 1: File upload and ingestion
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
- **File Validation & Ingestion**:
  - `FileValidator` enforces extension checks (`.csv`, `.xlsx`, `.xls`), non-empty payloads, and maximum file size (`MAX_UPLOAD_SIZE_MB`).
  - `DatasetLoader` implements multi-encoding fallback (`utf-8`, `utf-8-sig`, `latin-1`, `cp1252`, `iso-8859-1`) and dynamic delimiter detection (`,`, `;`, `\t`, `|`).
  - SQL column sanitization ensures safe, unique DuckDB identifiers (`clean_name`) while preserving original header labels in `ColumnSchema` metadata.
  - In-memory `DuckDBManager` registers pandas DataFrames as isolated tables (`dataset_<uuid>`) and provides fast preview generation.
- **Frontend FileUpload Component**:
  - Implemented interactive drag-and-drop zone using Framer Motion.
  - Client-side size & extension validation with instant feedback.
  - Displays detected schema badges, null counts, and interactive preview table of first 5 rows.
- **Synthetic Datasets**:
  - Created `samples/clean_dataset.csv`, `samples/clean_dataset.xlsx`, and `samples/messy_dataset.csv` (with missing values, duplicates, outliers, mixed types, inconsistent categories).

## Known Issues / Limitations
- In-memory DuckDB tables are ephemeral and tied to the active server process.

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
- Backend test suite (`backend/tests/`): 14 passed in 3.71s (`test_health.py` and `test_ingestion.py`).
- Frontend production bundle (`npm run build`): Clean build in 13.7s.

## Next Phase Plan
- **Phase 2: Dataset Profiling and Quality Checking**
  - Implement deterministic profiler (`backend/app/services/profiling/profiler.py`):
    * Row count, column count, data types, null counts and null percentages.
    * Duplicate row counts and percentages.
    * Cardinality, unique value counts, top frequent values for categorical columns.
    * Statistical summaries (min, max, mean, median, std, quantiles) for numerical columns.
    * Identifier / primary key candidate detection.
  - Implement deterministic data quality checker (`backend/app/services/quality/checker.py`):
    * Missing value severity assessment.
    * Duplicate row detection.
    * Type mismatch & mixed type heuristics.
    * Numerical outlier detection using IQR and Z-scores.
    * Inconsistent categorical labels detection (case variations, extra spaces, abbreviations).
    * Quality classification: Confirmed issue, Suspicious issue, Informational observation.
    * Overall data quality score (0 - 100%).
  - Create Pydantic models for profile and quality report (`backend/app/models/profile.py`, `quality.py`).
  - Implement API endpoint (`POST /api/profile/{dataset_id}` and `POST /api/quality/{dataset_id}`).
  - Add comprehensive unit tests on both `clean_dataset.csv` and `messy_dataset.csv`.
