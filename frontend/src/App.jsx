import React, { useState, useEffect } from 'react';
import { Sparkles, Activity, ShieldCheck, Database, Cpu } from 'lucide-react';
import FileUpload from './components/FileUpload';

export default function App() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeDataset, setActiveDataset] = useState(null);

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
      .catch(() => {
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
              {loading ? 'Checking Engine...' : health?.status === 'healthy' ? 'Engine Ready' : 'Backend Offline'}
            </span>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-6 py-12 flex-1 w-full space-y-12">
        {/* Hero Section */}
        <div className="text-center max-w-3xl mx-auto">
          <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-surface border border-border text-xs font-semibold text-text-secondary mb-4 shadow-sm">
            <Cpu className="w-4 h-4 text-primary" />
            <span>Multi-Agent Ingestion Engine</span>
          </div>
          <h2 className="text-4xl font-extrabold tracking-tight text-text-primary mb-4 sm:text-5xl">
            Analyze Complex Data with Multi-Agent Precision
          </h2>
          <p className="text-base sm:text-lg text-text-secondary leading-relaxed max-w-2xl mx-auto">
            Upload any messy CSV or Excel dataset. Our deterministic engine validates structure and loads it into DuckDB before orchestrating multi-agent insights.
          </p>
        </div>

        {/* Upload Component */}
        <FileUpload onDatasetIngested={(metadata) => setActiveDataset(metadata)} />

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-6">
          <div className="p-6 rounded-3xl bg-surface border border-border shadow-sm">
            <div className="w-12 h-12 rounded-2xl bg-surface-accent/30 border border-border flex items-center justify-center mb-4">
              <Database className="w-6 h-6 text-primary" />
            </div>
            <h3 className="text-base font-bold text-text-primary mb-2">Deterministic DuckDB Ingestion</h3>
            <p className="text-xs text-text-secondary leading-relaxed">
              Auto-detects CSV encodings (UTF-8, Latin-1, CP1252), delimiters, and parses Excel spreadsheets directly into memory without hallucination.
            </p>
          </div>

          <div className="p-6 rounded-3xl bg-surface border border-border shadow-sm">
            <div className="w-12 h-12 rounded-2xl bg-surface-accent/30 border border-border flex items-center justify-center mb-4">
              <ShieldCheck className="w-6 h-6 text-primary" />
            </div>
            <h3 className="text-base font-bold text-text-primary mb-2">Data Privacy & Security</h3>
            <p className="text-xs text-text-secondary leading-relaxed">
              Enforces strict size, row, and column limits. Sanitizes SQL column names and prevents formula or script injection.
            </p>
          </div>

          <div className="p-6 rounded-3xl bg-surface border border-border shadow-sm">
            <div className="w-12 h-12 rounded-2xl bg-surface-accent/30 border border-border flex items-center justify-center mb-4">
              <Activity className="w-6 h-6 text-primary" />
            </div>
            <h3 className="text-base font-bold text-text-primary mb-2">Multi-Agent Pipeline</h3>
            <p className="text-xs text-text-secondary leading-relaxed">
              Profiles dataset quality, formulates statistical tests, executes analytical SQL, and validates insights through a Critic loop.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border bg-surface/50 py-6">
        <div className="max-w-7xl mx-auto px-6 text-center text-xs text-text-secondary">
          Multi-Agent Data Analyst • Phase 1 Ingestion Pipeline
        </div>
      </footer>
    </div>
  );
}
