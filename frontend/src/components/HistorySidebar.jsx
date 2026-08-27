import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  History,
  X,
  Trash2,
  FileSpreadsheet,
  Calendar,
  Sparkles,
  Plus,
  Search,
  Database,
  ArrowRight,
  ShieldCheck,
  ChevronRight
} from 'lucide-react';

export default function HistorySidebar({
  isOpen,
  onClose,
  history = [],
  activeDatasetId = null,
  onSelectReport,
  onDeleteHistoryItem,
  onClearHistory,
  onNewAnalysis
}) {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredHistory = history.filter((item) => {
    const term = searchTerm.toLowerCase();
    const name = (item.filename || '').toLowerCase();
    const title = (item.title || '').toLowerCase();
    const domain = (item.domain || '').toLowerCase();
    return name.includes(term) || title.includes(term) || domain.includes(term);
  });

  const formatTimestamp = (dateStr) => {
    if (!dateStr) return 'Recent';
    try {
      const d = new Date(dateStr);
      if (isNaN(d.getTime())) return dateStr;
      return d.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop Blur Overlay for mobile & clicking outside */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-[#3E2723]/30 backdrop-blur-xs z-50 transition-opacity"
          />

          {/* Sidebar Drawer - Slide from Right */}
          <motion.aside
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 26, stiffness: 280 }}
            className="fixed top-0 right-0 bottom-0 w-full max-w-[360px] sm:max-w-[400px] bg-[#FFFBE9]/95 backdrop-blur-2xl border-l border-[#CEAB93]/60 shadow-2xl z-50 flex flex-col font-sans"
          >
            {/* 1. Sidebar Header */}
            <div className="p-5 border-b border-[#CEAB93]/40 flex items-center justify-between bg-white/60">
              <div className="flex items-center space-x-2.5">
                <div className="w-9 h-9 rounded-2xl bg-[#AD8B73]/15 text-[#3E2723] flex items-center justify-center border border-[#CEAB93]/60 shadow-xs">
                  <History className="w-4 h-4 text-[#AD8B73]" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h3 className="font-extrabold text-base text-[#3E2723] font-display">
                      Analysis History
                    </h3>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-[#AD8B73]/15 text-[#3E2723] border border-[#CEAB93]/50">
                      {history.length}
                    </span>
                  </div>
                  <p className="text-[11px] text-[#7D5A44]">
                    Saved dataset reports & synthesis
                  </p>
                </div>
              </div>

              <button
                onClick={onClose}
                className="w-8 h-8 rounded-xl bg-white border border-[#CEAB93]/50 text-[#7D5A44] hover:text-[#3E2723] hover:border-[#AD8B73] flex items-center justify-center transition-all shadow-xs cursor-pointer"
                title="Close Sidebar"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* 2. Action Bar & Search Filter */}
            <div className="p-4 space-y-3 border-b border-[#CEAB93]/30 bg-white/40">
              <button
                onClick={() => {
                  onNewAnalysis();
                  onClose();
                }}
                className="w-full py-2.5 px-4 rounded-2xl bg-gradient-to-r from-[#AD8B73] to-[#3E2723] text-white text-xs font-bold hover:from-[#3E2723] hover:to-[#2C1810] shadow-md shadow-[#AD8B73]/20 flex items-center justify-center space-x-2 transition-all cursor-pointer"
              >
                <Plus className="w-4 h-4" />
                <span>Start New Analysis</span>
              </button>

              {history.length > 0 && (
                <div className="relative">
                  <Search className="w-3.5 h-3.5 text-[#7D5A44] absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Search past datasets..."
                    className="w-full pl-9 pr-3 py-2 rounded-xl bg-white/90 border border-[#CEAB93]/50 text-xs text-[#3E2723] placeholder-[#7D5A44]/60 focus:outline-none focus:border-[#AD8B73] focus:ring-1 focus:ring-[#AD8B73]/30 transition-all font-mono"
                  />
                  {searchTerm && (
                    <button
                      onClick={() => setSearchTerm('')}
                      className="absolute right-2.5 top-1/2 -translate-y-1/2 text-xs text-[#7D5A44] hover:text-[#3E2723]"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* 3. History List Container */}
            <div className="flex-1 overflow-y-auto p-4 space-y-2.5">
              {history.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-3 text-[#7D5A44]">
                  <div className="w-14 h-14 rounded-3xl bg-white/80 border border-[#CEAB93]/50 flex items-center justify-center text-[#AD8B73] shadow-sm">
                    <Database className="w-7 h-7 opacity-70" />
                  </div>
                  <div className="space-y-1">
                    <h4 className="font-bold text-sm text-[#3E2723]">No Analysis Records Yet</h4>
                    <p className="text-xs max-w-[220px] leading-relaxed">
                      Upload and analyze any CSV or Excel file to automatically record reports here.
                    </p>
                  </div>
                </div>
              ) : filteredHistory.length === 0 ? (
                <div className="text-center py-10 text-xs text-[#7D5A44] space-y-1">
                  <p className="font-bold">No results found</p>
                  <p>Try searching with another filename keyword.</p>
                </div>
              ) : (
                filteredHistory.map((item) => {
                  const isActive = activeDatasetId === item.dataset_id;
                  const isCleanGrade = (item.grade || 'A').toUpperCase() === 'A';

                  return (
                    <motion.div
                      key={item.dataset_id}
                      whileHover={{ scale: 1.01 }}
                      className={`group relative p-3.5 rounded-2xl transition-all duration-200 border cursor-pointer ${
                        isActive
                          ? 'bg-white border-[#AD8B73] shadow-md ring-2 ring-[#AD8B73]/25'
                          : 'bg-white/75 hover:bg-white border-[#CEAB93]/40 hover:border-[#AD8B73]/60 shadow-xs'
                      }`}
                      onClick={() => {
                        onSelectReport(item);
                        onClose();
                      }}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-center space-x-2.5 min-w-0 flex-1">
                          <div className="w-8 h-8 rounded-xl bg-[#AD8B73]/15 text-[#3E2723] flex items-center justify-center flex-shrink-0 font-mono text-[10px] font-bold border border-[#CEAB93]/40">
                            <FileSpreadsheet className="w-4 h-4 text-[#AD8B73]" />
                          </div>
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center space-x-1.5">
                              <h4 className="font-bold text-xs text-[#3E2723] truncate">
                                {item.filename || 'dataset.csv'}
                              </h4>
                              {isActive && (
                                <span className="w-2 h-2 rounded-full bg-[#AD8B73] animate-pulse flex-shrink-0" />
                              )}
                            </div>
                            <span className="text-[10px] text-[#7D5A44] font-mono block">
                              {formatTimestamp(item.generated_at)}
                            </span>
                          </div>
                        </div>

                        {/* Delete Action Button */}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onDeleteHistoryItem(item.dataset_id, e);
                          }}
                          className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition-all cursor-pointer"
                          title="Delete Record"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>

                      {/* Summary Metrics & Quality Pills */}
                      <div className="mt-2.5 pt-2 border-t border-[#CEAB93]/20 flex items-center justify-between text-[10px] font-mono">
                        <div className="flex items-center space-x-2 text-[#7D5A44]">
                          <span>{item.total_rows?.toLocaleString() || 0} rows</span>
                          <span>•</span>
                          <span>{item.total_columns || 0} cols</span>
                        </div>

                        <span
                          className={`px-2 py-0.5 rounded-md font-bold ${
                            isCleanGrade
                              ? 'bg-[#AD8B73]/15 text-[#3E2723] border border-[#CEAB93]/60'
                              : 'bg-amber-100 text-amber-800 border border-amber-200'
                          }`}
                        >
                          Grade {item.grade || 'A'} ({item.quality_score || 100})
                        </span>
                      </div>
                    </motion.div>
                  );
                })
              )}
            </div>

            {/* 4. Sidebar Footer */}
            {history.length > 0 && (
              <div className="p-4 border-t border-[#CEAB93]/40 bg-white/60 flex items-center justify-between">
                <span className="text-[11px] text-[#7D5A44] font-mono">
                  {history.length} {history.length === 1 ? 'record' : 'records'} cached
                </span>
                <button
                  onClick={onClearHistory}
                  className="text-xs text-red-600 hover:text-red-700 hover:underline font-bold transition-colors cursor-pointer flex items-center space-x-1"
                >
                  <Trash2 className="w-3 h-3" />
                  <span>Clear All</span>
                </button>
              </div>
            )}
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}
