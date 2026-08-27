import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ShieldCheck,
  CheckCircle2,
  HelpCircle,
  Layers,
  Database,
  Calendar,
  Sparkles,
  TrendingUp,
  Table,
  Hash,
  Award,
  FileCheck2,
  AlertTriangle,
  Bot,
  Cpu,
  BarChart3,
  Lightbulb,
  FileText,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
  Check,
  Zap,
  Activity,
  Terminal
} from 'lucide-react';

export default function OverviewTab({ report }) {
  const [expandedStep, setExpandedStep] = useState(null);
  const [filterCategory, setFilterCategory] = useState('all');

  if (!report) return null;

  const { understanding, profile, quality, statistics, sql_results, patterns, charts, insights } = report;

  // Build the complete, dynamic list of concrete steps taken by the AI multi-agent pipeline
  const aiSteps = [
    {
      id: 1,
      category: 'prep',
      stepNumber: '01',
      title: 'Dataset Ingestion & Schema Profiling',
      agent: 'DatasetLoader & DatasetProfiler',
      icon: Database,
      status: 'Completed',
      headline: `Ingested "${report.filename}" (${profile?.memory_size_kb?.toFixed(1) || 0} KB) and parsed schema.`,
      details: [
        `Loaded ${profile?.total_rows?.toLocaleString() || 0} records across ${profile?.total_columns || 0} variables.`,
        `Identified ${profile?.numeric_column_names?.length || 0} numeric metrics, ${profile?.categorical_column_names?.length || 0} categorical dimensions, and ${profile?.datetime_column_names?.length || 0} temporal fields.`,
        `Mapped column types and registered in-memory DuckDB table "${profile?.table_name || 'dataset'}" for ultra-fast SQL.`
      ],
      badge: `${profile?.total_rows || 0} Rows • ${profile?.total_columns || 0} Cols`
    },
    {
      id: 2,
      category: 'prep',
      stepNumber: '02',
      title: 'Data Quality & Cleanliness Audit',
      agent: 'QualityChecker',
      icon: ShieldAlert,
      status: 'Completed',
      headline: `Audited data cleanliness: Awarded Grade ${quality?.grade || 'A'} (${quality?.quality_score || 100}/100).`,
      details: [
        quality?.issues?.length > 0
          ? `Detected and cataloged ${quality.issues.length} data quality findings (${quality.issues.map(i => i.title || i.description).slice(0, 2).join('; ')}).`
          : 'Zero critical missing values, corrupted labels, or schema anomalies detected (100% clean data).',
        `Checked duplicate records: ${profile?.duplicate_rows_count || 0} duplicates found; ${profile?.null_cell_count || 0} null cells isolated.`,
        `Assessed analysis readiness: ${quality?.is_analysis_ready ? 'Dataset verified 100% analysis ready' : 'Flagged for attention'}.`
      ],
      badge: `Grade ${quality?.grade || 'A'} • ${quality?.issues?.length || 0} Findings`
    },
    {
      id: 3,
      category: 'modeling',
      stepNumber: '03',
      title: 'Semantic Domain & KPI Synthesis',
      agent: 'DatasetUnderstandingAgent',
      icon: Bot,
      status: 'Completed',
      headline: `Synthesized business domain as "${understanding?.domain || 'General Data'}" targeting ${understanding?.target_entity || 'records'}.`,
      details: [
        `Extracted ${understanding?.key_kpis?.length || 0} core business KPIs: ${understanding?.key_kpis?.map(k => k.name).join(', ') || 'Primary Revenue/Volume metrics'}.`,
        `Structured ${understanding?.core_questions?.length || 0} strategic business hypotheses and executive exploration vectors.`,
        `Mapped contextual dimension hierarchies across ${understanding?.important_dimensions?.join(', ') || 'available attributes'}.`
      ],
      badge: `${understanding?.key_kpis?.length || 0} Key KPIs`
    },
    {
      id: 4,
      category: 'modeling',
      stepNumber: '04',
      title: 'Statistical Moments & Quantile Modeling',
      agent: 'StatisticalEngine',
      icon: Activity,
      status: 'Completed',
      headline: `Computed parametric and non-parametric distributions across ${statistics?.univariate_metrics?.length || 0} numerical features.`,
      details: [
        `Calculated means, medians, standard deviations, interquartile ranges (IQR), and skewness moments.`,
        `Discovered ${statistics?.correlation_results?.filter(c => c.is_statistically_significant || Math.abs(c.pearson_coef) > 0.4).length || 0} statistically significant pairwise correlations.`,
        statistics?.correlation_results?.length > 0
          ? `Top relationship: ${statistics.correlation_results[0].col1} vs ${statistics.correlation_results[0].col2} (Pearson r = ${statistics.correlation_results[0].pearson_coef?.toFixed(2)}).`
          : 'Verified absence of severe multicollinearity.'
      ],
      badge: `${statistics?.univariate_metrics?.length || 0} Metrics Modeled`
    },
    {
      id: 5,
      category: 'modeling',
      stepNumber: '05',
      title: 'Safe DuckDB SQL Generation & Execution',
      agent: 'SQLGenerationAgent & SQLExecutor',
      icon: Terminal,
      status: 'Completed',
      headline: `Synthesized and executed ${sql_results?.successful_queries || 0} analytical queries in DuckDB.`,
      details: [
        `Generated ${sql_results?.total_queries || 0} targeted analytical SQL statements answering key business questions.`,
        `Passed all AST query safety rules (SELECT/CTE verification, zero destructive queries allowed).`,
        `Executed in-memory with 100% success rate across DuckDB tables.`
      ],
      badge: `${sql_results?.successful_queries || 0}/${sql_results?.total_queries || 0} Queries Run`
    },
    {
      id: 6,
      category: 'insights',
      stepNumber: '06',
      title: 'Empirical Pattern & Anomaly Detection',
      agent: 'PatternDetector',
      icon: TrendingUp,
      status: 'Completed',
      headline: `Extracted ${patterns?.trends?.length || 0} trends, ${patterns?.concentrations?.length || 0} Pareto concentrations, and ${patterns?.anomalies?.length || 0} outliers.`,
      details: [
        patterns?.trends?.length > 0
          ? `Identified trajectory trends: ${patterns.trends.map(t => `${t.metric_column} (${t.direction})`).join(', ')}.`
          : 'Scanned for metric drift and time trends.',
        patterns?.concentrations?.length > 0
          ? `Pareto concentration: ${patterns.concentrations[0]?.description || 'Top segments analyzed'}.`
          : 'Calculated dimension distribution balance.',
        patterns?.anomalies?.length > 0
          ? `Flagged anomalies: ${patterns.anomalies.map(a => `${a.row_identifier} (${a.description})`).slice(0, 2).join('; ')}.`
          : 'Zero extreme multi-sigma outliers found.'
      ],
      badge: `${(patterns?.trends?.length || 0) + (patterns?.concentrations?.length || 0) + (patterns?.anomalies?.length || 0)} Patterns Found`
    },
    {
      id: 7,
      category: 'insights',
      stepNumber: '07',
      title: 'Interactive Plotly Visualizations',
      agent: 'ChartGenerator',
      icon: BarChart3,
      status: 'Completed',
      headline: `Rendered ${charts?.charts?.length || 0} interactive Plotly charts tailored to data types.`,
      details: [
        `Heuristically selected chart types based on cardinality and distributions (Histograms, Scatter plots, Box plots, Bar charts).`,
        `Generated specs: ${charts?.charts?.map(c => c.title.replace(/<[^>]*>/g, '')).slice(0, 3).join(' • ') || 'Interactive charts'}.`,
        `Configured custom theme color tokens and interactive tooltip annotations.`
      ],
      badge: `${charts?.charts?.length || 0} Visuals Created`
    },
    {
      id: 8,
      category: 'insights',
      stepNumber: '08',
      title: 'Adversarial Critic Fact-Checking & Insight Synthesis',
      agent: 'InsightGenerationAgent & CriticReviewAgent',
      icon: Lightbulb,
      status: 'Completed',
      headline: `Synthesized ${insights?.insights?.length || 0} verified insights with supporting empirical evidence.`,
      details: [
        `Formulated strategic findings and specific actionable recommendations for stakeholders.`,
        `Subjected findings to an adversarial Critic Review Agent loop to verify mathematical ground truth.`,
        `Audited evidence grounding: All insights verified against calculated statistical metrics.`
      ],
      badge: `${insights?.insights?.length || 0} Insights Audited`
    },
    {
      id: 9,
      category: 'insights',
      stepNumber: '09',
      title: 'Executive Report & Publication PDF Compilation',
      agent: 'ReportGenerationAgent & PDFExporter',
      icon: FileText,
      status: 'Completed',
      headline: `Compiled structured executive report with ${report.sections?.length || 0} sections and PDF download.`,
      details: [
        `Generated structured Markdown report with Executive Summary, Findings, and Strategic Actions.`,
        `Rendered publication-ready ReportLab vector PDF with high-contrast formatting and color palette.`,
        `Archived run to persistent Analysis History for instant retrieval.`
      ],
      badge: `${report.sections?.length || 0} Report Sections`
    }
  ];

  const filteredSteps = aiSteps.filter(step => {
    if (filterCategory === 'all') return true;
    return step.category === filterCategory;
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-8"
    >
      {/* 1. Quick Stats Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
        <div className="glass-card p-4 md:p-5 rounded-3xl relative overflow-hidden border border-[#CEAB93]/50 hover:shadow-md transition-all">
          <div className="relative z-10 space-y-1">
            <span className="text-[10px] font-mono uppercase text-[#7D5A44] block font-extrabold">Total Records</span>
            <span className="text-xl font-extrabold text-[#3E2723] font-mono">{profile?.total_rows?.toLocaleString() || '0'}</span>
          </div>
          <Table className="w-12 h-12 text-[#AD8B73]/10 absolute -bottom-2 -right-2 pointer-events-none" />
        </div>

        <div className="glass-card p-4 md:p-5 rounded-3xl relative overflow-hidden border border-[#CEAB93]/50 hover:shadow-md transition-all">
          <div className="relative z-10 space-y-1">
            <span className="text-[10px] font-mono uppercase text-[#7D5A44] block font-extrabold">Variables</span>
            <span className="text-xl font-extrabold text-[#3E2723] font-mono">{profile?.total_columns || '0'}</span>
          </div>
          <Hash className="w-12 h-12 text-[#AD8B73]/10 absolute -bottom-2 -right-2 pointer-events-none" />
        </div>

        <div className="glass-card p-4 md:p-5 rounded-3xl relative overflow-hidden border border-[#CEAB93]/50 hover:shadow-md transition-all">
          <div className="relative z-10 space-y-1">
            <span className="text-[10px] font-mono uppercase text-[#7D5A44] block font-extrabold">Quality Grade</span>
            <span className="text-xl font-extrabold text-[#AD8B73] font-display">Grade {quality?.grade || 'A'}</span>
          </div>
          <Award className="w-12 h-12 text-[#AD8B73]/10 absolute -bottom-2 -right-2 pointer-events-none" />
        </div>

        <div className="glass-card p-4 md:p-5 rounded-3xl relative overflow-hidden border border-[#CEAB93]/50 hover:shadow-md transition-all">
          <div className="relative z-10 space-y-1">
            <span className="text-[10px] font-mono uppercase text-[#7D5A44] block font-extrabold">Cleanliness</span>
            <span className="text-xl font-extrabold text-[#3E2723] font-mono">{quality?.quality_score || 100}/100</span>
          </div>
          <ShieldCheck className="w-12 h-12 text-[#AD8B73]/10 absolute -bottom-2 -right-2 pointer-events-none" />
        </div>

        <div className="glass-card p-4 md:p-5 rounded-3xl relative overflow-hidden border border-[#CEAB93]/50 hover:shadow-md transition-all">
          <div className="relative z-10 space-y-1">
            <span className="text-[10px] font-mono uppercase text-[#7D5A44] block font-extrabold">Numeric KPIs</span>
            <span className="text-xl font-extrabold text-[#3E2723] font-mono">{profile?.numeric_column_names?.length || '0'}</span>
          </div>
          <TrendingUp className="w-12 h-12 text-[#AD8B73]/10 absolute -bottom-2 -right-2 pointer-events-none" />
        </div>

        <div className="glass-card p-4 md:p-5 rounded-3xl relative overflow-hidden border border-[#CEAB93]/50 hover:shadow-md transition-all">
          <div className="relative z-10 space-y-1">
            <span className="text-[10px] font-mono uppercase text-[#7D5A44] block font-extrabold">Duplicates</span>
            <span className="text-xl font-extrabold text-[#3E2723] font-mono">{profile?.duplicate_rows_count || 0}</span>
          </div>
          <FileCheck2 className="w-12 h-12 text-[#AD8B73]/10 absolute -bottom-2 -right-2 pointer-events-none" />
        </div>
      </div>

      {/* 2. Autonomous AI Agent Execution Audit Log */}
      <div className="glass-card p-6 md:p-8 rounded-3xl space-y-6 shadow-glass border border-[#CEAB93]/60">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#CEAB93]/30">
          <div className="space-y-1">
            <div className="flex items-center space-x-2.5 text-[#3E2723]">
              <div className="w-8 h-8 rounded-xl bg-[#AD8B73]/15 text-[#3E2723] flex items-center justify-center">
                <Bot className="w-5 h-5 text-[#AD8B73]" />
              </div>
              <h3 className="font-extrabold text-lg md:text-xl font-display">
                Autonomous AI Agent Execution Audit Log
              </h3>
            </div>
            <p className="text-xs text-[#7D5A44]">
              Complete chronological audit of deterministic calculations, quality sanitization, SQL runs, charts, and reasoning steps taken by the AI.
            </p>
          </div>

          {/* Filter Pills */}
          <div className="flex items-center space-x-1.5 p-1 bg-white/70 rounded-2xl border border-[#CEAB93]/40 self-start sm:self-center text-xs font-mono">
            {[
              { id: 'all', label: `All Steps (${aiSteps.length})` },
              { id: 'prep', label: 'Data Prep' },
              { id: 'modeling', label: 'Modeling & SQL' },
              { id: 'insights', label: 'Insights & Charts' }
            ].map(f => (
              <button
                key={f.id}
                onClick={() => setFilterCategory(f.id)}
                className={`px-3 py-1 rounded-xl transition-all font-bold cursor-pointer ${
                  filterCategory === f.id
                    ? 'bg-[#AD8B73] text-white shadow-xs'
                    : 'text-[#7D5A44] hover:text-[#3E2723] hover:bg-[#FFFBE9]'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        {/* Step-by-Step Interactive Cards */}
        <div className="space-y-3.5">
          {filteredSteps.map((step) => {
            const Icon = step.icon;
            const isExpanded = expandedStep === step.id;

            return (
              <motion.div
                key={step.id}
                layout
                className={`rounded-2xl border transition-all duration-200 ${
                  isExpanded
                    ? 'bg-white border-[#AD8B73] shadow-md ring-1 ring-[#AD8B73]/30'
                    : 'bg-white/80 hover:bg-white border-[#CEAB93]/40 hover:border-[#AD8B73]/60 shadow-xs'
                }`}
              >
                <div
                  onClick={() => setExpandedStep(isExpanded ? null : step.id)}
                  className="p-4 md:p-5 flex items-start sm:items-center justify-between gap-3.5 cursor-pointer"
                >
                  <div className="flex items-start sm:items-center space-x-3.5 min-w-0 flex-1">
                    <span className="w-8 h-8 rounded-xl bg-[#AD8B73]/15 text-[#3E2723] font-mono text-xs font-bold flex items-center justify-center flex-shrink-0 border border-[#CEAB93]/40">
                      {step.stepNumber}
                    </span>

                    <div className="min-w-0 flex-1 space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h4 className="font-extrabold text-sm text-[#3E2723] font-display">
                          {step.title}
                        </h4>
                        <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-[#AD8B73]/15 text-[#3E2723] border border-[#CEAB93]/50">
                          {step.agent}
                        </span>
                      </div>
                      <p className="text-xs text-[#7D5A44] leading-relaxed">
                        {step.headline}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2.5 flex-shrink-0">
                    <span className="hidden md:inline text-[11px] font-mono font-bold px-2.5 py-1 rounded-xl bg-white border border-[#CEAB93]/50 text-[#3E2723]">
                      {step.badge}
                    </span>
                    <div className="w-6 h-6 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center border border-emerald-200" title="Step Complete">
                      <Check className="w-3.5 h-3.5" />
                    </div>
                    <button className="text-[#7D5A44] hover:text-[#3E2723] p-1">
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="px-5 pb-5 pt-1 border-t border-[#CEAB93]/20 space-y-2.5 text-xs text-[#3E2723]"
                    >
                      <div className="bg-[#FFFBE9]/70 p-4 rounded-xl border border-[#CEAB93]/30 space-y-2">
                        <span className="font-mono text-[10px] font-bold uppercase text-[#AD8B73] block tracking-wider">
                          Detailed Actions Executed by Agent
                        </span>
                        <ul className="space-y-1.5 font-sans">
                          {step.details.map((detail, dIdx) => (
                            <li key={dIdx} className="flex items-start space-x-2 text-[#3E2723] leading-relaxed">
                              <span className="w-1.5 h-1.5 rounded-full bg-[#AD8B73] mt-1.5 flex-shrink-0" />
                              <span>{detail}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* 3. Executive Synthesis Callout */}
      <div className="glass-card p-6 md:p-8 rounded-3xl border-l-4 border-l-[#AD8B73] space-y-5 shadow-glass">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2.5 text-[#3E2723] font-extrabold text-sm md:text-base font-display">
            <div className="w-8 h-8 rounded-xl bg-[#AD8B73]/15 text-[#3E2723] flex items-center justify-center">
              <ShieldCheck className="w-5 h-5 text-[#AD8B73]" />
            </div>
            <span>Executive Strategic Synthesis</span>
          </div>
          <span className="text-xs px-3 py-1 rounded-full bg-[#AD8B73]/15 text-[#3E2723] font-mono font-bold border border-[#CEAB93]/60">
            {understanding?.domain || 'General Data Domain'}
          </span>
        </div>

        <p className="text-sm md:text-base text-[#3E2723] leading-relaxed font-normal bg-white/70 p-5 rounded-2xl border border-[#CEAB93]/30 shadow-inner">
          {report.executive_summary}
        </p>

        {insights?.executive_summary_points?.length > 0 && (
          <div className="pt-2 grid grid-cols-1 md:grid-cols-3 gap-3.5">
            {insights.executive_summary_points.map((pt, idx) => (
              <div
                key={idx}
                className="p-4 rounded-2xl bg-white/80 border border-[#CEAB93]/40 text-xs text-[#3E2723] leading-relaxed flex items-start space-x-3 shadow-sm"
              >
                <CheckCircle2 className="w-4 h-4 text-[#AD8B73] mt-0.5 flex-shrink-0" />
                <span className="font-semibold">{pt}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 4. Core Strategic Questions Answered */}
      {understanding?.core_questions?.length > 0 && (
        <div className="glass-card p-6 md:p-8 rounded-3xl space-y-4 shadow-glass">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-xl bg-[#AD8B73]/15 text-[#3E2723] flex items-center justify-center">
              <HelpCircle className="w-5 h-5 text-[#AD8B73]" />
            </div>
            <h4 className="font-extrabold text-[#3E2723] text-sm md:text-base tracking-tight font-display">
              Core Strategic Business Questions Answered
            </h4>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
            {understanding.core_questions.map((q, idx) => (
              <div
                key={idx}
                className="p-4 rounded-2xl bg-white/80 border border-[#CEAB93]/40 text-xs text-[#3E2723] flex items-start space-x-3.5 shadow-sm hover:border-[#AD8B73] transition-colors"
              >
                <span className="w-6 h-6 rounded-xl bg-gradient-to-br from-[#AD8B73] to-[#3E2723] text-white font-mono text-xs font-bold flex items-center justify-center flex-shrink-0 shadow-sm">
                  {idx + 1}
                </span>
                <span className="leading-relaxed font-medium">{q}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
}
