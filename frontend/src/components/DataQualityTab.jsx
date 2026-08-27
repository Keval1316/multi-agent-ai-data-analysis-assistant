import React from 'react';
import { motion } from 'framer-motion';
import {
  ShieldAlert,
  AlertTriangle,
  Info,
  CheckCircle,
  Columns,
  Sparkles
} from 'lucide-react';

export default function DataQualityTab({ report }) {
  if (!report) return null;

  const { quality, profile } = report;

  const getSeverityBadge = (severity) => {
    switch (severity) {
      case 'confirmed_issue':
        return (
          <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase bg-red-100 text-red-700 border border-red-200">
            Confirmed Issue
          </span>
        );
      case 'suspicious_issue':
        return (
          <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase bg-amber-100 text-amber-700 border border-amber-200">
            Suspicious
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase bg-blue-50 text-blue-700 border border-blue-200">
            Observation
          </span>
        );
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* 1. Quality Scorecard */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="p-6 rounded-3xl bg-surface border border-border flex flex-col justify-between">
          <span className="text-xs font-mono uppercase text-text-secondary font-semibold">Data Quality Score</span>
          <div className="flex items-baseline space-x-2 my-2">
            <span className="text-4xl font-extrabold text-primary">{quality?.quality_score || 100}</span>
            <span className="text-sm text-text-secondary font-semibold">/ 100</span>
          </div>
          <span className="text-xs text-text-secondary">Assigned Quality Grade: <b className="text-text-primary">Grade {quality?.grade || 'A'}</b></span>
        </div>

        <div className="p-6 rounded-3xl bg-surface border border-border flex flex-col justify-between">
          <span className="text-xs font-mono uppercase text-text-secondary font-semibold">Quality Assessment</span>
          <div className="my-2">
            <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-primary/10 text-primary border border-primary/20">
              <CheckCircle className="w-3.5 h-3.5" />
              <span>{quality?.is_analysis_ready ? 'Analysis Ready' : 'Requires Attention'}</span>
            </span>
          </div>
          <span className="text-xs text-text-secondary">{quality?.summary || 'Standard data cleanliness verified.'}</span>
        </div>

        <div className="p-6 rounded-3xl bg-surface border border-border flex flex-col justify-between">
          <span className="text-xs font-mono uppercase text-text-secondary font-semibold">Issues Detected</span>
          <div className="text-3xl font-extrabold text-text-primary my-2">
            {quality?.issues?.length || 0}
          </div>
          <span className="text-xs text-text-secondary">
            {quality?.issues?.filter(i => i.severity === 'confirmed_issue').length || 0} confirmed, {quality?.issues?.filter(i => i.severity === 'suspicious_issue').length || 0} suspicious
          </span>
        </div>
      </div>

      {/* 2. Audit Issues List */}
      {quality?.issues?.length > 0 && (
        <div className="p-6 rounded-3xl bg-surface border border-border shadow-sm space-y-4">
          <div className="flex items-center space-x-2">
            <ShieldAlert className="w-4 h-4 text-primary" />
            <h4 className="font-bold text-text-primary text-sm tracking-tight">
              Data Quality Audit Findings
            </h4>
          </div>

          <div className="space-y-2.5">
            {quality.issues.map((issue) => (
              <div
                key={issue.id}
                className="p-4 rounded-2xl bg-surface-accent/15 border border-border flex flex-col sm:flex-row sm:items-start justify-between gap-3 text-xs"
              >
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-text-primary">{issue.issue_type.replace('_', ' ').toUpperCase()}</span>
                    {issue.column_name && (
                      <span className="font-mono text-[10px] px-1.5 py-0.2 rounded bg-surface border border-border text-text-secondary">
                        Column: {issue.column_name}
                      </span>
                    )}
                  </div>
                  <p className="text-text-secondary leading-relaxed">{issue.description}</p>
                  {issue.recommendation && (
                    <p className="text-primary font-medium mt-1">Recommendation: {issue.recommendation}</p>
                  )}
                </div>
                <div>{getSeverityBadge(issue.severity)}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 3. Column Profiles & Semantic Types Table */}
      {profile?.column_profiles?.length > 0 && (
        <div className="p-6 rounded-3xl bg-surface border border-border shadow-sm space-y-4">
          <div className="flex items-center space-x-2">
            <Columns className="w-4 h-4 text-primary" />
            <h4 className="font-bold text-text-primary text-sm tracking-tight">
              Column Profiling & Semantic Classification
            </h4>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-border bg-surface-accent/20 text-text-secondary uppercase tracking-wider font-mono text-[10px]">
                  <th className="py-2.5 px-3">Column</th>
                  <th className="py-2.5 px-3">Semantic Type</th>
                  <th className="py-2.5 px-3">Data Type</th>
                  <th className="py-2.5 px-3">Null %</th>
                  <th className="py-2.5 px-3">Unique</th>
                  <th className="py-2.5 px-3">Sample Values</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {profile.column_profiles.map((col) => (
                  <tr key={col.name} className="hover:bg-surface-accent/10 transition-colors">
                    <td className="py-2.5 px-3 font-semibold text-text-primary font-mono">{col.name}</td>
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-primary/10 text-primary border border-primary/20 font-semibold">
                        {col.semantic_type}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-text-secondary font-mono text-[11px]">{col.dtype}</td>
                    <td className="py-2.5 px-3 text-text-secondary">{col.null_percentage}%</td>
                    <td className="py-2.5 px-3 text-text-secondary">{col.unique_count.toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-text-secondary font-mono text-[11px] truncate max-w-xs">
                      {col.sample_values.slice(0, 3).join(', ') || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </motion.div>
  );
}
