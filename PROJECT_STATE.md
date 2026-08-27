# PROJECT STATE

Last updated: 2026-08-27 11:45

## Current Phase
Phase 4: Statistical and SQL analysis (Next)

## Completed Phases
- [x] Phase 0: Repository scaffolding
- [x] Phase 1: File upload and ingestion
- [x] Phase 2: Dataset profiling and quality checking
- [x] Phase 3: LLM router and dataset understanding
- [ ] Phase 4: Statistical and SQL analysis
- [ ] Phase 5: Pattern detection and visualizations
- [ ] Phase 6: Insight generation and critic loop
- [ ] Phase 7: Report generation and PDF export
- [ ] Phase 8: Full LangGraph orchestration and SSE
- [ ] Phase 9: Complete frontend workflow
- [ ] Phase 10: End-to-end testing
- [ ] Phase 11: Deployment and documentation

## Key Decisions and Notes
- **Resilient Multi-Provider LLM Abstraction**:
  - Abstract base `LLMProvider` implemented by `GroqProvider` (`groq`), `GeminiProvider` (`google-genai`), and `MockLLMProvider`.
  - Central `LLMRouter` maintains credential pools (`GROQ_API_KEY_1..3`, `GEMINI_API_KEY_1..2`), tracks health/cooldowns (60s on 429/quota error), automatically fails over across providers, and enforces Pydantic structured output validation.
  - `DataPrivacyFilter` automatically detects and redacts emails, phone numbers, SSNs, credit card numbers, and secret tokens before prompts leave the system.
- **Dataset Understanding & Analysis Planning**:
  - `DatasetUnderstandingAgent` takes compact structural summaries and quality scores to infer business domain, target entity, candidate KPIs, and strategic questions.
  - `AnalysisPlanningAgent` builds executable analysis plans with strict post-validation against real existing dataset columns, dropping or replacing any hallucinated column names.

## Known Issues / Limitations
- None in Phase 3.

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
- Backend test suite (`backend/tests/`): 26 passed in 5.85s (`test_health.py`, `test_ingestion.py`, `test_profiling.py`, `test_quality.py`, `test_llm_router.py`, `test_agents.py`).
- Frontend production bundle (`npm run build`): Clean build in 9.07s.

## Next Phase Plan
- **Phase 4: Statistical and SQL Analysis**
  - Implement deterministic statistical analysis engine (`backend/app/services/statistics/engine.py`):
    * Group-by aggregations (sum, mean, median, min, max, count)
    * Growth rates, distributions, and quantiles
    * Correlation matrix computation (Pearson / Spearman)
    * Hypothesis tests / ANOVA or Chi-Square where statistically appropriate
  - Implement SQL Generation Agent (`backend/app/agents/generate_sql.py`):
    * Generates safe DuckDB SQL queries based on validated Analysis Plan
  - Implement SQL Safety Validator (`backend/app/services/sql/validator.py`):
    * Validates read-only AST / syntax (permits SELECT, WITH/CTE)
    * Strictly rejects mutating or dangerous keywords: `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `COPY`, `ATTACH`, `DETACH`, `INSTALL`, `LOAD`, `PRAGMA`, `IMPORT`, `EXPORT`
    * Verifies referenced table and column names
  - Implement SQL Execution Service (`backend/app/services/sql/executor.py`):
    * Executes queries safely against DuckDB in-memory tables and formats structured result tables
  - Add comprehensive unit tests for safe SQL execution and rejecting dangerous SQL injections.
