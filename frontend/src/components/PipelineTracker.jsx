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
  FileText,
  Clock,
  Square
} from 'lucide-react';

const PIPELINE_STEPS = [
  { id: 'validate_file', index: 1, label: 'Validating File Structure & Encoding', agent: 'FileValidator', icon: FileCheck },
  { id: 'load_dataset', index: 2, label: 'Ingesting Raw Data & DuckDB Registration', agent: 'DatasetLoader', icon: Database },
  { id: 'profile_and_audit', index: 3, label: 'Profiling Schema & Quality Auditing', agent: 'QualityChecker', icon: ShieldAlert },
  { id: 'clean_and_standardize', index: 4, label: 'Sanitizing, Imputing & Standardizing Data', agent: 'DataCleaner', icon: Sparkles },
  { id: 'understand_dataset', index: 5, label: 'Synthesizing Domain & Analytical Intent', agent: 'DatasetUnderstandingAgent', icon: Bot },
  { id: 'plan_analysis', index: 6, label: 'Formulating Adaptive Analysis Plan', agent: 'AnalysisPlanningAgent', icon: Layers },
  { id: 'run_statistical_analysis', index: 7, label: 'Computing Distributions & Moments', agent: 'StatisticalEngine', icon: BarChart3 },
  { id: 'generate_sql', index: 8, label: 'Synthesizing Analytical DuckDB SQL', agent: 'SQLGenerationAgent', icon: Bot },
  { id: 'validate_sql', index: 9, label: 'Verifying SQL Syntax & Security Guards', agent: 'SQLValidator', icon: ShieldAlert },
  { id: 'execute_sql', index: 10, label: 'Executing In-Memory DuckDB Aggregations', agent: 'SQLExecutor', icon: Database },
  { id: 'detect_patterns', index: 11, label: 'Discovering Trends, Pareto Shares & Outliers', agent: 'PatternDetector', icon: BarChart3 },
  { id: 'render_charts', index: 12, label: 'Compiling Domain-Adaptive Plotly Visuals', agent: 'ChartGenerator', icon: BarChart3 },
  { id: 'generate_insights', index: 13, label: 'Extracting Strict 4-Part Evidence Insights', agent: 'InsightGenerationAgent', icon: Lightbulb },
  { id: 'critic_review', index: 14, label: 'Adversarial Fact-Checking & Auditing', agent: 'CriticReviewAgent', icon: ShieldAlert },
  { id: 'revise_insights', index: 15, label: 'Refining Findings & Correcting Weak Claims', agent: 'InsightRevisionOrchestrator', icon: Bot },
  { id: 'generate_report', index: 16, label: 'Compiling Comprehensive Executive Report', agent: 'ReportGenerationAgent', icon: FileText },
  { id: 'render_pdf', index: 17, label: 'Rendering Publication-Grade PDF & Caching', agent: 'PDFExporter', icon: FileText },
];

export default function PipelineTracker({
  currentStep,
  completedSteps = [],
  livePreviews = {},
  filename = 'dataset.csv',
  onStop,
  isStopping = false
}) {
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
      className="glass-card p-6 md:p-8 rounded-3xl space-y-6 max-w-4xl mx-auto shadow-glass border border-[#CEAB93]/60"
    >
      {/* 1. Header & Live Clock & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-[#CEAB93]/40">
        <div className="space-y-1.5">
          <div className="flex items-center space-x-2">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#AD8B73] opacity-75" />
              <span className="relative inline-flex rounded-full h-3 w-3 bg-[#AD8B73]" />
            </span>
            <span className="text-xs font-bold uppercase tracking-wider text-[#3E2723] font-mono">
              Live Multi-Agent Orchestration Active
            </span>
          </div>
          <h3 className="text-xl md:text-2xl font-black text-[#3E2723] font-display">
            Analyzing <span className="font-mono text-[#AD8B73] bg-[#AD8B73]/10 px-2 py-0.5 rounded-xl">{filename}</span>
          </h3>
          <p className="text-xs text-[#7D5A44]">
            17 autonomous specialized nodes executing deterministic calculations & LLM reasoning.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5 self-start sm:self-center">
          <div className="px-3.5 py-2 rounded-2xl bg-white/90 border border-[#CEAB93]/50 shadow-sm text-center">
            <div className="flex items-center space-x-1 text-[10px] uppercase font-mono text-[#7D5A44] font-bold justify-center">
              <Clock className="w-3 h-3" />
              <span>Elapsed</span>
            </div>
            <span className="text-sm font-mono font-extrabold text-[#3E2723]">{formatTimer(elapsedSeconds)}</span>
          </div>

          <div className="px-3.5 py-2 rounded-2xl bg-gradient-to-br from-[#AD8B73]/15 to-[#E3CAA5]/30 border border-[#AD8B73]/40 shadow-sm text-center">
            <span className="text-[10px] uppercase font-mono text-[#3E2723] block font-bold">Progress</span>
            <span className="text-sm font-mono font-extrabold text-[#3E2723]">{progressPct}%</span>
          </div>

          {onStop && (
            <button
              onClick={onStop}
              disabled={isStopping}
              className="flex items-center space-x-1.5 px-4 py-2 rounded-2xl bg-red-50 hover:bg-red-100 border border-red-200 text-red-700 text-xs font-bold transition-all shadow-sm hover:shadow-md cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed group"
              title="Terminate Pipeline Execution"
            >
              <Square className="w-3.5 h-3.5 fill-red-600 text-red-600 group-hover:scale-110 transition-transform" />
              <span>{isStopping ? 'Stopping...' : 'Stop Execution'}</span>
            </button>
          )}
        </div>
      </div>

      {/* 2. Dynamic Progress Bar */}
      <div className="space-y-1.5">
        <div className="flex justify-between text-xs font-mono font-semibold text-[#7D5A44]">
          <span>Pipeline Nodes Completed: {completedSteps.length}/17</span>
          <span>{progressPct}%</span>
        </div>
        <div className="w-full bg-[#E3CAA5]/30 rounded-full h-3 overflow-hidden border border-[#CEAB93]/50 shadow-inner">
          <motion.div
            className="bg-gradient-to-r from-[#AD8B73] to-[#3E2723] h-full rounded-full shadow-sm"
            initial={{ width: 0 }}
            animate={{ width: `${progressPct}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>
      </div>

      {/* 3. 17-Step Agent Rail - Full Height Without Inner Scroller */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
        {PIPELINE_STEPS.map((step) => {
          const isCompleted = completedSteps.includes(step.id);
          const isRunning = currentStep === step.id;
          const preview = livePreviews[step.id];
          const Icon = step.icon;

          return (
            <div
              key={step.id}
              className={`p-3.5 rounded-2xl border transition-all duration-300 flex items-start space-x-3.5 ${
                isRunning
                  ? 'bg-white border-[#AD8B73] shadow-md ring-2 ring-[#AD8B73]/20'
                  : isCompleted
                  ? 'bg-white/85 border-[#CEAB93]/50'
                  : 'bg-white/40 border-[#CEAB93]/20 opacity-55'
              }`}
            >
              <div className="mt-1 flex-shrink-0">
                {isCompleted ? (
                  <div className="w-5 h-5 rounded-full bg-[#AD8B73]/15 flex items-center justify-center text-[#AD8B73]">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                ) : isRunning ? (
                  <div className="w-5 h-5 rounded-full bg-[#AD8B73]/20 flex items-center justify-center text-[#3E2723]">
                    <Loader2 className="w-4 h-4 animate-spin text-[#AD8B73]" />
                  </div>
                ) : (
                  <div className="w-5 h-5 rounded-full bg-gray-200/50 flex items-center justify-center text-gray-400">
                    <Circle className="w-3.5 h-3.5" />
                  </div>
                )}
              </div>

              <div className="flex-1 min-w-0 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-[#7D5A44] font-bold uppercase">
                    Node {step.index}/17 • {step.agent}
                  </span>
                  {isRunning && (
                    <span className="text-[9px] font-bold uppercase px-2 py-0.5 rounded-full bg-[#AD8B73] text-white animate-pulse">
                      Executing
                    </span>
                  )}
                </div>
                <h4 className="text-xs font-bold text-[#3E2723] truncate">
                  {step.label}
                </h4>

                {preview && (
                  <div className="text-[11px] text-[#3E2723] bg-[#FFFBE9]/80 rounded-xl p-2 mt-1 border border-[#CEAB93]/50 font-medium">
                    {preview.quality_score && <span>Quality Score: <b>{preview.quality_score}/100</b> ({preview.grade})</span>}
                    {preview.domain && <span>Inferred Domain: <b>{preview.domain}</b></span>}
                    {preview.metrics_count && <span>Moments: <b>{preview.metrics_count}</b>, Correlations: <b>{preview.correlations_count}</b></span>}
                    {preview.top_title && <span>Top Insight: <b>{preview.top_title}</b></span>}
                    {preview.report_title && <span>Compiled <b>{preview.sections_count}</b> sections</span>}
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
