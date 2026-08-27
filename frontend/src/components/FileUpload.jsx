import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  X,
  ArrowRight,
  Database,
  Columns,
  Hash,
  Loader2,
  Table as TableIcon
} from 'lucide-react';

const MAX_FILE_SIZE_MB = 10;
const ALLOWED_EXTENSIONS = ['.csv', '.xlsx', '.xls'];

export default function FileUpload({ onDatasetIngested }) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState(null);
  const [datasetMetadata, setDatasetMetadata] = useState(null);

  const fileInputRef = useRef(null);
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  const validateFile = (file) => {
    if (!file) return 'No file selected.';

    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return `Unsupported file format '${ext}'. Please upload a CSV or Excel file (${ALLOWED_EXTENSIONS.join(', ')}).`;
    }

    if (file.size === 0) {
      return 'The selected file is empty (0 bytes).';
    }

    const maxSizeBytes = MAX_FILE_SIZE_MB * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      return `File size (${(file.size / (1024 * 1024)).toFixed(2)} MB) exceeds maximum allowed size of ${MAX_FILE_SIZE_MB} MB.`;
    }

    return null;
  };

  const handleFileSelection = (file) => {
    setError(null);
    setDatasetMetadata(null);

    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
    uploadFile(file);
  };

  const uploadFile = async (file) => {
    setUploading(true);
    setUploadProgress(10);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      setUploadProgress(40);
      const response = await fetch(`${apiBaseUrl}/api/upload`, {
        method: 'POST',
        body: formData,
      });

      setUploadProgress(80);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.message || 'Failed to upload and parse dataset.');
      }

      setUploadProgress(100);
      setDatasetMetadata(data.dataset);
      if (onDatasetIngested) {
        onDatasetIngested(data.dataset);
      }
    } catch (err) {
      setError(err.message || 'An error occurred during dataset ingestion.');
      setDatasetMetadata(null);
    } finally {
      setUploading(false);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  };

  const resetSelection = () => {
    setSelectedFile(null);
    setDatasetMetadata(null);
    setError(null);
    setUploadProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      {/* Upload Box */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !uploading && fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-3xl p-10 text-center cursor-pointer transition-all duration-300 ${
          isDragging
            ? 'border-active bg-surface-accent/20 scale-[1.01]'
            : 'border-border bg-surface hover:border-primary hover:bg-surface-accent/10 shadow-sm'
        } ${uploading ? 'pointer-events-none opacity-80' : ''}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv, .xlsx, .xls"
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files.length > 0) {
              handleFileSelection(e.target.files[0]);
            }
          }}
        />

        <div className="flex flex-col items-center justify-center space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-surface-accent/30 border border-border flex items-center justify-center text-primary shadow-sm group-hover:scale-105 transition-transform">
            {uploading ? (
              <Loader2 className="w-8 h-8 text-primary animate-spin" />
            ) : (
              <UploadCloud className="w-8 h-8 text-primary" />
            )}
          </div>

          <div>
            <h3 className="text-xl font-bold text-text-primary tracking-tight">
              {uploading ? 'Processing Dataset...' : 'Upload your CSV or Excel dataset'}
            </h3>
            <p className="text-sm text-text-secondary mt-1">
              Drag & drop your file here, or <span className="font-semibold text-primary underline underline-offset-2">browse files</span>
            </p>
          </div>

          <div className="flex items-center space-x-3 text-xs text-text-secondary bg-surface-accent/20 px-4 py-1.5 rounded-full border border-border">
            <span>Supported: .CSV, .XLSX, .XLS</span>
            <span>•</span>
            <span>Max Size: {MAX_FILE_SIZE_MB} MB</span>
            <span>•</span>
            <span>Max Rows: 500k</span>
          </div>
        </div>

        {/* Upload Progress Bar */}
        {uploading && (
          <div className="mt-6 w-full max-w-md mx-auto">
            <div className="flex justify-between text-xs text-text-secondary mb-1">
              <span>Validating and ingesting into DuckDB...</span>
              <span>{uploadProgress}%</span>
            </div>
            <div className="w-full h-2 bg-surface-accent/30 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-primary"
                initial={{ width: '0%' }}
                animate={{ width: `${uploadProgress}%` }}
                transition={{ duration: 0.4 }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Error Alert */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="p-4 rounded-2xl bg-red-50 border border-red-200 text-red-700 flex items-start justify-between shadow-sm"
          >
            <div className="flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-semibold text-sm">Upload Error</p>
                <p className="text-xs text-red-600 mt-0.5 leading-relaxed">{error}</p>
              </div>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setError(null);
              }}
              className="text-red-400 hover:text-red-700 p-1"
            >
              <X className="w-4 h-4" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Ingested Dataset Summary Card */}
      <AnimatePresence>
        {datasetMetadata && (
          <motion.div
            initial={{ opacity: 0, scale: 0.98, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.98 }}
            className="rounded-3xl bg-surface border border-border p-6 shadow-sm space-y-6"
          >
            {/* Header */}
            <div className="flex items-center justify-between pb-4 border-b border-border">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-surface-accent/30 border border-border flex items-center justify-center text-primary">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-bold text-text-primary text-base flex items-center gap-2">
                    {datasetMetadata.filename}
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-surface-accent/40 text-text-primary border border-border">
                      <CheckCircle2 className="w-3.5 h-3.5 text-primary mr-1" />
                      Ready for Analysis
                    </span>
                  </h4>
                  <p className="text-xs text-text-secondary mt-0.5">
                    {(datasetMetadata.file_size_bytes / 1024).toFixed(1)} KB • Ingested table: <span className="font-mono">{datasetMetadata.table_name}</span>
                  </p>
                </div>
              </div>

              <button
                onClick={resetSelection}
                className="text-xs px-3 py-1.5 rounded-xl border border-border text-text-secondary hover:bg-surface-accent/20 transition-colors"
              >
                Change File
              </button>
            </div>

            {/* Quick Metrics */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <div className="p-4 rounded-2xl bg-surface-accent/15 border border-border">
                <div className="flex items-center space-x-2 text-text-secondary text-xs font-medium mb-1">
                  <Hash className="w-4 h-4 text-primary" />
                  <span>Total Rows</span>
                </div>
                <p className="text-2xl font-extrabold text-text-primary">
                  {datasetMetadata.row_count.toLocaleString()}
                </p>
              </div>

              <div className="p-4 rounded-2xl bg-surface-accent/15 border border-border">
                <div className="flex items-center space-x-2 text-text-secondary text-xs font-medium mb-1">
                  <Columns className="w-4 h-4 text-primary" />
                  <span>Total Columns</span>
                </div>
                <p className="text-2xl font-extrabold text-text-primary">
                  {datasetMetadata.column_count}
                </p>
              </div>

              <div className="p-4 rounded-2xl bg-surface-accent/15 border border-border col-span-2 sm:col-span-1">
                <div className="flex items-center space-x-2 text-text-secondary text-xs font-medium mb-1">
                  <Database className="w-4 h-4 text-primary" />
                  <span>Engine</span>
                </div>
                <p className="text-2xl font-extrabold text-text-primary">
                  DuckDB
                </p>
              </div>
            </div>

            {/* Schema Badges */}
            <div>
              <h5 className="text-xs font-bold text-text-secondary uppercase tracking-wider mb-2">
                Detected Schema Columns ({datasetMetadata.columns.length})
              </h5>
              <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto p-1">
                {datasetMetadata.columns.map((col, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center px-3 py-1 rounded-xl text-xs font-mono bg-surface border border-border text-text-primary shadow-xs"
                  >
                    <span className="font-semibold text-text-primary mr-1.5">{col.name}</span>
                    <span className="text-[10px] text-text-secondary font-normal">({col.dtype})</span>
                    {col.null_count > 0 && (
                      <span className="ml-1.5 text-[10px] text-amber-700 bg-amber-100 px-1 rounded">
                        {col.null_count} nulls
                      </span>
                    )}
                  </span>
                ))}
              </div>
            </div>

            {/* Preview Table */}
            {datasetMetadata.preview_rows && datasetMetadata.preview_rows.length > 0 && (
              <div>
                <h5 className="text-xs font-bold text-text-secondary uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <TableIcon className="w-3.5 h-3.5 text-primary" />
                  Dataset Preview (First 5 Rows)
                </h5>
                <div className="overflow-x-auto rounded-2xl border border-border">
                  <table className="min-w-full text-xs text-left">
                    <thead className="bg-surface-accent/20 text-text-primary border-b border-border font-semibold">
                      <tr>
                        {datasetMetadata.columns.map((col, i) => (
                          <th key={i} className="px-3 py-2.5 whitespace-nowrap">
                            {col.name}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border bg-surface">
                      {datasetMetadata.preview_rows.map((row, rowIdx) => (
                        <tr key={rowIdx} className="hover:bg-surface-accent/10 transition-colors font-mono text-[11px]">
                          {datasetMetadata.columns.map((col, colIdx) => (
                            <td key={colIdx} className="px-3 py-2 whitespace-nowrap text-text-primary">
                              {row[col.name] !== null && row[col.name] !== undefined ? String(row[col.name]) : (
                                <span className="text-neutral-400 italic">null</span>
                              )}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
