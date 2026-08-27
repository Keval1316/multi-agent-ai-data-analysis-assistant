import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Info,
  CheckCircle2,
  Columns,
  Hash,
  Database,
  Calendar,
  Layers,
  Sparkles,
  TrendingUp,
  Filter,
  BarChart3,
  Loader2,
  Copy
} from 'lucide-react';

export default function DatasetProfileView({ datasetId, onProceedToAnalysis }) {
  const [profile, setProfile] = useState(null);
  const [quality, setQuality] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('quality'); // 'quality' | 'columns' | 'distributions'

  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  useEffect(() => {
    if (!datasetId) return;

    setLoading(true);
    setError(null);

    Promise.all([
      fetch(`${apiBaseUrl}/api/dataset/${datasetId}/profile`).then((res) => {
        if (!res.ok) throw new Error('Failed to load dataset profile.');
        return res.json();
      }),
      fetch(`${apiBaseUrl}/api/dataset/${datasetId}/quality`).then((res) => {
        if (!res.ok) throw new Error('Failed to load data quality report.');
        return res.json();
      }),
    ])
      .then(([profData, qualData]) => {
        setProfile(profData);
        setQuality(qualData);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'An error occurred while inspecting the dataset.');
        setLoading(false);
      });
  }, [datasetId, apiBaseUrl]);

  if (loading) {
    return (
      <div className="w-full max-w-4xl mx-auto rounded-3xl bg-surface border border-border p-12 text-center shadow-sm">
        <Loader2 className="w-10 h-10 text-primary animate-spin mx-auto mb-4" />
        <h4 className="text-lg font-bold text-text-primary">Profiling Dataset & Auditing Quality...</h4>
        <p className="text-xs text-text-secondary mt-1">Computing statistical moments, distributions, IQR outliers, and category consistency.</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full max-w-4xl mx-auto rounded-3xl bg-red-50 border border-red-200 p-6 text-red-700 shadow-sm">
        <p className="font-bold text-sm">Failed to Load Profile</p>
        <p className="text-xs text-red-600 mt-1">{error}</p>
      </div>
    );
  }

  if (!profile || !quality) return null;

  const getScoreColor = (score) => {
    if (score >= 90) return 'text-primary border-primary bg-surface-accent/20';
    if (score >= 75) return 'text-emerald-700 border-emerald-400 bg-emerald-50';
    if (score >= 60) return 'text-amber-700 border-amber-400 bg-amber-50';
    return 'text-red-700 border-red-400 bg-red-50';
  };

  const getSeverityBadge = (severity) => {
    switch (severity) {
      case 'confirmed_issue':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-lg text-[10px] font-bold uppercase tracking-wider bg-red-100 text-red-700 border border-red-200">
            <ShieldAlert className="w-3 h-3 mr-1" />
            Confirmed Issue
          </span>
        );
      case 'suspicious_issue':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-lg text-[10px] font-bold uppercase tracking-wider bg-amber-100 text-amber-700 border border-amber-200">
            <AlertTriangle className="w-3 h-3 mr-1" />
            Suspicious
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-lg text-[10px] font-bold uppercase tracking-wider bg-surface-accent/30 text-text-primary border border-border">
            <Info className="w-3 h-3 mr-1 text-primary" />
            Informational
          </span>
        );
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-5xl mx-auto space-y-6"
    >
      {/* Top Banner: Quality Score & Health Card */}
      <div className="rounded-3xl bg-surface border border-border p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-center space-x-5">
            <div className={`w-20 h-20 rounded-2xl border-2 flex flex-col items-center justify-center font-extrabold shadow-sm ${getScoreColor(quality.quality_score)}`}>
              <span className="text-2xl leading-none">{quality.quality_score}</span>
              <span className="text-[10px] tracking-wider uppercase opacity-80 mt-1">Grade {quality.grade}</span>
            </div>

            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-xl font-bold text-text-primary tracking-tight">
                  Data Quality & Structure Assessment
                </h3>
                {quality.is_analysis_ready ? (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-surface-accent/40 text-text-primary border border-border">
                    <CheckCircle2 className="w-3.5 h-3.5 text-primary mr-1" />
                    Analysis Ready
                  </span>
                ) : (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-700 border border-red-200">
                    <AlertTriangle className="w-3.5 h-3.5 mr-1" />
                    Review Required
                  </span>
                )}
              </div>
              <p className="text-xs text-text-secondary mt-1 max-w-xl leading-relaxed">
                {quality.summary}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {onProceedToAnalysis && (
              <button
                onClick={onProceedToAnalysis}
                className="px-5 py-2.5 rounded-2xl bg-primary text-white font-semibold text-sm hover:bg-primary-hover transition-colors shadow-sm flex items-center gap-2"
              >
                <Sparkles className="w-4 h-4" />
                <span>Begin Multi-Agent Analysis</span>
              </button>
            )}
          </div>
        </div>

        {/* Severity Metrics Bar */}
        <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-border">
          <div className="p-3.5 rounded-2xl bg-red-50/70 border border-red-200/80 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <ShieldAlert className="w-4 h-4 text-red-600" />
              <span className="text-xs font-semibold text-red-900">Confirmed Issues</span>
            </div>
            <span className="text-base font-extrabold text-red-700">
              {quality.issues_count.confirmed_issue || 0}
            </span>
          </div>

          <div className="p-3.5 rounded-2xl bg-amber-50/70 border border-amber-200/80 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              <span className="text-xs font-semibold text-amber-900">Suspicious Anomalies</span>
            </div>
            <span className="text-base font-extrabold text-amber-700">
              {quality.issues_count.suspicious_issue || 0}
            </span>
          </div>

          <div className="p-3.5 rounded-2xl bg-surface-accent/20 border border-border flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Info className="w-4 h-4 text-primary" />
              <span className="text-xs font-semibold text-text-primary">Observations</span>
            </div>
            <span className="text-base font-extrabold text-text-primary">
              {quality.issues_count.informational || 0}
            </span>
          </div>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="flex space-x-2 border-b border-border pb-1">
        <button
          onClick={() => setActiveTab('quality')}
          className={`px-4 py-2 rounded-2xl text-xs font-bold transition-all ${
            activeTab === 'quality'
              ? 'bg-surface text-text-primary border border-border shadow-xs'
              : 'text-text-secondary hover:text-text-primary'
          }`}
        >
          Quality Audit Issues ({quality.total_issues})
        </button>

        <button
          onClick={() => setActiveTab('columns')}
          className={`px-4 py-2 rounded-2xl text-xs font-bold transition-all ${
            activeTab === 'columns'
              ? 'bg-surface text-text-primary border border-border shadow-xs'
              : 'text-text-secondary hover:text-text-primary'
          }`}
        >
          Column Schemas & Types ({profile.total_columns})
        </button>

        <button
          onClick={() => setActiveTab('distributions')}
          className={`px-4 py-2 rounded-2xl text-xs font-bold transition-all ${
            activeTab === 'distributions'
              ? 'bg-surface text-text-primary border border-border shadow-xs'
              : 'text-text-secondary hover:text-text-primary'
          }`}
        >
          Distributions & Statistics
        </button>
      </div>

      {/* Tab 1: Quality Issues */}
      {activeTab === 'quality' && (
        <div className="space-y-4">
          {quality.issues.length === 0 ? (
            <div className="p-10 text-center rounded-3xl bg-surface border border-border">
              <CheckCircle2 className="w-10 h-10 text-primary mx-auto mb-2" />
              <h4 className="text-base font-bold text-text-primary">No Quality Issues Detected</h4>
              <p className="text-xs text-text-secondary mt-1">This dataset is exceptionally clean and ready for statistical modeling.</p>
            </div>
          ) : (
            quality.issues.map((issue) => (
              <div
                key={issue.id}
                className="p-5 rounded-3xl bg-surface border border-border shadow-xs space-y-3 hover:border-primary/60 transition-colors"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center space-x-3">
                    {getSeverityBadge(issue.severity)}
                    {issue.column_name && (
                      <span className="font-mono text-xs px-2.5 py-0.5 rounded-lg bg-surface-accent/20 border border-border text-text-primary font-semibold">
                        {issue.column_name}
                      </span>
                    )}
                  </div>

                  {issue.affected_count > 0 && (
                    <span className="text-[11px] font-medium text-text-secondary">
                      Affected: <span className="font-bold text-text-primary">{issue.affected_count.toLocaleString()} rows</span> ({issue.affected_percentage}%)
                    </span>
                  )}
                </div>

                <div>
                  <h4 className="text-sm font-bold text-text-primary">{issue.title}</h4>
                  <p className="text-xs text-text-secondary mt-1 leading-relaxed">{issue.description}</p>
                </div>

                {issue.sample_affected_values && issue.sample_affected_values.length > 0 && (
                  <div className="text-[11px] bg-surface-accent/10 border border-border rounded-xl p-2 font-mono text-text-primary">
                    <span className="font-semibold text-text-secondary">Sample anomalies: </span>
                    {JSON.stringify(issue.sample_affected_values)}
                  </div>
                )}

                <div className="pt-2 border-t border-border/60 flex items-center text-xs text-text-secondary">
                  <span className="font-semibold text-primary mr-1.5">Suggested Remedy:</span>
                  <span>{issue.suggested_action}</span>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Tab 2: Column Profiles */}
      {activeTab === 'columns' && (
        <div className="rounded-3xl bg-surface border border-border overflow-hidden shadow-xs">
          <div className="overflow-x-auto">
            <table className="min-w-full text-xs text-left">
              <thead className="bg-surface-accent/20 text-text-primary border-b border-border font-semibold">
                <tr>
                  <th className="px-4 py-3">Column Name</th>
                  <th className="px-4 py-3">Semantic Type</th>
                  <th className="px-4 py-3">Data Type</th>
                  <th className="px-4 py-3">Missingness</th>
                  <th className="px-4 py-3">Cardinality</th>
                  <th className="px-4 py-3">Attributes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border font-mono text-[11px]">
                {profile.column_profiles.map((col, idx) => (
                  <tr key={`${col.name}-${idx}`} className="hover:bg-surface-accent/10 transition-colors">
                    <td className="px-4 py-3 font-semibold text-text-primary">
                      {col.name}
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded-lg bg-surface border border-border text-[10px] uppercase font-bold text-primary">
                        {col.semantic_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-text-secondary">{col.dtype}</td>
                    <td className="px-4 py-3">
                      <span className={col.null_count > 0 ? 'text-amber-700 font-semibold' : 'text-text-secondary'}>
                        {col.null_count} ({col.null_percentage}%)
                      </span>
                    </td>
                    <td className="px-4 py-3 text-text-primary">
                      {col.unique_count} distinct ({col.unique_percentage}%)
                    </td>
                    <td className="px-4 py-3">
                      {col.is_identifier_candidate && (
                        <span className="px-2 py-0.5 rounded-lg bg-surface-accent/40 text-text-primary text-[10px] font-bold">
                          Primary Key ID
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Distributions & Numeric Stats */}
      {activeTab === 'distributions' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Numeric Columns Stats */}
          <div className="space-y-4">
            <h4 className="text-xs font-bold text-text-secondary uppercase tracking-wider flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-primary" />
              Numeric Column Summary
            </h4>
            {profile.column_profiles.filter((c) => c.numeric_stats).map((col, idx) => (
              <div key={`${col.name}-${idx}`} className="p-4 rounded-3xl bg-surface border border-border space-y-2 shadow-xs">
                <div className="flex justify-between items-center border-b border-border pb-2">
                  <span className="font-mono text-xs font-bold text-text-primary">{col.name}</span>
                  <span className="text-[10px] text-text-secondary">Mean: {col.numeric_stats.mean.toFixed(2)}</span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-[11px] font-mono">
                  <div className="bg-surface-accent/15 p-2 rounded-xl border border-border">
                    <span className="text-[10px] text-text-secondary block">Min / Max</span>
                    <span className="font-bold">{col.numeric_stats.min} / {col.numeric_stats.max}</span>
                  </div>
                  <div className="bg-surface-accent/15 p-2 rounded-xl border border-border">
                    <span className="text-[10px] text-text-secondary block">Median (Q2)</span>
                    <span className="font-bold">{col.numeric_stats.median}</span>
                  </div>
                  <div className="bg-surface-accent/15 p-2 rounded-xl border border-border">
                    <span className="text-[10px] text-text-secondary block">Std Dev / IQR</span>
                    <span className="font-bold">{col.numeric_stats.std.toFixed(1)} / {col.numeric_stats.iqr.toFixed(1)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Categorical Top Values */}
          <div className="space-y-4">
            <h4 className="text-xs font-bold text-text-secondary uppercase tracking-wider flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-primary" />
              Categorical Frequencies (Top 5)
            </h4>
            {profile.column_profiles.filter((c) => c.categorical_stats && c.categorical_stats.top_values.length > 0).map((col, idx) => (
              <div key={`${col.name}-${idx}`} className="p-4 rounded-3xl bg-surface border border-border space-y-2 shadow-xs">
                <div className="flex justify-between items-center border-b border-border pb-2">
                  <span className="font-mono text-xs font-bold text-text-primary">{col.name}</span>
                  <span className="text-[10px] text-text-secondary">{col.categorical_stats.unique_count} categories</span>
                </div>
                <div className="space-y-1.5 pt-1">
                  {col.categorical_stats.top_values.map((v, i) => (
                    <div key={i} className="text-[11px]">
                      <div className="flex justify-between text-text-primary mb-0.5">
                        <span className="font-mono truncate max-w-[180px]">{v.value || '<empty>'}</span>
                        <span className="text-text-secondary font-mono">{v.count} ({v.percentage}%)</span>
                      </div>
                      <div className="w-full h-1.5 bg-surface-accent/20 rounded-full overflow-hidden">
                        <div className="h-full bg-primary" style={{ width: `${Math.min(100, v.percentage)}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
}
