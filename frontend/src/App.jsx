import React, { useState, useEffect } from 'react';
import { Activity, Sparkles, CheckCircle2, Database, ShieldCheck, Cpu } from 'lucide-react';

export default function App() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  useEffect(() => {
    fetch(`${apiBaseUrl}/api/health`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP error ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setHealth(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [apiBaseUrl]);

  return (
    <div className="min-h-screen bg-background text-text-primary flex flex-col justify-between selection:bg-surface-accent selection:text-text-primary">
      {/* Header */}
      <header className="border-b border-border bg-surface/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-surface-accent/30 border border-border flex items-center justify-center text-primary shadow-sm">
              <Sparkles className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h1 className="font-bold text-lg leading-tight tracking-tight text-text-primary">
                Multi-Agent Data Analyst
              </h1>
              <p className="text-xs text-text-secondary font-medium">
                AI-Powered CSV/Excel Intelligence & Reporting
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-surface border border-border text-text-secondary">
              <span className={`w-2 h-2 rounded-full mr-2 ${health?.status === 'healthy' ? 'bg-primary animate-pulse' : 'bg-red-500'}`} />
              {loading ? 'Checking Backend...' : health?.status === 'healthy' ? 'System Operational' : 'Backend Offline'}
            </span>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-6 py-12 flex-1 w-full">
        {/* Hero Section */}
        <div className="text-center max-w-3xl mx-auto mb-12">
          <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-surface border border-border text-xs font-semibold text-text-secondary mb-4 shadow-sm">
            <Cpu className="w-4 h-4 text-primary" />
            <span>Phase 0 • Foundation & Scaffolding</span>
          </div>
          <h2 className="text-4xl font-extrabold tracking-tight text-text-primary mb-4 sm:text-5xl">
            Autonomous Multi-Agent Intelligence for Complex Datasets
          </h2>
          <p className="text-lg text-text-secondary leading-relaxed">
            Deterministic data engineering combined with self-correcting multi-agent reasoning. Transform raw spreadsheets into actionable intelligence and executive-ready reports.
          </p>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="p-6 rounded-2xl bg-surface border border-border shadow-sm hover:shadow-md transition-shadow">
            <div className="w-12 h-12 rounded-xl bg-surface-accent/30 border border-border flex items-center justify-center mb-4">
              <Database className="w-6 h-6 text-primary" />
            </div>
            <h3 className="text-lg font-bold text-text-primary mb-2">Deterministic Core</h3>
            <p className="text-sm text-text-secondary leading-relaxed">
              Powered by DuckDB, pandas, numpy, and statsmodels. No hallucinations in statistics, distributions, or calculations.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-surface border border-border shadow-sm hover:shadow-md transition-shadow">
            <div className="w-12 h-12 rounded-xl bg-surface-accent/30 border border-border flex items-center justify-center mb-4">
              <ShieldCheck className="w-6 h-6 text-primary" />
            </div>
            <h3 className="text-lg font-bold text-text-primary mb-2">Self-Correcting Critic</h3>
            <p className="text-sm text-text-secondary leading-relaxed">
              Every insight is rigorously audited by a Critic agent against real evidence tables before inclusion in the final report.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-surface border border-border shadow-sm hover:shadow-md transition-shadow">
            <div className="w-12 h-12 rounded-xl bg-surface-accent/30 border border-border flex items-center justify-center mb-4">
              <Activity className="w-6 h-6 text-primary" />
            </div>
            <h3 className="text-lg font-bold text-text-primary mb-2">Real-Time SSE Stream</h3>
            <p className="text-sm text-text-secondary leading-relaxed">
              Watch the multi-agent pipeline execute live across ingestion, SQL validation, pattern detection, and report authoring.
            </p>
          </div>
        </div>

        {/* System Diagnostics / Backend Card */}
        <div className="max-w-xl mx-auto rounded-2xl bg-surface border border-border p-6 shadow-sm">
          <div className="flex items-center justify-between pb-4 mb-4 border-b border-border">
            <h4 className="text-base font-bold text-text-primary flex items-center gap-2">
              <Activity className="w-4 h-4 text-primary" />
              API Connectivity Status
            </h4>
            <span className="text-xs font-mono text-text-secondary">{apiBaseUrl}</span>
          </div>

          {loading ? (
            <div className="py-6 flex items-center justify-center text-text-secondary text-sm">
              <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin mr-3"></div>
              Checking backend connection...
            </div>
          ) : error ? (
            <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm">
              <p className="font-semibold">Backend Unreachable</p>
              <p className="text-xs mt-1 text-red-600">Ensure the FastAPI server is running on port 8000 ({error}).</p>
            </div>
          ) : (
            <div className="space-y-3 text-sm">
              <div className="flex justify-between items-center py-1">
                <span className="text-text-secondary">App Name:</span>
                <span className="font-medium text-text-primary">{health?.app_name}</span>
              </div>
              <div className="flex justify-between items-center py-1">
                <span className="text-text-secondary">API Version:</span>
                <span className="font-mono text-xs px-2 py-0.5 rounded bg-surface-accent/30 text-text-primary border border-border">{health?.version}</span>
              </div>
              <div className="flex justify-between items-center py-1">
                <span className="text-text-secondary">Environment:</span>
                <span className="font-medium text-text-primary capitalize">{health?.environment}</span>
              </div>
              <div className="flex justify-between items-center py-1">
                <span className="text-text-secondary">Status:</span>
                <span className="inline-flex items-center text-primary font-semibold">
                  <CheckCircle2 className="w-4 h-4 mr-1 text-primary" />
                  {health?.status}
                </span>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border bg-surface/50 py-6">
        <div className="max-w-7xl mx-auto px-6 text-center text-xs text-text-secondary">
          Multi-Agent Data Analyst • Phase 0 Scaffolding Ready
        </div>
      </footer>
    </div>
  );
}
