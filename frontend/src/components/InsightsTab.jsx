import React from 'react';
import { motion } from 'framer-motion';
import {
  Lightbulb,
  ShieldCheck,
  TrendingUp,
  AlertCircle,
  PieChart,
  Sparkles,
  ArrowUpRight,
  Zap,
  Target
} from 'lucide-react';

export default function InsightsTab({ report }) {
  if (!report) return null;

  const { insights, patterns } = report;

  const getPriorityBadge = (importance) => {
    switch (importance?.toLowerCase()) {
      case 'critical':
      case 'high':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-red-100 text-red-800 border border-red-200">
            {importance} Priority
          </span>
        );
      case 'medium':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-amber-100 text-amber-800 border border-amber-200">
            {importance} Priority
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-[#AD8B73]/15 text-[#3E2723] border border-[#CEAB93]/50">
            {importance || 'Standard'}
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
      {/* 1. Verified Strategic Insights Deck */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-xl bg-[#AD8B73]/15 text-[#3E2723] flex items-center justify-center">
              <Lightbulb className="w-5 h-5 text-[#AD8B73]" />
            </div>
            <h3 className="text-lg md:text-xl font-extrabold text-[#3E2723] tracking-tight font-display">
              Verified Strategic Insights
            </h3>
          </div>
          <span className="text-xs px-3 py-1 rounded-full bg-[#AD8B73]/15 text-[#3E2723] font-mono font-bold flex items-center gap-1.5 border border-[#CEAB93]/60 shadow-sm">
            <ShieldCheck className="w-4 h-4 text-[#AD8B73]" /> Adversarially Audited
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {insights?.insights?.map((ins) => (
            <motion.div
              key={ins.id}
              whileHover={{ y: -4 }}
              className="glass-card p-6 rounded-3xl shadow-glass border border-[#CEAB93]/50 flex flex-col justify-between space-y-4 hover:shadow-xl transition-all"
            >
              <div className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] uppercase font-mono px-2.5 py-0.5 rounded-full bg-[#AD8B73]/15 text-[#3E2723] border border-[#CEAB93]/60 font-bold">
                    {ins.category}
                  </span>
                  {getPriorityBadge(ins.importance)}
                </div>
                <h4 className="font-extrabold text-[#3E2723] text-base leading-snug font-display">
                  {ins.title}
                </h4>
                <p className="text-xs text-[#7D5A44] leading-relaxed font-normal">
                  {ins.finding}
                </p>
              </div>

              <div className="space-y-3 pt-3 border-t border-[#CEAB93]/30">
                <div className="text-[11px] text-[#3E2723] bg-[#FFFBE9]/80 p-3 rounded-2xl border border-[#CEAB93]/40 leading-relaxed">
                  <div className="flex items-center space-x-1 font-bold text-[#3E2723] mb-1">
                    <Target className="w-3 h-3 text-[#AD8B73]" />
                    <span>Supporting Evidence</span>
                  </div>
                  {ins.supporting_evidence}
                </div>

                {ins.recommendation && (
                  <div className="text-[11px] text-[#3E2723] bg-white/90 border border-[#AD8B73]/40 p-3 rounded-2xl leading-relaxed shadow-sm">
                    <div className="flex items-center space-x-1 font-bold text-[#AD8B73] mb-1">
                      <Zap className="w-3.5 h-3.5 text-[#AD8B73]" />
                      <span>Recommended Action</span>
                    </div>
                    {ins.recommendation}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* 2. Detected Trends & Patterns */}
      {patterns && (patterns.trends?.length > 0 || patterns.concentrations?.length > 0 || patterns.anomalies?.length > 0) && (
        <div className="glass-card p-6 md:p-8 rounded-3xl space-y-4 shadow-glass border border-[#CEAB93]/50">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-xl bg-[#AD8B73]/15 text-[#3E2723] flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-[#AD8B73]" />
            </div>
            <h4 className="font-extrabold text-[#3E2723] text-sm md:text-base tracking-tight font-display">
              Empirical Pattern & Anomaly Log
            </h4>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {patterns.trends?.slice(0, 2).map((t, idx) => (
              <div key={idx} className="p-4 rounded-2xl bg-white/80 border border-[#CEAB93]/40 text-xs space-y-1.5 shadow-sm">
                <span className="text-[10px] font-mono text-[#AD8B73] font-bold uppercase block">Trend ({t.direction})</span>
                <p className="text-[#7D5A44] leading-relaxed font-medium">{t.description}</p>
              </div>
            ))}
            {patterns.concentrations?.slice(0, 2).map((c, idx) => (
              <div key={idx} className="p-4 rounded-2xl bg-white/80 border border-[#CEAB93]/40 text-xs space-y-1.5 shadow-sm">
                <span className="text-[10px] font-mono text-[#AD8B73] font-bold uppercase block">Pareto Concentration</span>
                <p className="text-[#7D5A44] leading-relaxed font-medium">{c.description}</p>
              </div>
            ))}
            {patterns.anomalies?.slice(0, 2).map((a, idx) => (
              <div key={idx} className="p-4 rounded-2xl bg-red-50/70 border border-red-200 text-xs space-y-1.5 shadow-sm">
                <span className="text-[10px] font-mono text-red-700 font-bold uppercase block">Anomaly ({a.row_identifier})</span>
                <p className="text-[#7D5A44] leading-relaxed font-medium">{a.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
}
