import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckCircle2,
  Loader2,
  Circle,
  Sparkles,
  Bot,
  Layers,
  Database,
  BarChart3,
  Lightbulb,
  FileCheck,
  ShieldAlert,
  FileText
} from 'lucide-react';

const PIPELINE_STEPS = [
  { id: 'validate_file', index: 1, label: 'Validating File Structure', agent: 'FileValidator', icon: FileCheck },
  { id: 'load_dataset', index: 2, label: 'Ingesting & Sanitizing Table', agent: 'DatasetLoader', icon: Database },
  { id: 'profile_and_audit', index: 3, label: 'Profiling Schema & Quality Audit', agent: 'QualityChecker', icon: ShieldAlert },
  { id: 'understand_dataset', index: 4, label: 'Synthesizing Domain & Key KPIs', agent: 'DatasetUnderstandingAgent', icon: Bot },
  { id: 'plan_analysis', index: 5, label: 'Formulating Analysis Plan', agent: 'AnalysisPlanningAgent', icon: Layers },
  { id: 'run_statistical_analysis', index: 6, label: 'Computing Distributions & Correlations', agent: 'StatisticalEngine', icon: BarChart3 },
  { id: 'generate_sql', index: 7, label: 'Synthesizing Analytical DuckDB SQL', agent: 'SQLGenerationAgent', icon: Bot },
  { id: 'validate_sql', index: 8, label: 'Verifying SQL Syntax & Security', agent: 'SQLValidator', icon: ShieldAlert },
  { id: 'execute_sql', index: 9, label: 'Executing In-Memory DuckDB Queries', agent: 'SQLExecutor', icon: Database },
  { id: 'detect_patterns', index: 10, label: 'Discovering Trends, Pareto & Anomalies', agent: 'PatternDetector', icon: BarChart3 },
  { id: 'select_visualizations', index: 11, label: 'Selecting Optimal Chart Types', agent: 'ChartGenerator', icon: BarChart3 },
  { id: 'render_charts', index: 12, label: 'Compiling Interactive Plotly Visuals', agent: 'ChartGenerator', icon: BarChart3 },
  { id: 'generate_insights', index: 13, label: 'Deriving Evidence-Grounded Insights', agent: 'InsightGenerationAgent', icon: Lightbulb },
  { id: 'critic_review', index: 14, label: 'Adversarial Fact-Checking & Auditing', agent: 'CriticReviewAgent', icon: ShieldAlert },
  { id: 'revise_insights', index: 15, label: 'Refining Findings & Capping Revisions', agent: 'InsightRevisionOrchestrator', icon: Bot },
  { id: 'generate_report', index: 16, label: 'Compiling Executive Markdown Report', agent: 'ReportGenerationAgent', icon: FileText },
  { id: 'render_pdf', index: 17, label: 'Rendering Publication-Grade PDF', agent: 'PDFExporter', icon: FileText },
];

export default function PipelineTracker({ currentStep, completedSteps = [], livePreviews = {}, filename = 'dataset.csv' }) {
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTimer = (sec) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const progressPct = Math.round((completedSteps.length / PIPELINE_STEPS.length) * 100);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      className="p-6 md:p-8 rounded-3xl bg-surface border border-border shadow-sm space-y-6 max-w-4xl mx-auto"
    >
      {/* 1. Header & Timer */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-primary animate-ping" />
            <span className="text-xs font-bold uppercase tracking-wider text-primary font-mono">
              Live Multi-Agent Pipeline Running
            </span>
          </div>
          <h3 className="text-xl md:text-2xl font-bold text-text-primary">
            Analyzing <span className="text-primary font-mono">{filename}</span>
          </h3>
          <p className="text-xs text-text-secondary">
            17 autonomous specialized agent nodes collaborating deterministically.
          </p>
        </div>

        <div className="flex items-center space-x-4 self-start sm:self-center">
          <div className="px-4 py-2 rounded-2xl bg-surface-accent/20 border border-border text-center">
            <span className="text-[10px] uppercase font-mono text-text-secondary block font-semibold">Elapsed</span>
            <span className="text-base font-mono font-bold text-text-primary">{formatTimer(elapsedSeconds)}</span>
          </div>
          <div className="px-4 py-2 rounded-2xl bg-primary/10 border border-primary/20 text-center">
            <span className="text-[10px] uppercase font-mono text-primary block font-semibold">Progress</span>
            <span className="text-base font-mono font-bold text-primary">{progressPct}%</span>
          </div>
        </div>
      </div>

      {/* 2. Progress Bar */}
      <div className="w-full bg-surface-accent/30 rounded-full h-2.5 overflow-hidden border border-border">
        <motion.div
          className="bg-primary h-full rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${progressPct}%` }}
          transition={{ duration: 0.3 }}
        />
      </div>

      {/* 3. 17-Step Agent Rail */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 pt-2 max-h-[460px] overflow-y-auto pr-1">
        {PIPELINE_STEPS.map((step) => {
          const isCompleted = completedSteps.includes(step.id);
          const isRunning = currentStep === step.id;
          const preview = livePreviews[step.id];
          const Icon = step.icon;

          return (
            <div
              key={step.id}
              className={`p-3 rounded-2xl border transition-all duration-200 flex items-start space-x-3 ${
                isRunning
                  ? 'bg-primary/5 border-primary shadow-sm'
                  : isCompleted
                  ? 'bg-surface-accent/15 border-border/80'
                  : 'bg-surface/50 border-border/40 opacity-50'
              }`}
            >
              <div className="mt-0.5 flex-shrink-0">
                {isCompleted ? (
                  <CheckCircle2 className="w-4 h-4 text-primary" />
                ) : isRunning ? (
                  <Loader2 className="w-4 h-4 text-primary animate-spin" />
                ) : (
                  <Circle className="w-4 h-4 text-text-secondary/40" />
                )}
              </div>

              <div className="flex-1 min-w-0 space-y-0.5">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-text-secondary uppercase">
                    Step {step.index}/17 • {step.agent}
                  </span>
                  {isRunning && (
                    <span className="text-[9px] font-bold uppercase px-1.5 py-0.2 rounded bg-primary text-white animate-pulse">
                      Active
                    </span>
                  )}
                </div>
                <h4 className="text-xs font-semibold text-text-primary truncate">
                  {step.label}
                </h4>

                {preview && (
                  <div className="text-[10px] text-text-secondary bg-surface rounded-md p-1.5 mt-1 border border-border/60">
                    {preview.quality_score && <span>Quality: <b>{preview.quality_score}/100</b> ({preview.grade})</span>}
                    {preview.domain && <span>Domain: <b>{preview.domain}</b></span>}
                    {preview.metrics_count && <span>Computed <b>{preview.metrics_count}</b> moments, <b>{preview.correlations_count}</b> correlations</span>}
                    {preview.top_title && <span>Top Insight: <b>{preview.top_title}</b></span>}
                    {preview.report_title && <span>Compiled <b>{preview.sections_count}</b> report sections</span>}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </motion.div>
  );
}
