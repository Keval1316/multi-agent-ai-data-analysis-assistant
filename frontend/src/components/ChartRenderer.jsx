import React, { useEffect, useRef } from 'react';
import Plotly from 'plotly.js-dist-min';
import { motion } from 'framer-motion';
import { BarChart3, LineChart, PieChart, ScatterChart, Info, Layers } from 'lucide-react';

export default function ChartRenderer({ spec }) {
  const chartContainerRef = useRef(null);

  useEffect(() => {
    if (!chartContainerRef.current || !spec) return;

    const data = spec.data || [];
    const layout = {
      ...spec.layout,
      autosize: true,
      responsive: true,
    };
    const config = {
      responsive: true,
      displayModeBar: true,
      displaylogo: false,
      modeBarButtonsToRemove: ['lasso2d', 'select2d'],
      ...spec.config,
    };

    Plotly.newPlot(chartContainerRef.current, data, layout, config);

    const handleResize = () => {
      if (chartContainerRef.current) {
        Plotly.Plots.resize(chartContainerRef.current);
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartContainerRef.current) {
        Plotly.purge(chartContainerRef.current);
      }
    };
  }, [spec]);

  if (!spec) return null;

  const getChartIcon = (type) => {
    switch (type) {
      case 'line':
        return <LineChart className="w-4 h-4" />;
      case 'donut':
      case 'pie':
        return <PieChart className="w-4 h-4" />;
      case 'scatter':
        return <ScatterChart className="w-4 h-4" />;
      default:
        return <BarChart3 className="w-4 h-4" />;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col space-y-4 w-full"
    >
      {/* Top Title & Metadata Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#CEAB93]/30 pb-4">
        <div className="flex items-start sm:items-center space-x-3">
          <div className="w-8 h-8 rounded-xl bg-[#AD8B73]/15 border border-[#CEAB93]/60 flex items-center justify-center text-[#AD8B73] shrink-0 mt-0.5 sm:mt-0">
            {getChartIcon(spec.chart_type)}
          </div>
          <div>
            <h4 className="font-extrabold text-[#3E2723] text-base md:text-lg tracking-tight font-display">
              {spec.title}
            </h4>
            {spec.subtitle && (
              <p className="text-xs text-[#7D5A44] leading-relaxed mt-0.5">{spec.subtitle}</p>
            )}
          </div>
        </div>

        {/* Metadata Badges */}
        <div className="flex items-center space-x-2 self-start sm:self-auto shrink-0">
          {spec.x_column && (
            <span className="text-[10px] font-mono px-2.5 py-1 rounded-full bg-[#AD8B73]/10 text-[#3E2723] border border-[#CEAB93]/40 font-medium">
              X: {spec.x_column}
            </span>
          )}
          {spec.aggregation && (
            <span className="text-[10px] font-mono uppercase px-2.5 py-1 rounded-full bg-[#E3CAA5]/30 text-[#3E2723] border border-[#CEAB93]/50 font-bold">
              {spec.aggregation}
            </span>
          )}
          <span className="text-[10px] font-mono uppercase px-2.5 py-1 rounded-full bg-[#AD8B73]/20 text-[#3E2723] border border-[#CEAB93]/60 font-bold">
            {spec.chart_type?.replace('_', ' ')}
          </span>
        </div>
      </div>

      {/* Plotly Canvas Container - Full Width */}
      <div ref={chartContainerRef} className="w-full h-80 sm:h-96 min-h-[340px]" />

      {/* Data-Driven Insight Takeaway Box */}
      {spec.insights_summary && (
        <div className="mt-2 p-4 rounded-2xl bg-[#FFFBE9] border border-[#CEAB93]/60 flex items-start space-x-3 text-xs text-[#3E2723] shadow-xs">
          <div className="w-5 h-5 rounded-lg bg-[#AD8B73] text-white flex items-center justify-center shrink-0 mt-0.5">
            <Info className="w-3.5 h-3.5" />
          </div>
          <div className="space-y-0.5">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#AD8B73] block font-mono">
              Key Insight / Takeaway
            </span>
            <p className="text-xs leading-relaxed text-[#3E2723] font-medium">
              {spec.insights_summary}
            </p>
          </div>
        </div>
      )}
    </motion.div>
  );
}
