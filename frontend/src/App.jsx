import React, { useState } from 'react';
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
  Lightbulb
} from 'lucide-react';
import FileUpload from './components/FileUpload';
import PipelineTracker from './components/PipelineTracker';
import OverviewTab from './components/OverviewTab';
import DataQualityTab from './components/DataQualityTab';
import StatisticsTab from './components/StatisticsTab';
import VisualizationsTab from './components/VisualizationsTab';
import InsightsTab from './components/InsightsTab';
import ReportMarkdownTab from './components/ReportMarkdownTab';

export default function App() {
  // Workflow Stage: 'upload' | 'streaming' | 'dashboard'
  const [stage, setStage] = useState('upload');
  const [selectedFile, setSelectedFile] = useState(null);
  const [currentStep, setCurrentStep] = useState(null);
  const [completedSteps, setCompletedSteps] = useState([]);
  const [livePreviews, setLivePreviews] = useState({});
  const [finalReport, setFinalReport] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  // Load sample dataset
  const handleSelectSample = async (sampleName) => {
    setErrorMsg(null);
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
      } else {
        // clean_dataset.csv fallback
        sampleData = `order_id,customer_name,category,product,quantity,unit_price,discount,total_revenue,order_date,is_returned,region
ORD-1001,Alice Johnson,Electronics,Wireless Headphones,2,79.99,0.00,159.98,2025-01-15,False,North
ORD-1002,Bob Smith,Furniture,Ergonomic Chair,1,249.50,0.10,224.55,2025-01-16,False,South`;
      }

      const file = new File([sampleData], sampleName, { type: mimeType });
      setSelectedFile(file);
    } catch (err) {
      setErrorMsg('Failed to load sample dataset');
    }
  };

  // Start SSE Streaming Execution
  const handleStartAnalysis = async () => {
    if (!selectedFile) return;

    setErrorMsg(null);
    setStage('streaming');
    setCurrentStep('validate_file');
    setCompletedSteps([]);
    setLivePreviews({});

    const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch(`${apiBase}/api/analyze/stream`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}: ${response.statusText}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop(); // Keep last incomplete segment

        for (const line of lines) {
          if (!line.trim()) continue;

          const eventMatch = line.match(/^event:\s*(\w+)/m);
          const dataMatch = line.match(/^data:\s*(.+)$/m);

          if (eventMatch && dataMatch) {
            const eventType = eventMatch[1];
            try {
              const data = JSON.parse(dataMatch[1]);

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
      console.error('Streaming connection error:', err);
      setErrorMsg(err.message || 'Connection to analysis engine failed.');
    }
  };

  const handleReset = () => {
    setStage('upload');
    setSelectedFile(null);
    setCurrentStep(null);
    setCompletedSteps([]);
    setLivePreviews({});
    setFinalReport(null);
    setErrorMsg(null);
    setActiveTab('overview');
  };

  return (
    <div className="min-h-screen bg-canvas text-text-primary flex flex-col font-sans selection:bg-primary/20 selection:text-text-primary">
      {/* 1. Navigation Top Bar */}
      <header className="sticky top-0 z-50 bg-surface/90 backdrop-blur-md border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-2xl bg-primary text-white flex items-center justify-center shadow-md">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <span className="font-extrabold text-base tracking-tight text-text-primary block leading-none">
                Multi-Agent Data Analyst
              </span>
              <span className="text-[10px] text-text-secondary font-mono">
                AI CSV & Excel Insight Generator
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            {stage === 'dashboard' && (
              <button
                onClick={handleReset}
                className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl bg-surface-accent/20 border border-border text-xs font-semibold text-text-primary hover:bg-surface-accent/40 transition-colors cursor-pointer"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>New Analysis</span>
              </button>
            )}
            <span className="text-xs px-2.5 py-1 rounded-full bg-primary/10 text-primary font-mono font-semibold border border-primary/20">
              17 Agents Active
            </span>
          </div>
        </div>
      </header>

      {/* 2. Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12">
        <AnimatePresence mode="wait">
          {/* STAGE 1: UPLOAD & HERO */}
          {stage === 'upload' && (
            <motion.div
              key="upload-stage"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              className="space-y-10 max-w-3xl mx-auto"
            >
              {/* Hero Banner */}
              <div className="text-center space-y-3">
                <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-primary/10 text-primary border border-primary/20 text-xs font-bold font-mono">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Autonomous Multi-Agent Analysis Pipeline</span>
                </div>
                <h1 className="text-3xl md:text-5xl font-black text-text-primary tracking-tight">
                  Turn Raw Datasets into <span className="text-primary">Executive Insights</span>
                </h1>
                <p className="text-sm md:text-base text-text-secondary max-w-xl mx-auto leading-relaxed">
                  Upload CSV or Excel data. Our 17 specialized AI and deterministic computation agents will profile quality, execute safe SQL, identify anomalies, and build an interactive report.
                </p>
              </div>

              {/* Sample Dataset Picker */}
              <div className="p-4 rounded-3xl bg-surface border border-border space-y-2">
                <span className="text-xs font-mono uppercase text-text-secondary font-semibold block text-center">
                  Quick Start with Sample Data
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  <button
                    onClick={() => handleSelectSample('clean_dataset.csv')}
                    className="p-3 rounded-2xl bg-surface-accent/15 border border-border hover:border-primary/60 text-left transition-all text-xs flex items-center space-x-3 cursor-pointer group"
                  >
                    <div className="w-8 h-8 rounded-xl bg-primary/10 text-primary flex items-center justify-center font-bold font-mono group-hover:scale-105 transition-transform">
                      CSV
                    </div>
                    <div>
                      <div className="font-bold text-text-primary">Clean E-Commerce Dataset</div>
                      <div className="text-[10px] text-text-secondary">20 rows • Sales & Regions</div>
                    </div>
                  </button>

                  <button
                    onClick={() => handleSelectSample('messy_dataset.csv')}
                    className="p-3 rounded-2xl bg-surface-accent/15 border border-border hover:border-primary/60 text-left transition-all text-xs flex items-center space-x-3 cursor-pointer group"
                  >
                    <div className="w-8 h-8 rounded-xl bg-amber-500/10 text-amber-600 flex items-center justify-center font-bold font-mono group-hover:scale-105 transition-transform">
                      ANOM
                    </div>
                    <div>
                      <div className="font-bold text-text-primary">Messy Outlier Dataset</div>
                      <div className="text-[10px] text-text-secondary">Missing values & extreme outliers</div>
                    </div>
                  </button>
                </div>
              </div>

              {/* Drag and Drop Zone */}
              <div className="p-8 rounded-3xl bg-surface border-2 border-dashed border-border hover:border-primary transition-all text-center space-y-4 shadow-sm">
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
                <label htmlFor="file-input" className="cursor-pointer block space-y-3">
                  <div className="w-14 h-14 mx-auto rounded-3xl bg-surface-accent/20 border border-border flex items-center justify-center text-primary">
                    <UploadCloud className="w-7 h-7" />
                  </div>
                  <div>
                    <span className="font-bold text-text-primary text-base block">
                      {selectedFile ? selectedFile.name : 'Choose a CSV or Excel file'}
                    </span>
                    <span className="text-xs text-text-secondary">
                      {selectedFile
                        ? `${(selectedFile.size / 1024).toFixed(1)} KB ready`
                        : 'Drag & drop file here or click to browse'}
                    </span>
                  </div>
                </label>

                {selectedFile && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="pt-4"
                  >
                    <button
                      onClick={handleStartAnalysis}
                      className="w-full py-4 rounded-2xl bg-primary text-white font-bold text-sm hover:bg-primary-hover shadow-md hover:shadow-lg transition-all duration-200 flex items-center justify-center space-x-2 cursor-pointer group"
                    >
                      <Sparkles className="w-4 h-4 group-hover:rotate-12 transition-transform" />
                      <span>Launch 17-Agent Pipeline</span>
                    </button>
                  </motion.div>
                )}
              </div>

              {errorMsg && (
                <div className="p-4 rounded-2xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{errorMsg}</span>
                </div>
              )}
            </motion.div>
          )}

          {/* STAGE 2: LIVE STREAMING PIPELINE TRACKER */}
          {stage === 'streaming' && (
            <motion.div
              key="streaming-stage"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              className="space-y-6"
            >
              <PipelineTracker
                currentStep={currentStep}
                completedSteps={completedSteps}
                livePreviews={livePreviews}
                filename={selectedFile?.name || 'dataset.csv'}
              />

              {errorMsg && (
                <div className="max-w-4xl mx-auto p-4 rounded-2xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    <span>{errorMsg}</span>
                  </div>
                  <button
                    onClick={handleReset}
                    className="px-3 py-1 rounded-xl bg-red-100 font-bold hover:bg-red-200 cursor-pointer"
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
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              className="space-y-8"
            >
              {/* Header Title Banner */}
              <div className="p-6 md:p-8 rounded-3xl bg-surface border border-border shadow-sm flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-bold uppercase font-mono px-2.5 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20">
                      Analysis Complete
                    </span>
                    <span className="text-xs text-text-secondary font-mono">
                      Quality: <b>Grade {finalReport.quality?.grade || 'A'}</b> ({finalReport.quality?.quality_score || 95}/100)
                    </span>
                  </div>
                  <h2 className="text-2xl md:text-3xl font-extrabold text-text-primary tracking-tight">
                    {finalReport.title}
                  </h2>
                  <p className="text-xs md:text-sm text-text-secondary">
                    {finalReport.subtitle}
                  </p>
                </div>

                <div className="flex items-center space-x-3 self-start md:self-center">
                  <span className="text-xs text-text-secondary font-mono">
                    {finalReport.profile?.total_rows?.toLocaleString()} Rows • {finalReport.profile?.total_columns} Cols
                  </span>
                </div>
              </div>

              {/* Navigation Tabs Bar */}
              <div className="flex items-center space-x-2 overflow-x-auto pb-1 border-b border-border text-xs font-semibold">
                {[
                  { id: 'overview', label: 'Executive Overview', icon: Sparkles },
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
                      className={`flex items-center space-x-2 px-4 py-2.5 rounded-2xl transition-all cursor-pointer whitespace-nowrap ${
                        isActive
                          ? 'bg-primary text-white shadow-sm'
                          : 'bg-surface text-text-secondary hover:text-text-primary hover:bg-surface-accent/20 border border-border'
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5" />
                      <span>{tab.label}</span>
                    </button>
                  );
                })}
              </div>

              {/* Tab Contents */}
              <div>
                {activeTab === 'overview' && <OverviewTab report={finalReport} />}
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
      <footer className="border-t border-border bg-surface/50 py-6 text-center text-xs text-text-secondary font-mono">
        Multi-Agent AI Data Analysis Assistant • Built with LangGraph, DuckDB & Plotly
      </footer>
    </div>
  );
}
