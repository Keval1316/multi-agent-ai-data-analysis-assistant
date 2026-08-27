import React, { useEffect, useRef } from 'react';
import Plotly from 'plotly.js-dist-min';
import { motion } from 'framer-motion';
import { BarChart3, Info } from 'lucide-react';

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

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-5 rounded-3xl bg-surface border border-border shadow-sm flex flex-col justify-between"
    >
      <div>
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center space-x-2">
            <div className="w-7 h-7 rounded-lg bg-surface-accent/20 border border-border flex items-center justify-center text-primary">
              <BarChart3 className="w-4 h-4" />
            </div>
            <h4 className="font-bold text-text-primary text-sm tracking-tight">{spec.title}</h4>
          </div>
          <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-md bg-surface-accent/30 text-text-primary border border-border font-semibold">
            {spec.chart_type}
          </span>
        </div>

        {spec.subtitle && (
          <p className="text-xs text-text-secondary ml-9 mb-3 leading-tight">{spec.subtitle}</p>
        )}

        {/* Plotly Canvas Container */}
        <div ref={chartContainerRef} className="w-full h-72 min-h-[280px]" />
      </div>

      {spec.insights_summary && (
        <div className="mt-3 pt-3 border-t border-border flex items-start space-x-2 text-xs text-text-secondary bg-surface-accent/10 p-2.5 rounded-2xl">
          <Info className="w-3.5 h-3.5 text-primary mt-0.5 flex-shrink-0" />
          <span className="text-[11px] leading-relaxed"><b className="text-text-primary font-semibold">Takeaway: </b>{spec.insights_summary}</span>
        </div>
      )}
    </motion.div>
  );
}
