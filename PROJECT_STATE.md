# PROJECT STATE

Last updated: 2026-08-27 11:59

## Current Phase
Phase 6: Insight generation and critic loop (Next)

## Completed Phases
- [x] Phase 0: Repository scaffolding
- [x] Phase 1: File upload and ingestion
- [x] Phase 2: Dataset profiling and quality checking
- [x] Phase 3: LLM router and dataset understanding
- [x] Phase 4: Statistical and SQL analysis
- [x] Phase 5: Pattern detection and visualizations
- [ ] Phase 6: Insight generation and critic loop
- [ ] Phase 7: Report generation and PDF export
- [ ] Phase 8: Full LangGraph orchestration and SSE
- [ ] Phase 9: Complete frontend workflow
- [ ] Phase 10: End-to-end testing
- [ ] Phase 11: Deployment and documentation

## Key Decisions and Notes
- **Pattern & Anomaly Detection**:
  - `PatternDetector` executes deterministic linear regression trends (`slope`, `r_squared`, growth rates, p-values), Pareto concentration analysis (measuring category dominance), z-score / IQR multi-metric anomaly detection, and day-of-week seasonality cycles.
- **Interactive Visualization Engine**:
  - `ChartGenerator` produces rich, interactive Plotly JSON specs (bar, line, scatter, donut) styled with the exact requested color palette (`#EDF1D6`, `#40513B`, `#609966`, `#9DC08B`, `#FFFFFF`).
  - `ChartRenderer` provides responsive client-side rendering with tooltips and interactive hover states.

## Known Issues / Limitations
- None in Phase 5.

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
- Backend test suite (`backend/tests/`): 39 passed in 2.63s (`test_health.py`, `test_ingestion.py`, `test_profiling.py`, `test_quality.py`, `test_llm_router.py`, `test_agents.py`, `test_statistics.py`, `test_sql_safety.py`, `test_sql_execution.py`, `test_patterns.py`, `test_visualizations.py`).
- Frontend production bundle (`npm run build`): Clean build in 2.55s.

## Next Phase Plan
- **Phase 6: Insight Generation and Critic Loop**
  - Implement Insight Generation Agent (`backend/app/agents/generate_insights.py`):
    * Generates evidence-grounded findings referencing only computed statistics, SQL results, and patterns
    * Avoids causal claims without proof ("is associated with", "may indicate", "suggests")
    * Pydantic model `InsightCollection` (`InsightItem`: finding, supporting_evidence, importance, confidence, recommendation)
  - Implement Critic Review Agent (`backend/app/agents/critic_review.py`):
    * Audits generated insights against ground-truth statistical numbers and SQL tables
    * Detects hallucinated numbers, unsupported claims, overstated causation
    * Pydantic model `CriticReviewResult` (approved: bool, feedback, unsupported_claims, required_corrections)
  - Implement Insight Revision Loop (`backend/app/agents/revise_insights.py`):
    * Condition-based revision with a strict cap of maximum 2 revision loops
    * Preserves supported insights and attaches internal/user caveats if revision limit reached
  - Add comprehensive unit and mock tests for supported, unsupported, and revision loop handling.
