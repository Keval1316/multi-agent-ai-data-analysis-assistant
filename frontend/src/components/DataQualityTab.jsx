import React from 'react';
import { motion } from 'framer-motion';
import {
  ShieldAlert,
  AlertTriangle,
  Info,
  CheckCircle,
  Columns,
  Sparkles,
  Award,
  ShieldCheck,
  CheckCircle2
} from 'lucide-react';

export default function DataQualityTab({ report }) {
  if (!report) return null;

  const { quality, profile } = report;

  const getSeverityBadge = (severity) => {
    switch (severity) {
      case 'confirmed_issue':
        return (
          <span className="px-2.5 py-1 rounded-xl text-[10px] font-bold uppercase bg-red-100 text-red-700 border border-red-200">
            Confirmed Issue
          </span>
        );
      case 'suspicious_issue':
        return (
          <span className="px-2.5 py-1 rounded-xl text-[10px] font-bold uppercase bg-amber-100 text-amber-800 border border-amber-200">
            Suspicious
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-1 rounded-xl text-[10px] font-bold uppercase bg-emerald-100 text-emerald-800 border border-emerald-200">
            Observation
          </span>
        );
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      {/* 1. Quality Scorecards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="glass-card p-6 rounded-3xl flex flex-col justify-between shadow-glass border border-[#CEAB93]/50">
          <span className="text-xs font-mono uppercase text-[#7D5A44] font-bold">Data Quality Cleanliness</span>
          <div className="flex items-baseline space-x-2.5 my-3">
            <span className="text-5xl font-black text-[#3E2723] font-mono">{quality?.quality_score || 100}</span>
            <span className="text-sm text-[#7D5A44] font-bold font-mono">/ 100</span>
          </div>
          <div className="text-xs text-[#7D5A44] font-medium">
            Assigned Grade: <b className="text-[#3E2723] font-extrabold font-display">Grade {quality?.grade || 'A'}</b>
          </div>
        </div>

        <div className="glass-card p-6 rounded-3xl flex flex-col justify-between shadow-glass border border-[#CEAB93]/50">
          <span className="text-xs font-mono uppercase text-[#7D5A44] font-bold">Analysis Readiness</span>
          <div className="my-3">
            <span className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full text-xs font-bold bg-[#AD8B73]/15 text-[#3E2723] border border-[#CEAB93]/60 shadow-sm">
              <CheckCircle2 className="w-4 h-4 text-[#AD8B73]" />
              <span>{quality?.is_analysis_ready ? 'Analysis Ready' : 'Requires Attention'}</span>
            </span>
          </div>
          <span className="text-xs text-[#7D5A44] font-medium leading-relaxed">
            {quality?.summary || 'Standard data cleanliness verified across variables.'}
          </span>
        </div>

        <div className="glass-card p-6 rounded-3xl flex flex-col justify-between shadow-glass border border-[#CEAB93]/50">
          <span className="text-xs font-mono uppercase text-[#7D5A44] font-bold">Audit Observations</span>
          <div className="text-4xl font-black text-[#3E2723] my-3 font-mono">
            {quality?.issues?.length || 0}
          </div>
          <span className="text-xs text-[#7D5A44] font-medium">
            {quality?.issues?.filter(i => i.severity === 'confirmed_issue').length || 0} confirmed, {quality?.issues?.filter(i => i.severity === 'suspicious_issue').length || 0} suspicious
          </span>
        </div>
      </div>

      {/* 2. Audit Issues List */}
      {quality?.issues?.length > 0 && (
        <div className="glass-card p-6 md:p-8 rounded-3xl space-y-4 shadow-glass border border-[#CEAB93]/50">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-xl bg-[#AD8B73]/15 text-[#3E2723] flex items-center justify-center">
              <ShieldAlert className="w-5 h-5 text-[#AD8B73]" />
            </div>
            <h4 className="font-extrabold text-[#3E2723] text-sm md:text-base tracking-tight font-display">
              Data Quality Audit Findings
            </h4>
          </div>

          <div className="space-y-3">
            {quality.issues.map((issue, idx) => {
              const issueTitle =
                issue.title ||
                (issue.category || issue.issue_type || 'Data Quality Finding')
                  .toString()
                  .replace(/_/g, ' ')
                  .toUpperCase();
              const action = issue.suggested_action || issue.recommendation;

              return (
                <div
                  key={issue.id || `issue-${idx}`}
                  className="p-4 md:p-5 rounded-2xl bg-white/80 border border-[#CEAB93]/40 flex flex-col sm:flex-row sm:items-start justify-between gap-3.5 text-xs shadow-sm hover:border-[#AD8B73] transition-colors"
                >
                  <div className="space-y-1.5 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-extrabold text-sm text-[#3E2723]">{issueTitle}</span>
                      {issue.category && (
                        <span className="font-mono text-[10px] font-bold uppercase px-2 py-0.5 rounded-md bg-[#AD8B73]/15 text-[#3E2723] border border-[#CEAB93]/60">
                          {issue.category.replace(/_/g, ' ')}
                        </span>
                      )}
                      {issue.column_name && (
                        <span className="font-mono text-[11px] font-bold px-2 py-0.5 rounded-lg bg-[#FFFBE9] border border-[#CEAB93]/60 text-[#3E2723]">
                          Variable: {issue.column_name}
                        </span>
                      )}
                    </div>
                    <p className="text-[#7D5A44] leading-relaxed font-normal">{issue.description}</p>
                    {action && (
                      <div className="text-[#3E2723] font-semibold mt-1 bg-[#AD8B73]/10 p-2.5 rounded-xl border border-[#CEAB93]/40">
                        Suggested Action: {action}
                      </div>
                    )}
                  </div>
                  <div>{getSeverityBadge(issue.severity)}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 3. Column Profiles Table */}
      {profile?.column_profiles?.length > 0 && (
        <div className="glass-card p-6 md:p-8 rounded-3xl space-y-4 shadow-glass border border-[#CEAB93]/50">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-xl bg-[#AD8B73]/15 text-[#3E2723] flex items-center justify-center">
              <Columns className="w-5 h-5 text-[#AD8B73]" />
            </div>
            <h4 className="font-extrabold text-[#3E2723] text-sm md:text-base tracking-tight font-display">
              Column Profiling & Semantic Classification
            </h4>
          </div>

          <div className="overflow-x-auto rounded-2xl border border-[#CEAB93]/40">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-[#CEAB93]/50 bg-white text-[#3E2723] uppercase tracking-wider font-mono text-[10px] font-bold">
                  <th className="py-3 px-4">Column Name</th>
                  <th className="py-3 px-4">Semantic Role</th>
                  <th className="py-3 px-4">Storage Type</th>
                  <th className="py-3 px-4">Null %</th>
                  <th className="py-3 px-4">Distinct</th>
                  <th className="py-3 px-4">Sample Values</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#CEAB93]/30 bg-white/70">
                {profile.column_profiles.map((col) => (
                  <tr key={col.name} className="hover:bg-white/95 transition-colors">
                    <td className="py-3 px-4 font-bold text-[#3E2723] font-mono">{col.name}</td>
                    <td className="py-3 px-4">
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-[#AD8B73]/15 text-[#3E2723] border border-[#CEAB93]/60 font-bold">
                        {col.semantic_type || 'unclassified'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-[#7D5A44] font-mono text-[11px]">{col.dtype}</td>
                    <td className="py-3 px-4 text-[#7D5A44] font-mono">{col.null_percentage}%</td>
                    <td className="py-3 px-4 text-[#3E2723] font-mono font-semibold">{col.unique_count?.toLocaleString() ?? 0}</td>
                    <td className="py-3 px-4 text-[#7D5A44] font-mono text-[11px] truncate max-w-xs">
                      {(col.sample_values || []).slice(0, 3).join(', ') || '—'}
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
