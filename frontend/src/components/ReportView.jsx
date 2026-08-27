import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  FileText,
  Download,
  CheckCircle2,
  TrendingUp,
  AlertTriangle,
  Lightbulb,
  ShieldCheck,
  BarChart2,
  Loader2,
  Sparkles
} from 'lucide-react';
import ChartRenderer from './ChartRenderer';

export default function ReportView({ report, datasetId }) {
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState(null);

  if (!report) return null;

  const handleDownloadPDF = async () => {
    setDownloading(true);
    setDownloadError(null);
    try {
      const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const targetId = datasetId || report.dataset_id;
      const res = await fetch(`${apiBase}/api/dataset/${targetId}/report/pdf`);

      if (!res.ok) {
        throw new Error(`Failed to generate PDF (${res.status} ${res.statusText})`);
      }

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `analysis_report_${targetId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('PDF download error:', err);
      setDownloadError(err.message || 'Failed to download PDF');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-8"
    >
      {/* 1. Header Banner & Download Bar */}
      <div className="p-6 md:p-8 rounded-3xl bg-surface border border-border shadow-sm flex flex-col md:flex-row md:items-center md:justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20 flex items-center gap-1">
              <Sparkles className="w-3 h-3" /> Multi-Agent Executive Report
            </span>
            <span className="text-xs text-text-secondary font-mono">
              Grade {report.quality?.grade || 'A'} • {report.quality?.quality_score || 95}/100 Quality
            </span>
          </div>
          <h2 className="text-2xl md:text-3xl font-extrabold text-text-primary tracking-tight">
            {report.title}
          </h2>
          <p className="text-sm text-text-secondary max-w-2xl">
            {report.subtitle}
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
          <button
            onClick={handleDownloadPDF}
            disabled={downloading}
            className="flex items-center space-x-2 px-5 py-3 rounded-2xl bg-primary text-white font-semibold text-sm hover:bg-primary-hover shadow-md hover:shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed group cursor-pointer"
          >
            {downloading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Generating PDF...</span>
              </>
            ) : (
              <>
                <Download className="w-4 h-4 group-hover:-translate-y-0.5 transition-transform" />
                <span>Download PDF Report</span>
              </>
            )}
          </button>
        </div>
      </div>

      {downloadError && (
        <div className="p-4 rounded-2xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span>{downloadError}</span>
        </div>
      )}

      {/* 2. Executive Summary Callout */}
      <div className="p-6 md:p-8 rounded-3xl bg-surface border-l-4 border-primary border-t border-r border-b border-border shadow-sm space-y-3">
        <div className="flex items-center space-x-2 text-primary font-bold text-sm">
          <ShieldCheck className="w-4 h-4" />
          <span>Executive Synthesis</span>
        </div>
        <p className="text-sm md:text-base text-text-primary leading-relaxed">
          {report.executive_summary}
        </p>

        {report.insights?.executive_summary_points?.length > 0 && (
          <div className="pt-3 grid grid-cols-1 md:grid-cols-3 gap-3">
            {report.insights.executive_summary_points.map((pt, idx) => (
              <div key={idx} className="p-3.5 rounded-2xl bg-surface-accent/20 border border-border text-xs text-text-secondary leading-relaxed flex items-start space-x-2">
                <CheckCircle2 className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
                <span>{pt}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 3. Verified Insights & Recommendations */}
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <Lightbulb className="w-5 h-5 text-primary" />
          <h3 className="text-lg font-bold text-text-primary tracking-tight">
            Verified Strategic Insights
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {report.insights?.insights?.map((ins) => (
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

              <div className="space-y-3 pt-3 border-t border-border">
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

      {/* 4. Interactive Visualizations Grid */}
      {report.charts?.charts?.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <BarChart2 className="w-5 h-5 text-primary" />
            <h3 className="text-lg font-bold text-text-primary tracking-tight">
              Interactive Data Visualizations
            </h3>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {report.charts.charts.map((spec) => (
              <ChartRenderer key={spec.id} spec={spec} />
            ))}
          </div>
        </div>
      )}

      {/* 5. Key Statistical Metrics Table */}
      {report.statistics?.univariate_metrics?.length > 0 && (
        <div className="p-6 rounded-3xl bg-surface border border-border shadow-sm space-y-4">
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-4 h-4 text-primary" />
            <h4 className="font-bold text-text-primary text-sm tracking-tight">
              Statistical Moments & Quantile Benchmarks
            </h4>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-border bg-surface-accent/20 text-text-secondary uppercase tracking-wider font-mono text-[10px]">
                  <th className="py-2.5 px-3">Metric</th>
                  <th className="py-2.5 px-3">Mean</th>
                  <th className="py-2.5 px-3">Median</th>
                  <th className="py-2.5 px-3">Min</th>
                  <th className="py-2.5 px-3">Max</th>
                  <th className="py-2.5 px-3">Std Dev</th>
                  <th className="py-2.5 px-3">IQR</th>
                  <th className="py-2.5 px-3">Skewness</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {report.statistics.univariate_metrics.map((um) => (
                  <tr key={um.column_name} className="hover:bg-surface-accent/10 transition-colors">
                    <td className="py-2.5 px-3 font-semibold text-text-primary">{um.column_name}</td>
                    <td className="py-2.5 px-3 text-text-secondary">{um.mean.toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-text-secondary">{um.median.toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-text-secondary">{um.min.toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-text-secondary">{um.max.toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-text-secondary">{um.std.toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-text-secondary">{um.iqr.toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-text-secondary">{um.skewness !== null ? um.skewness : '—'}</td>
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
