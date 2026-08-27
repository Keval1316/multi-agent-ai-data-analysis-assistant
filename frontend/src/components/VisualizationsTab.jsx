import React from 'react';
import { motion } from 'framer-motion';
import { BarChart2, Info, PieChart, Sparkles } from 'lucide-react';
import ChartRenderer from './ChartRenderer';

export default function VisualizationsTab({ report }) {
  if (!report) return null;

  const charts = report.charts?.charts || [];

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-xl bg-[#AD8B73]/15 text-[#3E2723] flex items-center justify-center">
            <BarChart2 className="w-5 h-5 text-[#AD8B73]" />
          </div>
          <h3 className="text-lg md:text-xl font-extrabold text-[#3E2723] tracking-tight font-display">
            Interactive Plotly Visualizations
          </h3>
        </div>
        <span className="text-xs text-[#7D5A44] font-mono font-bold px-3 py-1 rounded-full bg-white border border-[#CEAB93]/50 shadow-sm">
          {charts.length} Charts Compiled
        </span>
      </div>

      {charts.length === 0 ? (
        <div className="glass-card p-12 rounded-3xl text-center text-xs text-[#7D5A44] space-y-2 border border-[#CEAB93]/50">
          <PieChart className="w-10 h-10 mx-auto text-[#AD8B73]" />
          <p className="font-semibold">No visualizations generated for this dataset structure.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {charts.map((spec) => (
            <div key={spec.id} className="glass-card rounded-3xl p-5 md:p-6 shadow-glass border border-[#CEAB93]/50 hover:shadow-xl transition-all">
              <ChartRenderer spec={spec} />
            </div>
          ))}
        </div>
      )}
    </motion.div>
  );
}
