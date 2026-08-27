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
  TrendingUp,
  Table,
  Hash,
  Award,
  FileCheck2,
  AlertTriangle
} from 'lucide-react';

export default function OverviewTab({ report }) {
  if (!report) return null;

  const { understanding, profile, quality, insights } = report;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
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

      {/* 2. Executive Synthesis Callout */}
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

      {/* 3. Core Strategic Questions Answered */}
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
