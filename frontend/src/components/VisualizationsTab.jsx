import React from 'react';
import { motion } from 'framer-motion';
import { BarChart2, Info } from 'lucide-react';
import ChartRenderer from './ChartRenderer';

export default function VisualizationsTab({ report }) {
  if (!report) return null;

  const charts = report.charts?.charts || [];

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <BarChart2 className="w-5 h-5 text-primary" />
          <h3 className="text-lg font-bold text-text-primary tracking-tight">
            Interactive Plotly Visualizations
          </h3>
        </div>
        <span className="text-xs text-text-secondary font-mono">
          {charts.length} Charts Generated
        </span>
      </div>

      {charts.length === 0 ? (
        <div className="p-8 rounded-3xl bg-surface border border-border text-center text-xs text-text-secondary">
          No visualizations generated for this dataset structure.
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {charts.map((spec) => (
            <ChartRenderer key={spec.id} spec={spec} />
          ))}
        </div>
      )}
    </motion.div>
  );
}
