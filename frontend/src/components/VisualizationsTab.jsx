import React from 'react';
import { motion } from 'framer-motion';
import { BarChart2, PieChart, Sparkles, TrendingUp, HelpCircle } from 'lucide-react';
import ChartRenderer from './ChartRenderer';

export default function VisualizationsTab({ report }) {
  if (!report) return null;

  const charts = report.charts?.charts || [];
  const emptyReason = report.charts?.empty_reason;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-8 w-full"
    >
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-3xl bg-white border border-[#CEAB93]/50 shadow-glass">
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-[#AD8B73] to-[#3E2723] text-white flex items-center justify-center shadow-md shadow-[#AD8B73]/20">
            <TrendingUp className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg md:text-xl font-extrabold text-[#3E2723] tracking-tight font-display">
              Data-Driven Visual Insights
            </h3>
            <p className="text-xs text-[#7D5A44] font-medium">
              Dynamically selected and compiled based on empirical dataset properties and distributions
            </p>
          </div>
        </div>
        <span className="self-start sm:self-auto text-xs text-[#3E2723] font-mono font-bold px-3.5 py-1.5 rounded-full bg-[#AD8B73]/15 border border-[#CEAB93]/60 shadow-xs">
          {charts.length} {charts.length === 1 ? 'Visual Compiled' : 'Visuals Compiled'}
        </span>
      </div>

      {/* Empty State vs Single-Column Multi-Row Layout */}
      {charts.length === 0 ? (
        <div className="glass-card p-12 rounded-3xl text-center text-xs text-[#7D5A44] space-y-3 border border-[#CEAB93]/50">
          <PieChart className="w-12 h-12 mx-auto text-[#AD8B73]/80 animate-pulse" />
          <h4 className="text-sm font-bold text-[#3E2723]">No Meaningful Visualizations Identified</h4>
          <p className="max-w-md mx-auto text-xs leading-relaxed text-[#7D5A44]">
            {emptyReason || 'The dataset structure contains insufficient variance, non-null numerical measures, or categorical distributions for a meaningful visual chart.'}
          </p>
        </div>
      ) : (
        <div className="flex flex-col space-y-8">
          {charts.map((spec, index) => (
            <React.Fragment key={spec.id || index}>
              <div className="glass-card rounded-3xl p-6 md:p-8 shadow-glass border border-[#CEAB93]/50 hover:border-[#AD8B73] transition-all bg-white">
                <ChartRenderer spec={spec} />
              </div>
              {index < charts.length - 1 && (
                <div className="relative py-1">
                  <div className="absolute inset-0 flex items-center" aria-hidden="true">
                    <div className="w-full border-t border-[#CEAB93]/30" />
                  </div>
                  <div className="relative flex justify-center">
                    <span className="bg-[#FFFBE9] px-3 text-[11px] font-mono text-[#AD8B73] uppercase tracking-wider font-semibold">
                      Visual Analysis #{index + 2}
                    </span>
                  </div>
                </div>
              )}
            </React.Fragment>
          ))}
        </div>
      )}
    </motion.div>
  );
}
