import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  FileText,
  Download,
  Copy,
  Check,
  Loader2,
  AlertTriangle
} from 'lucide-react';

export default function ReportMarkdownTab({ report, datasetId }) {
  const [downloading, setDownloading] = useState(false);
  const [copied, setCopied] = useState(false);
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
        throw new Error(`Failed to download PDF (${res.status} ${res.statusText})`);
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

  const handleCopyMarkdown = () => {
    if (report.markdown_report) {
      navigator.clipboard.writeText(report.markdown_report);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Action Bar */}
      <div className="p-6 rounded-3xl bg-surface border border-border shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="font-bold text-text-primary text-base">
            Executive Report Document
          </h3>
          <p className="text-xs text-text-secondary">
            Generated on {report.generated_at} • {report.filename}
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleCopyMarkdown}
            className="flex items-center space-x-1.5 px-4 py-2.5 rounded-2xl bg-surface-accent/20 border border-border text-text-primary text-xs font-semibold hover:bg-surface-accent/40 transition-colors cursor-pointer"
          >
            {copied ? <Check className="w-4 h-4 text-primary" /> : <Copy className="w-4 h-4" />}
            <span>{copied ? 'Copied!' : 'Copy Markdown'}</span>
          </button>

          <button
            onClick={handleDownloadPDF}
            disabled={downloading}
            className="flex items-center space-x-2 px-5 py-2.5 rounded-2xl bg-primary text-white text-xs font-semibold hover:bg-primary-hover transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            {downloading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Rendering PDF...</span>
              </>
            ) : (
              <>
                <Download className="w-4 h-4" />
                <span>Download PDF</span>
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

      {/* Structured Sections */}
      <div className="p-6 md:p-8 rounded-3xl bg-surface border border-border shadow-sm space-y-6 text-text-primary">
        {report.sections?.map((sec) => (
          <div key={sec.id} className="space-y-2 pb-6 border-b border-border last:border-none last:pb-0">
            <h4 className="text-base font-bold text-text-primary">
              {sec.title}
            </h4>
            <p className="text-xs text-text-secondary italic mb-2">
              {sec.summary}
            </p>
            <div className="text-xs md:text-sm text-text-primary leading-relaxed whitespace-pre-line bg-surface-accent/10 p-4 rounded-2xl border border-border/40 font-sans">
              {sec.markdown_content}
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
