import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles,
  Bot,
  Layers,
  BarChart3,
  ShieldCheck,
  FileText,
  RotateCcw,
  UploadCloud,
  FileSpreadsheet,
  AlertCircle,
  Database,
  TrendingUp,
  Lightbulb,
  CheckCircle2,
  FileCode2,
  ArrowRight,
  ShieldAlert,
  History as HistoryIcon,
  Square,
  Info
} from 'lucide-react';
import PipelineTracker from './components/PipelineTracker';
import OverviewTab from './components/OverviewTab';
import DataQualityTab from './components/DataQualityTab';
import StatisticsTab from './components/StatisticsTab';
import VisualizationsTab from './components/VisualizationsTab';
import InsightsTab from './components/InsightsTab';
import ReportMarkdownTab from './components/ReportMarkdownTab';
import HistorySidebar from './components/HistorySidebar';
import CleanDataTab from './components/CleanDataTab';

export default function App() {
  const [stage, setStage] = useState('upload'); // 'upload' | 'streaming' | 'dashboard'
  const [selectedFile, setSelectedFile] = useState(null);
  const [currentStep, setCurrentStep] = useState(null);
  const [completedSteps, setCompletedSteps] = useState([]);
  const [livePreviews, setLivePreviews] = useState({});
  const [finalReport, setFinalReport] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const [statusNotice, setStatusNotice] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  // Sidebar & History state
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [history, setHistory] = useState(() => {
    try {
      const saved = localStorage.getItem('data_analysis_history');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });
  const [isStopping, setIsStopping] = useState(false);

  // Cancellation and Stream refs
  const abortControllerRef = useRef(null);
  const streamReaderRef = useRef(null);

  // Persist history to localStorage
  useEffect(() => {
    try {
      localStorage.setItem('data_analysis_history', JSON.stringify(history));
    } catch (err) {
      console.warn('Failed to save history to localStorage:', err);
    }
  }, [history]);

  // Sync initial history from backend if available
  useEffect(() => {
    const fetchBackendHistory = async () => {
      try {
        const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
        const res = await fetch(`${apiBase}/api/dataset/history`);
        if (res.ok) {
          const data = await res.json();
          if (data.history && Array.isArray(data.history) && data.history.length > 0) {
            setHistory((prev) => {
              const map = new Map();
              data.history.forEach((item) => map.set(item.dataset_id, item));
              prev.forEach((item) => {
                const existing = map.get(item.dataset_id) || {};
                map.set(item.dataset_id, { ...existing, ...item });
              });
              return Array.from(map.values());
            });
          }
        }
      } catch {
        // Backend offline or unreachable, local storage remains intact
      }
    };
    fetchBackendHistory();
  }, []);

  const handleSelectSample = async (sampleName) => {
    setErrorMsg(null);
    setStatusNotice(null);
    try {
      let sampleData = '';
      let mimeType = 'text/csv';

      if (sampleName === 'clean_dataset.csv') {
        sampleData = `order_id,customer_name,category,product,quantity,unit_price,discount,total_revenue,order_date,is_returned,region
ORD-1001,Alice Johnson,Electronics,Wireless Headphones,2,79.99,0.00,159.98,2025-01-15,False,North
ORD-1002,Bob Smith,Furniture,Ergonomic Chair,1,249.50,0.10,224.55,2025-01-16,False,South
ORD-1003,Charlie Davis,Office Supplies,Gel Pens Pack,5,12.00,0.00,60.00,2025-01-17,False,East
ORD-1004,Diana Evans,Electronics,Smart Watch,1,199.99,0.05,189.99,2025-01-18,False,West
ORD-1005,Evan Wright,Furniture,Standing Desk,1,399.00,0.15,339.15,2025-01-19,False,North
ORD-1006,Fiona Green,Office Supplies,Notebook Set,3,15.50,0.00,46.50,2025-01-20,False,South
ORD-1007,George Hall,Electronics,Bluetooth Speaker,2,45.00,0.00,90.00,2025-01-21,True,East
ORD-1008,Hannah King,Furniture,Bookshelf,1,129.99,0.00,129.99,2025-01-22,False,West
ORD-1009,Ian Lee,Office Supplies,Desk Organizer,2,22.00,0.05,41.80,2025-01-23,False,North
ORD-1010,Julia Miller,Electronics,Noise Cancelling Earbuds,1,149.99,0.10,134.99,2025-01-24,False,South
ORD-1011,Kevin Nelson,Furniture,LED Desk Lamp,2,34.50,0.00,69.00,2025-01-25,False,East
ORD-1012,Laura Owens,Office Supplies,Heavy Duty Stapler,1,18.75,0.00,18.75,2025-01-26,False,West
ORD-1013,Mike Perez,Electronics,4K Monitor,1,329.00,0.10,296.10,2025-01-27,False,North
ORD-1014,Nina Quinn,Furniture,Monitor Arm,1,59.99,0.00,59.99,2025-01-28,False,South
ORD-1015,Oscar Roberts,Office Supplies,Printer Paper Box,4,28.00,0.00,112.00,2025-01-29,False,East
ORD-1016,Paula Scott,Electronics,USB-C Hub,3,39.99,0.05,113.97,2025-01-30,False,West
ORD-1017,Quinn Taylor,Furniture,Footrest Cushion,1,29.95,0.00,29.95,2025-01-31,False,North
ORD-1018,Rachel Adams,Office Supplies,Whiteboard Markers,6,8.50,0.00,51.00,2025-02-01,False,South
ORD-1019,Sam Wilson,Electronics,Mechanical Keyboard,1,119.00,0.00,119.00,2025-02-02,False,East
ORD-1020,Tony Stark,Electronics,VR Headset,2,499.99,0.05,949.98,2025-03-01,False,South`;
      } else if (sampleName === 'messy_dataset.csv') {
        sampleData = `order_id,customer_name,category,product,quantity,unit_price,discount,total_revenue,order_date,is_returned,region
ORD-2001,John Doe,Electronics,Smartphone,1,699.99,0,699.99,2025-01-01,False,North
ORD-2002,Jane Smith,electronics,Smartphone,-2,699.99,0,-1399.98,2025-01-02,False,north
ORD-2003,Bob Johnson,FURNITURE,Office Chair,99999,150.00,0,14999850.00,2025-01-03,False,South
ORD-2004,Alice Brown,,Desk Lamp,1,35.00,0.50,17.50,2025-01-04,False,East
ORD-2005,,Office Supplies,Pen Box,10,5.00,0,50.00,2025-01-05,True,West
ORD-2006,Charlie Davis,Electronics,Laptop,1,1200.00,0.10,1080.00,2025-01-06,False,North
ORD-2001,John Doe,Electronics,Smartphone,1,699.99,0,699.99,2025-01-01,False,North
ORD-2007,Eve White,Furniture,Table,1,450.00,0,450.00,invalid_date,False,South
ORD-2008,Frank Miller,Office Supplies,Notebook,5,4.50,0,22.50,2025-01-08,False,N/A
ORD-2009,Grace Wilson,Electronics,Tablet,1,499.99,0.05,474.99,2025-01-09,False,East
ORD-2010,Hank Green,electronics,Mouse,2,25.00,0,50.00,2025-01-10,False,West`;
      }

      const file = new File([sampleData], sampleName, { type: mimeType });
      setSelectedFile(file);
    } catch {
      setErrorMsg('Failed to load sample dataset');
    }
  };

  const handleStartAnalysis = async () => {
    if (!selectedFile) return;

    setErrorMsg(null);
    setStatusNotice(null);
    setStage('streaming');
    setCurrentStep('validate_file');
    setCompletedSteps([]);
    setLivePreviews({});
    setIsStopping(false);

    // Setup AbortController for termination support
    abortControllerRef.current = new AbortController();

    const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch(`${apiBase}/api/analyze/stream`, {
        method: 'POST',
        body: formData,
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}: ${response.statusText}`);
      }

      const reader = response.body.getReader();
      streamReaderRef.current = reader;
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.trim()) continue;

          const eventMatch = line.match(/^event:\s*(\w+)/m);
          const dataMatch = line.match(/^data:\s*(.+)$/m);

          if (eventMatch && dataMatch) {
            const eventType = eventMatch[1];
            try {
              // Sanitize non-standard JSON tokens like NaN, Infinity, -Infinity
              const sanitizedJson = dataMatch[1]
                .replace(/:\s*NaN\b/g, ': null')
                .replace(/:\s*Infinity\b/g, ': null')
                .replace(/:\s*-Infinity\b/g, ': null');
              const data = JSON.parse(sanitizedJson);

              if (eventType === 'step_complete') {
                setCurrentStep(data.step);
                setCompletedSteps((prev) => [...new Set([...prev, data.step])]);
                if (data.preview) {
                  setLivePreviews((prev) => ({ ...prev, [data.step]: data.preview }));
                }
              } else if (eventType === 'complete') {
                if (data.report) {
                  setFinalReport(data.report);
                  setStage('dashboard');
                  setActiveTab('overview');

                  // Save to persistent history
                  const historyRecord = {
                    dataset_id: data.report.dataset_id,
                    filename: data.report.filename || selectedFile?.name || 'dataset.csv',
                    title: data.report.title,
                    subtitle: data.report.subtitle,
                    generated_at: data.report.generated_at || new Date().toISOString(),
                    quality_score: data.report.quality?.quality_score || 100,
                    grade: data.report.quality?.grade || 'A',
                    total_rows: data.report.profile?.total_rows || 0,
                    total_columns: data.report.profile?.total_columns || 0,
                    domain: data.report.understanding?.domain || 'General Data',
                    charts_count: data.report.charts?.charts?.length || 0,
                    insights_count: data.report.insights?.insights?.length || 0,
                    report: data.report
                  };
                  setHistory((prev) => [historyRecord, ...prev.filter((h) => h.dataset_id !== data.report.dataset_id)]);
                }
              } else if (eventType === 'error') {
                setErrorMsg(data.error || 'Pipeline encountered an error.');
              }
            } catch (err) {
              console.error('Error parsing SSE event data:', err);
            }
          }
        }
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        console.log('Analysis fetch aborted cleanly by user.');
      } else {
        console.error('Streaming connection error:', err);
        setErrorMsg(err.message || 'Connection to analysis engine failed.');
      }
    } finally {
      abortControllerRef.current = null;
      streamReaderRef.current = null;
      setIsStopping(false);
    }
  };

  const handleStopAnalysis = async () => {
    setIsStopping(true);
    try {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (streamReaderRef.current) {
        await streamReaderRef.current.cancel();
      }
    } catch (err) {
      console.warn('Error during stream cancellation:', err);
    } finally {
      setIsStopping(false);
      setStage('upload');
      setCurrentStep(null);
      setCompletedSteps([]);
      setLivePreviews({});
      setStatusNotice('Pipeline analysis was terminated and cancelled by user.');
    }
  };

  const handleSelectHistoryReport = async (item) => {
    setErrorMsg(null);
    setStatusNotice(null);

    if (item.report) {
      setFinalReport(item.report);
      setStage('dashboard');
      setActiveTab('overview');
      return;
    }

    try {
      const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const res = await fetch(`${apiBase}/api/dataset/${item.dataset_id}/report`);
      if (!res.ok) {
        throw new Error(`Failed to retrieve dataset report (${res.status})`);
      }
      const reportData = await res.json();
      setHistory((prev) =>
        prev.map((h) => (h.dataset_id === item.dataset_id ? { ...h, report: reportData } : h))
      );
      setFinalReport(reportData);
      setStage('dashboard');
      setActiveTab('overview');
    } catch (err) {
      setErrorMsg(`Could not load report for ${item.filename}: ${err.message}`);
    }
  };

  const handleDeleteHistoryItem = async (dataset_id, e) => {
    if (e) e.stopPropagation();
    setHistory((prev) => prev.filter((h) => h.dataset_id !== dataset_id));
    if (finalReport?.dataset_id === dataset_id) {
      handleReset();
    }
    try {
      const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      await fetch(`${apiBase}/api/dataset/${dataset_id}`, { method: 'DELETE' });
    } catch {
      // Backend deletion best effort
    }
  };

  const handleClearHistory = () => {
    setHistory([]);
    try {
      localStorage.removeItem('data_analysis_history');
    } catch {}
  };

  const handleReset = () => {
    setStage('upload');
    setSelectedFile(null);
    setCurrentStep(null);
    setCompletedSteps([]);
    setLivePreviews({});
    setFinalReport(null);
    setErrorMsg(null);
    setStatusNotice(null);
    setActiveTab('overview');
  };

  return (
    <div className="min-h-screen bg-[#FFFBE9] text-[#3E2723] flex flex-col font-sans relative overflow-x-hidden">
      {/* Background Ambient Glowing Orbs */}
      <div className="fixed top-0 left-1/4 w-[650px] h-[650px] bg-[#E3CAA5]/30 rounded-full blur-[120px] pointer-events-none -z-10 animate-pulse" style={{ animationDuration: '8s' }} />
      <div className="fixed bottom-10 right-1/4 w-[550px] h-[550px] bg-[#AD8B73]/20 rounded-full blur-[140px] pointer-events-none -z-10" />
      <div className="fixed inset-0 bg-dot-grid pointer-events-none -z-10 opacity-60" />

      {/* History Sidebar Drawer */}
      <HistorySidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        history={history}
        activeDatasetId={finalReport?.dataset_id}
        onSelectReport={handleSelectHistoryReport}
        onDeleteHistoryItem={handleDeleteHistoryItem}
        onClearHistory={handleClearHistory}
        onNewAnalysis={handleReset}
      />

      {/* 1. Header Navigation */}
      <header className="sticky top-0 z-40 bg-white/85 backdrop-blur-xl border-b border-[#CEAB93]/40 shadow-sm transition-all">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
          {/* Left: Brand Identity */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 md:w-11 md:h-11 rounded-2xl bg-gradient-to-br from-[#AD8B73] to-[#3E2723] text-white flex items-center justify-center shadow-md shadow-[#AD8B73]/20 ring-2 ring-white/80">
              <Bot className="w-5 h-5 md:w-6 md:h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-base md:text-lg tracking-tight text-[#3E2723] font-display">
                  Multi-Agent Data Analyst
                </span>
                <span className="hidden sm:inline px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-[#AD8B73]/15 text-[#3E2723] border border-[#CEAB93]/50">
                  v1.0
                </span>
              </div>
              <span className="text-[11px] md:text-xs text-[#7D5A44] font-medium tracking-wide block">
                Autonomous CSV & Excel Insight Synthesizer
              </span>
            </div>
          </div>

          {/* Right: History, New Analysis & Status */}
          <div className="flex items-center space-x-2.5">
            <button
              onClick={() => setIsSidebarOpen(true)}
              className="p-2 sm:px-3.5 sm:py-2 rounded-2xl bg-white/90 border border-[#CEAB93]/60 text-[#3E2723] hover:border-[#AD8B73] hover:bg-[#FFFBE9] transition-all shadow-xs flex items-center space-x-2 cursor-pointer group"
              title="Open Analysis History"
            >
              <HistoryIcon className="w-4 h-4 text-[#AD8B73] group-hover:scale-110 transition-transform" />
              <span className="text-xs font-bold font-sans">History</span>
              {history.length > 0 && (
                <span className="px-1.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-[#AD8B73]/15 text-[#3E2723] border border-[#CEAB93]/40">
                  {history.length}
                </span>
              )}
            </button>

            {stage === 'dashboard' && (
              <button
                onClick={handleReset}
                className="flex items-center space-x-2 px-3.5 py-2 rounded-2xl bg-white/90 border border-[#CEAB93]/60 text-xs font-bold text-[#3E2723] hover:bg-[#FFFBE9] hover:border-[#AD8B73] transition-all shadow-sm cursor-pointer"
              >
                <RotateCcw className="w-3.5 h-3.5 text-[#AD8B73]" />
                <span className="hidden sm:inline">New Analysis</span>
              </button>
            )}

            <div className="hidden sm:flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-[#AD8B73]/10 border border-[#CEAB93]/50 text-[#3E2723] text-xs font-mono font-semibold">
              <span className="w-2 h-2 rounded-full bg-[#AD8B73] animate-pulse" />
              <span>17 Agents</span>
            </div>
          </div>
        </div>
      </header>

      {/* 2. Main Content Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-14">
        <AnimatePresence mode="wait">
          {/* STAGE 1: HERO & UPLOAD */}
          {stage === 'upload' && (
            <motion.div
              key="upload-stage"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.3 }}
              className="space-y-10 max-w-3xl mx-auto"
            >
              {/* Notice Banner if analysis was stopped / cancelled */}
              {statusNotice && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="p-4 rounded-2xl bg-[#E3CAA5]/30 border border-[#CEAB93]/60 text-[#3E2723] text-xs flex items-center justify-between shadow-sm"
                >
                  <div className="flex items-center space-x-2.5">
                    <Info className="w-4 h-4 text-[#AD8B73] flex-shrink-0" />
                    <span className="font-semibold">{statusNotice}</span>
                  </div>
                  <button
                    onClick={() => setStatusNotice(null)}
                    className="text-[#7D5A44] hover:text-[#3E2723] text-xs font-bold"
                  >
                    Dismiss
                  </button>
                </motion.div>
              )}

              {/* Hero Banner */}
              <div className="text-center space-y-4">
                <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-white/90 border border-[#CEAB93]/60 shadow-sm text-xs font-bold text-[#3E2723]">
                  <Sparkles className="w-4 h-4 text-[#AD8B73] animate-pulse" />
                  <span>Deterministic Computing • LLM Reasoning • Adversarial Critic</span>
                </div>

                <h1 className="text-4xl sm:text-5xl md:text-6xl font-black text-[#3E2723] tracking-tight font-display leading-[1.1]">
                  Turn Raw Data into <br className="hidden sm:inline" />
                  <span className="bg-clip-text text-transparent bg-gradient-to-r from-[#3E2723] via-[#AD8B73] to-[#8C6542]">
                    Executive Intelligence
                  </span>
                </h1>

                <p className="text-sm md:text-base text-[#7D5A44] max-w-xl mx-auto leading-relaxed font-normal">
                  Ingest CSV or Excel spreadsheets. Our 17 specialized AI and deterministic agents compute statistical moments, audit quality, execute safe SQL, and compile a verified executive report.
                </p>
              </div>

              {/* Sample Datasets Selector */}
              <div className="glass-card p-5 md:p-6 rounded-3xl space-y-3 shadow-glass">
                <div className="flex items-center justify-between px-1">
                  <span className="text-xs font-mono uppercase tracking-wider text-[#7D5A44] font-bold">
                    Quick Start with Built-in Datasets
                  </span>
                  <span className="text-[11px] text-[#7D5A44]">Click to load instant test data</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                  <button
                    onClick={() => handleSelectSample('clean_dataset.csv')}
                    className="p-4 rounded-2xl bg-white/70 border border-[#CEAB93]/40 hover:border-[#AD8B73] hover:bg-white text-left transition-all duration-200 flex items-center space-x-3.5 shadow-sm hover:shadow-md cursor-pointer group"
                  >
                    <div className="w-10 h-10 rounded-xl bg-[#AD8B73]/15 text-[#3E2723] flex items-center justify-center font-mono font-bold text-xs group-hover:scale-105 group-hover:bg-[#AD8B73] group-hover:text-white transition-all shadow-inner">
                      CSV
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-bold text-sm text-[#3E2723] truncate group-hover:text-[#AD8B73] transition-colors">
                        Clean E-Commerce Dataset
                      </div>
                      <div className="text-[11px] text-[#7D5A44] font-mono">
                        20 rows • Sales, Discounts & Regions
                      </div>
                    </div>
                  </button>

                  <button
                    onClick={() => handleSelectSample('messy_dataset.csv')}
                    className="p-4 rounded-2xl bg-white/70 border border-[#CEAB93]/40 hover:border-amber-500/80 hover:bg-white text-left transition-all duration-200 flex items-center space-x-3.5 shadow-sm hover:shadow-md cursor-pointer group"
                  >
                    <div className="w-10 h-10 rounded-xl bg-amber-500/15 text-amber-800 flex items-center justify-center font-mono font-bold text-xs group-hover:scale-105 group-hover:bg-amber-600 group-hover:text-white transition-all shadow-inner">
                      ANOM
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-bold text-sm text-[#3E2723] truncate group-hover:text-amber-700 transition-colors">
                        Messy Outlier Dataset
                      </div>
                      <div className="text-[11px] text-[#7D5A44] font-mono">
                        Extreme outliers & missing values
                      </div>
                    </div>
                  </button>
                </div>
              </div>

              {/* Drag and Drop Zone */}
              <div className="glass-card p-8 md:p-10 rounded-3xl border-2 border-dashed border-[#CEAB93]/70 hover:border-[#AD8B73] transition-all text-center space-y-5 shadow-glass group">
                <input
                  type="file"
                  id="file-input"
                  accept=".csv,.xlsx,.xls"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      setSelectedFile(e.target.files[0]);
                    }
                  }}
                  className="hidden"
                />
                <label htmlFor="file-input" className="cursor-pointer block space-y-4">
                  <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br from-[#AD8B73]/20 to-[#E3CAA5]/30 border border-[#CEAB93]/60 flex items-center justify-center text-[#3E2723] group-hover:scale-110 group-hover:text-[#AD8B73] transition-all shadow-sm">
                    <UploadCloud className="w-8 h-8" />
                  </div>
                  <div className="space-y-1">
                    <span className="font-extrabold text-base md:text-lg text-[#3E2723] block font-display">
                      {selectedFile ? selectedFile.name : 'Choose or Drop your CSV / Excel File'}
                    </span>
                    <p className="text-xs text-[#7D5A44]">
                      {selectedFile
                        ? `${(selectedFile.size / 1024).toFixed(1)} KB selected and ready`
                        : 'Supports .CSV, .XLSX, and .XLS up to 10MB'}
                    </p>
                  </div>
                </label>

                {selectedFile && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="pt-2"
                  >
                    <button
                      onClick={handleStartAnalysis}
                      className="w-full py-4 px-6 rounded-2xl bg-gradient-to-r from-[#AD8B73] to-[#3E2723] text-white font-extrabold text-sm md:text-base tracking-wide hover:from-[#3E2723] hover:to-[#2C1810] shadow-lg shadow-[#AD8B73]/30 hover:shadow-xl hover:shadow-[#3E2723]/30 hover:scale-[1.01] active:scale-[0.99] transition-all duration-200 flex items-center justify-center space-x-2.5 cursor-pointer"
                    >
                      <Sparkles className="w-5 h-5 animate-pulse" />
                      <span>Launch 17-Agent Pipeline</span>
                      <ArrowRight className="w-4 h-4 ml-1" />
                    </button>
                  </motion.div>
                )}
              </div>

              {errorMsg && (
                <div className="p-4 rounded-2xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center space-x-2.5 shadow-sm">
                  <AlertCircle className="w-4 h-4 flex-shrink-0 text-red-600" />
                  <span className="font-medium">{errorMsg}</span>
                </div>
              )}
            </motion.div>
          )}

          {/* STAGE 2: LIVE STREAMING PIPELINE TRACKER */}
          {stage === 'streaming' && (
            <motion.div
              key="streaming-stage"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              className="space-y-6"
            >
              <PipelineTracker
                currentStep={currentStep}
                completedSteps={completedSteps}
                livePreviews={livePreviews}
                filename={selectedFile?.name || 'dataset.csv'}
                onStop={handleStopAnalysis}
                isStopping={isStopping}
              />

              {errorMsg && (
                <div className="max-w-4xl mx-auto p-4 rounded-2xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center justify-between shadow-sm">
                  <div className="flex items-center space-x-2">
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    <span>{errorMsg}</span>
                  </div>
                  <button
                    onClick={handleReset}
                    className="px-3.5 py-1.5 rounded-xl bg-red-100 font-bold hover:bg-red-200 cursor-pointer"
                  >
                    Retry
                  </button>
                </div>
              )}
            </motion.div>
          )}

          {/* STAGE 3: EXECUTIVE DASHBOARD */}
          {stage === 'dashboard' && finalReport && (
            <motion.div
              key="dashboard-stage"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              className="space-y-8"
            >
              {/* Executive Header Banner */}
              <div className="glass-card p-6 md:p-8 rounded-3xl shadow-glass flex flex-col md:flex-row md:items-center md:justify-between gap-5 border border-[#CEAB93]/50">
                <div className="space-y-1.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-bold uppercase font-mono px-3 py-0.5 rounded-full bg-[#AD8B73]/15 text-[#3E2723] border border-[#CEAB93]/60 flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5 text-[#AD8B73]" />
                      Multi-Agent Synthesis Complete
                    </span>
                    <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded-full bg-white border border-[#CEAB93]/50 text-[#3E2723]">
                      Grade {finalReport.quality?.grade || 'A'} ({finalReport.quality?.quality_score || 98}/100)
                    </span>
                  </div>
                  <h2 className="text-2xl md:text-3xl font-extrabold text-[#3E2723] tracking-tight font-display">
                    {finalReport.title}
                  </h2>
                  <p className="text-xs md:text-sm text-[#7D5A44] font-medium">
                    {finalReport.subtitle}
                  </p>
                </div>

                <div className="flex items-center space-x-3 self-start md:self-center">
                  <div className="p-3 px-4 rounded-2xl bg-white/90 border border-[#CEAB93]/40 text-center shadow-sm">
                    <span className="text-[10px] uppercase font-mono text-[#7D5A44] block font-bold">Records</span>
                    <span className="text-base font-bold text-[#3E2723] font-mono">{finalReport.profile?.total_rows?.toLocaleString()}</span>
                  </div>
                  <div className="p-3 px-4 rounded-2xl bg-white/90 border border-[#CEAB93]/40 text-center shadow-sm">
                    <span className="text-[10px] uppercase font-mono text-[#7D5A44] block font-bold">Variables</span>
                    <span className="text-base font-bold text-[#3E2723] font-mono">{finalReport.profile?.total_columns}</span>
                  </div>
                </div>
              </div>

              {/* Navigation Segmented Tab Bar */}
              <div className="flex items-center space-x-2 overflow-x-auto pb-1 text-xs font-bold font-sans">
                {[
                  { id: 'overview', label: 'Executive Overview', icon: Sparkles },
                  { id: 'cleandata', label: 'Cleaned Dataset & Export', icon: FileSpreadsheet },
                  { id: 'quality', label: 'Data Quality & Schema', icon: ShieldCheck },
                  { id: 'statistics', label: 'Statistics & SQL', icon: Database },
                  { id: 'visualizations', label: 'Interactive Visuals', icon: BarChart3 },
                  { id: 'insights', label: 'Verified Insights', icon: Lightbulb },
                  { id: 'report', label: 'Full Report & PDF', icon: FileText },
                ].map((tab) => {
                  const Icon = tab.icon;
                  const isActive = activeTab === tab.id;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`flex items-center space-x-2 px-4 py-3 rounded-2xl transition-all duration-200 cursor-pointer whitespace-nowrap ${
                        isActive
                          ? 'bg-gradient-to-r from-[#AD8B73] to-[#3E2723] text-white shadow-md shadow-[#AD8B73]/20 scale-100'
                          : 'glass-card text-[#3E2723] hover:bg-white/95 border-[#CEAB93]/40'
                      }`}
                    >
                      <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-[#AD8B73]'}`} />
                      <span>{tab.label}</span>
                    </button>
                  );
                })}
              </div>

              {/* Tab Contents */}
              <div>
                {activeTab === 'overview' && <OverviewTab report={finalReport} />}
                {activeTab === 'cleandata' && <CleanDataTab report={finalReport} />}
                {activeTab === 'quality' && <DataQualityTab report={finalReport} />}
                {activeTab === 'statistics' && <StatisticsTab report={finalReport} />}
                {activeTab === 'visualizations' && <VisualizationsTab report={finalReport} />}
                {activeTab === 'insights' && <InsightsTab report={finalReport} />}
                {activeTab === 'report' && (
                  <ReportMarkdownTab report={finalReport} datasetId={finalReport.dataset_id} />
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Footer */}
      <footer className="border-t border-[#CEAB93]/40 bg-white/60 backdrop-blur-md py-6 text-center text-xs text-[#7D5A44] font-mono">
        Multi-Agent AI Data Analysis Assistant • LangGraph Orchestration & DuckDB Engine
      </footer>
    </div>
  );
}
