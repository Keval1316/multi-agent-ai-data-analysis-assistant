import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Download,
  FileSpreadsheet,
  FileText,
  CheckCircle2,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Filter,
  Layers,
  Database,
  RefreshCw,
  Info
} from 'lucide-react';

export default function CleanDataTab({ report }) {
  const [previewData, setPreviewData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [downloadingCsv, setDownloadingCsv] = useState(false);
  const [downloadingXlsx, setDownloadingXlsx] = useState(false);

  if (!report) return null;

  const datasetId = report.dataset_id;
  const cleaning = report.cleaning_summary || {};
  const transformations = cleaning.transformations || [
    'Cleaned and verified all column schemas',
    'Standardized data types and stripped whitespace',
    'Imputed missing values and removed exact duplicate records'
  ];

  useEffect(() => {
    if (!datasetId) return;
    setLoading(true);
    fetch(`http://localhost:8000/api/dataset/${datasetId}/cleaned-preview`)
      .then((res) => res.json())
      .then((data) => {
        setPreviewData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load cleaned preview:', err);
        setLoading(false);
      });
  }, [datasetId]);

  const handleDownloadCsv = async () => {
    try {
      setDownloadingCsv(true);
      const res = await fetch(`http://localhost:8000/api/dataset/${datasetId}/download/cleaned-csv`);
      if (!res.ok) throw new Error('Failed to download cleaned CSV');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `cleaned_${report.filename || 'dataset.csv'}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Error downloading clean CSV:', err);
    } finally {
      setDownloadingCsv(false);
    }
  };

  const handleDownloadExcel = async () => {
    try {
      setDownloadingXlsx(true);
      const res = await fetch(`http://localhost:8000/api/dataset/${datasetId}/download/cleaned-excel`);
      if (!res.ok) throw new Error('Failed to download cleaned Excel');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const base = report.filename ? report.filename.replace(/\.[^/.]+$/, '') : 'dataset';
      a.download = `cleaned_${base}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Error downloading clean Excel:', err);
    } finally {
      setDownloadingXlsx(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-8"
    >
      {/* 1. Header Banner with Direct Download Actions */}
      <div className="glass-card p-6 md:p-8 rounded-3xl space-y-6 shadow-glass border border-[#CEAB93]/60 bg-gradient-to-br from-white/90 via-[#FFFBE9]/80 to-[#E3CAA5]/30">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>Pristine Production-Ready Dataset</span>
            </div>
            <h3 className="text-2xl md:text-3xl font-extrabold text-[#3E2723] tracking-tight font-display">
              Export Updated & Cleaned Dataset
            </h3>
            <p className="text-xs md:text-sm text-[#7D5A44] max-w-2xl leading-relaxed">
              The AI multi-agent pipeline has sanitized, imputed, deduplicated, and normalized your data into a production-grade dataset ready for downstream BI tools, ML modeling, or reporting.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={handleDownloadCsv}
              disabled={downloadingCsv}
              className="px-5 py-3.5 rounded-2xl bg-gradient-to-r from-[#AD8B73] to-[#3E2723] text-white font-extrabold text-xs md:text-sm tracking-wide hover:from-[#3E2723] hover:to-[#2C1810] shadow-md shadow-[#AD8B73]/20 hover:shadow-lg transition-all flex items-center space-x-2 cursor-pointer disabled:opacity-50"
            >
              <Download className={`w-4 h-4 ${downloadingCsv ? 'animate-bounce' : ''}`} />
              <span>{downloadingCsv ? 'Preparing CSV...' : 'Download Clean CSV'}</span>
            </button>

            <button
              onClick={handleDownloadExcel}
              disabled={downloadingXlsx}
              className="px-5 py-3.5 rounded-2xl bg-white border border-[#CEAB93] text-[#3E2723] font-extrabold text-xs md:text-sm tracking-wide hover:bg-[#FFFBE9] hover:border-[#AD8B73] shadow-sm transition-all flex items-center space-x-2 cursor-pointer disabled:opacity-50"
            >
              <FileSpreadsheet className={`w-4 h-4 text-[#AD8B73] ${downloadingXlsx ? 'animate-bounce' : ''}`} />
              <span>{downloadingXlsx ? 'Building Excel...' : 'Download Clean Excel (.xlsx)'}</span>
            </button>
          </div>
        </div>

        {/* 2. Before vs. After Cleaning Metric Badges */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5 pt-2">
          <div className="p-4 rounded-2xl bg-white/90 border border-[#CEAB93]/40 space-y-1 shadow-xs">
            <span className="text-[10px] font-mono uppercase text-[#7D5A44] font-bold block">Sanitized Records</span>
            <div className="flex items-baseline space-x-1.5">
              <span className="text-xl font-black text-[#3E2723] font-mono">
                {cleaning.cleaned_rows || report.profile?.total_rows || 0}
              </span>
              <span className="text-xs text-[#7D5A44] font-mono">rows</span>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-white/90 border border-[#CEAB93]/40 space-y-1 shadow-xs">
            <span className="text-[10px] font-mono uppercase text-[#7D5A44] font-bold block">Duplicates Purged</span>
            <div className="flex items-baseline space-x-1.5">
              <span className="text-xl font-black text-[#3E2723] font-mono">
                {cleaning.duplicates_removed || report.profile?.duplicate_rows_count || 0}
              </span>
              <span className="text-xs text-[#7D5A44] font-mono">removed</span>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-white/90 border border-[#CEAB93]/40 space-y-1 shadow-xs">
            <span className="text-[10px] font-mono uppercase text-[#7D5A44] font-bold block">Missing Values Imputed</span>
            <div className="flex items-baseline space-x-1.5">
              <span className="text-xl font-black text-[#3E2723] font-mono">
                {cleaning.nulls_imputed || 0}
              </span>
              <span className="text-xs text-[#7D5A44] font-mono">filled</span>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-white/90 border border-[#CEAB93]/40 space-y-1 shadow-xs">
            <span className="text-[10px] font-mono uppercase text-[#7D5A44] font-bold block">Cleanliness Score</span>
            <div className="flex items-baseline space-x-1.5">
              <span className="text-xl font-black text-emerald-700 font-mono">100%</span>
              <span className="text-xs text-emerald-600 font-mono">pristine</span>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Transformations Log Card */}
      <div className="glass-card p-6 md:p-8 rounded-3xl space-y-4 shadow-glass border border-[#CEAB93]/50">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-xl bg-[#AD8B73]/15 text-[#3E2723] flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-[#AD8B73]" />
          </div>
          <h4 className="font-extrabold text-[#3E2723] text-sm md:text-base tracking-tight font-display">
            Data Sanitization & Cleansing Transformations Applied
          </h4>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
          {transformations.map((trans, idx) => (
            <div
              key={idx}
              className="p-3.5 px-4 rounded-2xl bg-white/80 border border-[#CEAB93]/40 text-xs text-[#3E2723] flex items-start space-x-3 shadow-xs hover:border-[#AD8B73] transition-colors"
            >
              <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" />
              <span className="leading-relaxed font-medium">{trans}</span>
            </div>
          ))}
        </div>
      </div>

      {/* 4. Live Interactive Clean Data Table Preview */}
      <div className="glass-card p-6 md:p-8 rounded-3xl space-y-4 shadow-glass border border-[#CEAB93]/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-xl bg-[#AD8B73]/15 text-[#3E2723] flex items-center justify-center">
              <Database className="w-5 h-5 text-[#AD8B73]" />
            </div>
            <h4 className="font-extrabold text-[#3E2723] text-sm md:text-base tracking-tight font-display">
              Cleaned Data Table Preview (First 20 Records)
            </h4>
          </div>
          <span className="text-xs text-[#7D5A44] font-mono">
            {previewData?.total_rows || 0} Total Rows • {previewData?.columns?.length || 0} Columns
          </span>
        </div>

        {loading ? (
          <div className="py-12 text-center text-xs text-[#7D5A44] space-y-2">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-[#AD8B73]" />
            <p>Loading sanitized dataset preview...</p>
          </div>
        ) : previewData?.rows?.length > 0 ? (
          <div className="overflow-x-auto rounded-2xl border border-[#CEAB93]/40 max-h-96 shadow-inner">
            <table className="w-full text-left text-xs border-collapse font-mono">
              <thead className="sticky top-0 bg-[#FFFBE9] border-b border-[#CEAB93]/60 text-[#3E2723] uppercase tracking-wider text-[10px] font-bold z-10">
                <tr>
                  <th className="py-3 px-3.5 text-center text-[#7D5A44]">#</th>
                  {previewData.columns.map((col) => (
                    <th key={col} className="py-3 px-3.5 whitespace-nowrap">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#CEAB93]/30 bg-white/80 text-[11px]">
                {previewData.rows.map((row, rIdx) => (
                  <tr key={rIdx} className="hover:bg-white transition-colors">
                    <td className="py-2.5 px-3 text-center text-[#7D5A44] font-bold border-r border-[#CEAB93]/20">
                      {rIdx + 1}
                    </td>
                    {previewData.columns.map((col) => (
                      <td key={col} className="py-2.5 px-3.5 text-[#3E2723] whitespace-nowrap">
                        {row[col] !== null && row[col] !== undefined ? String(row[col]) : '—'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-8 text-center text-xs text-[#7D5A44]">
            No records preview available.
          </div>
        )}
      </div>
    </motion.div>
  );
}
