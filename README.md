# Multi-Agent Data Analyst

AI-Powered CSV/Excel Insight & Report Generator built with LangGraph, DuckDB, FastAPI, React, and Tailwind CSS.

## Architecture

- **Backend**: FastAPI, LangGraph multi-agent pipeline, DuckDB SQL execution, pandas/numpy/scipy/statsmodels statistical analysis, Jinja2 & ReportLab report & PDF generation.
- **Frontend**: Vite + React, Tailwind CSS with custom design tokens, Framer Motion animations, Plotly.js charts, Server-Sent Events (SSE) for real-time progress.
- **LLM Abstraction**: Multi-provider router supporting Groq & Google Gemini with failover, retries, and Pydantic structured output validation.

## Design Palette Tokens

- **Background**: `#EDF1D6`
- **Cards / Panels**: `#FFFFFF`
- **Secondary Card / Accent**: `#9DC08B`
- **Primary Text**: `#40513B`
- **Secondary Text**: `#609966`
- **Primary Button**: `#609966`
- **Primary Button Hover**: `#40513B`
- **Borders**: `#9DC08B`
- **Icons**: `#609966`

## Quickstart

### Backend Setup

```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```
