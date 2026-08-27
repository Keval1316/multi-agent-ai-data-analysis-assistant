import React from 'react';
import { motion } from 'framer-motion';
import {
  Lightbulb,
  ShieldCheck,
  TrendingUp,
  AlertCircle,
  PieChart,
  Sparkles
} from 'lucide-react';

export default function InsightsTab({ report }) {
  if (!report) return null;

  const { insights, patterns } = report;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* 1. Verified Strategic Insights Grid */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Lightbulb className="w-5 h-5 text-primary" />
            <h3 className="text-lg font-bold text-text-primary tracking-tight">
              Verified Strategic Insights
            </h3>
          </div>
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-primary/10 text-primary font-mono font-semibold flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5" /> Adversarially Audited
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {insights?.insights?.map((ins) => (
            <motion.div
              key={ins.id}
              whileHover={{ y: -3 }}
              className="p-5 rounded-3xl bg-surface border border-border shadow-sm flex flex-col justify-between space-y-4"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-md bg-primary/10 text-primary border border-primary/20 font-bold">
                    {ins.category}
                  </span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-surface-accent/30 text-text-secondary border border-border">
                    {ins.importance} Priority
                  </span>
                </div>
                <h4 className="font-bold text-text-primary text-sm leading-snug">
                  {ins.title}
                </h4>
                <p className="text-xs text-text-secondary leading-relaxed">
                  {ins.finding}
                </p>
              </div>

              <div className="space-y-2.5 pt-3 border-t border-border">
                <div className="text-[11px] text-text-secondary bg-surface-accent/15 p-2.5 rounded-2xl">
                  <span className="font-semibold text-text-primary">Evidence: </span>
                  {ins.supporting_evidence}
                </div>
                {ins.recommendation && (
                  <div className="text-[11px] text-primary bg-primary/5 border border-primary/15 p-2.5 rounded-2xl">
                    <span className="font-bold text-text-primary">Action: </span>
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
        <div className="p-6 rounded-3xl bg-surface border border-border shadow-sm space-y-4">
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-4 h-4 text-primary" />
            <h4 className="font-bold text-text-primary text-sm tracking-tight">
              Empirical Pattern & Anomaly Log
            </h4>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {patterns.trends?.slice(0, 2).map((t, idx) => (
              <div key={idx} className="p-4 rounded-2xl bg-surface-accent/15 border border-border text-xs space-y-1">
                <span className="text-[10px] font-mono text-primary font-bold uppercase block">Trend ({t.direction})</span>
                <p className="text-text-secondary leading-relaxed">{t.description}</p>
              </div>
            ))}
            {patterns.concentrations?.slice(0, 2).map((c, idx) => (
              <div key={idx} className="p-4 rounded-2xl bg-surface-accent/15 border border-border text-xs space-y-1">
                <span className="text-[10px] font-mono text-primary font-bold uppercase block">Pareto Concentration</span>
                <p className="text-text-secondary leading-relaxed">{c.description}</p>
              </div>
            ))}
            {patterns.anomalies?.slice(0, 2).map((a, idx) => (
              <div key={idx} className="p-4 rounded-2xl bg-surface-accent/15 border border-border text-xs space-y-1">
                <span className="text-[10px] font-mono text-red-600 font-bold uppercase block">Anomaly ({a.row_identifier})</span>
                <p className="text-text-secondary leading-relaxed">{a.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
}
