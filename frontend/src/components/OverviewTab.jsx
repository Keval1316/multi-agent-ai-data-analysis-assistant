import React from 'react';
import { motion } from 'framer-motion';
import {
  ShieldCheck,
  CheckCircle2,
  HelpCircle,
  Layers,
  Database,
  Calendar,
  Sparkles,
  TrendingUp
} from 'lucide-react';

export default function OverviewTab({ report }) {
  if (!report) return null;

  const { understanding, profile, quality, insights } = report;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* 1. Quick Stats Banner */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="p-4 rounded-2xl bg-surface border border-border">
          <span className="text-[10px] font-mono uppercase text-text-secondary block font-semibold">Total Rows</span>
          <span className="text-lg font-bold text-text-primary">{profile?.total_rows?.toLocaleString() || '0'}</span>
        </div>
        <div className="p-4 rounded-2xl bg-surface border border-border">
          <span className="text-[10px] font-mono uppercase text-text-secondary block font-semibold">Columns</span>
          <span className="text-lg font-bold text-text-primary">{profile?.total_columns || '0'}</span>
        </div>
        <div className="p-4 rounded-2xl bg-surface border border-border">
          <span className="text-[10px] font-mono uppercase text-text-secondary block font-semibold">Quality Grade</span>
          <span className="text-lg font-bold text-primary">Grade {quality?.grade || 'A'}</span>
        </div>
        <div className="p-4 rounded-2xl bg-surface border border-border">
          <span className="text-[10px] font-mono uppercase text-text-secondary block font-semibold">Quality Score</span>
          <span className="text-lg font-bold text-text-primary">{quality?.quality_score || 100}/100</span>
        </div>
        <div className="p-4 rounded-2xl bg-surface border border-border">
          <span className="text-[10px] font-mono uppercase text-text-secondary block font-semibold">Numeric KPIs</span>
          <span className="text-lg font-bold text-text-primary">{profile?.numeric_column_names?.length || '0'}</span>
        </div>
        <div className="p-4 rounded-2xl bg-surface border border-border">
          <span className="text-[10px] font-mono uppercase text-text-secondary block font-semibold">Duplicates</span>
          <span className="text-lg font-bold text-text-primary">{profile?.duplicate_rows_count || 0}</span>
        </div>
      </div>

      {/* 2. Executive Synthesis Callout */}
      <div className="p-6 md:p-8 rounded-3xl bg-surface border-l-4 border-primary border-t border-r border-b border-border shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 text-primary font-bold text-sm">
            <ShieldCheck className="w-4 h-4" />
            <span>Executive Strategic Synthesis</span>
          </div>
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-primary/10 text-primary font-mono font-semibold">
            {understanding?.domain || 'General Data Domain'}
          </span>
        </div>

        <p className="text-sm md:text-base text-text-primary leading-relaxed">
          {report.executive_summary}
        </p>

        {insights?.executive_summary_points?.length > 0 && (
          <div className="pt-3 grid grid-cols-1 md:grid-cols-3 gap-3">
            {insights.executive_summary_points.map((pt, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-2xl bg-surface-accent/20 border border-border text-xs text-text-secondary leading-relaxed flex items-start space-x-2.5"
              >
                <CheckCircle2 className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
                <span className="font-medium">{pt}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 3. Core Strategic Questions Answered */}
      {understanding?.core_questions?.length > 0 && (
        <div className="p-6 rounded-3xl bg-surface border border-border shadow-sm space-y-4">
          <div className="flex items-center space-x-2">
            <HelpCircle className="w-4 h-4 text-primary" />
            <h4 className="font-bold text-text-primary text-sm tracking-tight">
              Core Strategic Business Questions Answered
            </h4>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {understanding.core_questions.map((q, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-2xl bg-surface-accent/10 border border-border text-xs text-text-primary flex items-start space-x-3"
              >
                <span className="w-5 h-5 rounded-full bg-primary/10 text-primary font-mono text-[10px] font-bold flex items-center justify-center flex-shrink-0 mt-0.5">
                  {idx + 1}
                </span>
                <span className="leading-relaxed">{q}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
}
