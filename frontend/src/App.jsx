import React, { useState, useEffect } from 'react';
import { Sparkles, ShieldCheck, Database, Cpu, RefreshCw } from 'lucide-react';
import FileUpload from './components/FileUpload';
import DatasetProfileView from './components/DatasetProfileView';

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

          <div className="flex items-center space-x-3">
            {activeDataset && (
              <button
                onClick={() => setActiveDataset(null)}
                className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-surface border border-border text-text-secondary hover:text-text-primary hover:bg-surface-accent/20 transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Upload New File</span>
              </button>
            )}

            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-surface border border-border text-text-secondary">
              <span className={`w-2 h-2 rounded-full mr-2 ${health?.status === 'healthy' ? 'bg-primary animate-pulse' : 'bg-red-500'}`} />
              {loading ? 'Checking Engine...' : health?.status === 'healthy' ? 'Engine Ready' : 'Backend Offline'}
            </span>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-6 py-10 flex-1 w-full space-y-10">
        {!activeDataset ? (
          <>
            {/* Hero Section */}
            <div className="text-center max-w-3xl mx-auto">
              <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-surface border border-border text-xs font-semibold text-text-secondary mb-4 shadow-sm">
                <Cpu className="w-4 h-4 text-primary" />
                <span>Phase 2 • Automated Profiling & Quality Audit</span>
              </div>
              <h2 className="text-4xl font-extrabold tracking-tight text-text-primary mb-4 sm:text-5xl">
                Analyze Complex Data with Multi-Agent Precision
              </h2>
              <p className="text-base sm:text-lg text-text-secondary leading-relaxed max-w-2xl mx-auto">
                Upload any messy CSV or Excel dataset. Our deterministic engine profiles structure, audits quality, and detects statistical anomalies in real-time.
              </p>
            </div>

            {/* Upload Component */}
            <FileUpload onDatasetIngested={(metadata) => setActiveDataset(metadata)} />

            {/* Feature Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4">
              <div className="p-6 rounded-3xl bg-surface border border-border shadow-sm">
                <div className="w-12 h-12 rounded-2xl bg-surface-accent/30 border border-border flex items-center justify-center mb-4">
                  <Database className="w-6 h-6 text-primary" />
                </div>
                <h3 className="text-base font-bold text-text-primary mb-2">Deterministic Profiling</h3>
                <p className="text-xs text-text-secondary leading-relaxed">
                  Computes quantiles, IQR, variance, categorical frequencies, and primary key candidates without hallucinating numbers.
                </p>
              </div>

              <div className="p-6 rounded-3xl bg-surface border border-border shadow-sm">
                <div className="w-12 h-12 rounded-2xl bg-surface-accent/30 border border-border flex items-center justify-center mb-4">
                  <ShieldCheck className="w-6 h-6 text-primary" />
                </div>
                <h3 className="text-base font-bold text-text-primary mb-2">Comprehensive Quality Audit</h3>
                <p className="text-xs text-text-secondary leading-relaxed">
                  Detects duplicates, statistical outliers, inconsistent category labels, negative anomalies, and scores datasets on a 0-100 scale.
                </p>
              </div>

              <div className="p-6 rounded-3xl bg-surface border border-border shadow-sm">
                <div className="w-12 h-12 rounded-2xl bg-surface-accent/30 border border-border flex items-center justify-center mb-4">
                  <Sparkles className="w-6 h-6 text-primary" />
                </div>
                <h3 className="text-base font-bold text-text-primary mb-2">Multi-Agent Ready</h3>
                <p className="text-xs text-text-secondary leading-relaxed">
                  Generates compact, safe statistical representations to ground downstream LLM agents with zero data leak risks.
                </p>
              </div>
            </div>
          </>
        ) : (
          <div className="space-y-8">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-text-primary tracking-tight">
                  Dataset Structure & Quality Inspection
                </h2>
                <p className="text-xs text-text-secondary mt-0.5">
                  Inspecting active table <span className="font-mono font-semibold">{activeDataset.table_name}</span> ({activeDataset.filename})
                </p>
              </div>
            </div>

            <DatasetProfileView
              datasetId={activeDataset.dataset_id}
              onProceedToAnalysis={() => {
                alert(`Proceeding to multi-agent analysis for dataset ${activeDataset.dataset_id}`);
              }}
            />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-border bg-surface/50 py-6">
        <div className="max-w-7xl mx-auto px-6 text-center text-xs text-text-secondary">
          Multi-Agent Data Analyst • Phase 2 Dataset Profiling & Quality Engine
        </div>
      </footer>
    </div>
  );
}
