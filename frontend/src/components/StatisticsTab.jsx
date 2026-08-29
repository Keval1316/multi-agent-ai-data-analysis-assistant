import React from 'react';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  GitCommit,
  Database,
  CheckCircle2,
  Activity
} from 'lucide-react';

export default function StatisticsTab({ report }) {
  if (!report) return null;

  const { statistics, sql_results } = report;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      {/* 1. Univariate Moments & Quantiles Table */}
      {statistics?.univariate_metrics?.length > 0 && (
        <div className="glass-card p-6 md:p-8 rounded-3xl space-y-4 shadow-glass border border-[#CEAB93]/50">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-xl bg-[#AD8B73]/15 text-[#3E2723] flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-[#AD8B73]" />
            </div>
            <h4 className="font-extrabold text-[#3E2723] text-sm md:text-base tracking-tight font-display">
              Univariate Moments & Quantile Distribution Summary
            </h4>
          </div>

          <div className="overflow-x-auto rounded-2xl border border-[#CEAB93]/40">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-[#CEAB93]/50 bg-white text-[#3E2723] uppercase tracking-wider font-mono text-[10px] font-bold">
                  <th className="py-3 px-4">Metric</th>
                  <th className="py-3 px-4">Mean</th>
                  <th className="py-3 px-4">Median</th>
                  <th className="py-3 px-4">Min</th>
                  <th className="py-3 px-4">Max</th>
                  <th className="py-3 px-4">Std Dev</th>
                  <th className="py-3 px-4">P25</th>
                  <th className="py-3 px-4">P75</th>
                  <th className="py-3 px-4">IQR</th>
                  <th className="py-3 px-4">Skewness</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#CEAB93]/30 bg-white/70 font-mono">
                {statistics.univariate_metrics.map((um, idx) => (
                  <tr key={`${um.column_name}-${idx}`} className="hover:bg-white/95 transition-colors">
                    <td className="py-3 px-4 font-bold text-[#3E2723]">{um.column_name}</td>
                    <td className="py-3 px-4 text-[#3E2723] font-semibold">{um.mean.toLocaleString()}</td>
                    <td className="py-3 px-4 text-[#7D5A44]">{um.median.toLocaleString()}</td>
                    <td className="py-3 px-4 text-[#7D5A44]">{um.min.toLocaleString()}</td>
                    <td className="py-3 px-4 text-[#7D5A44]">{um.max.toLocaleString()}</td>
                    <td className="py-3 px-4 text-[#7D5A44]">{um.std.toLocaleString()}</td>
                    <td className="py-3 px-4 text-[#7D5A44]">{um.p25.toLocaleString()}</td>
                    <td className="py-3 px-4 text-[#7D5A44]">{um.p75.toLocaleString()}</td>
                    <td className="py-3 px-4 text-[#7D5A44]">{um.iqr.toLocaleString()}</td>
                    <td className="py-3 px-4 text-[#7D5A44]">{um.skewness !== null ? um.skewness : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 2. Correlation Pairs Matrix */}
      {statistics?.correlation_results?.length > 0 && (
        <div className="glass-card p-6 md:p-8 rounded-3xl space-y-4 shadow-glass border border-[#CEAB93]/50">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-xl bg-[#AD8B73]/15 text-[#3E2723] flex items-center justify-center">
              <GitCommit className="w-5 h-5 text-[#AD8B73]" />
            </div>
            <h4 className="font-extrabold text-[#3E2723] text-sm md:text-base tracking-tight font-display">
              Bivariate Correlation Matrix & Significance
            </h4>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
            {statistics.correlation_results.map((cp, idx) => (
              <div
                key={`${cp.col1}-${cp.col2}-${idx}`}
                className="p-4 md:p-5 rounded-2xl bg-white/80 border border-[#CEAB93]/40 flex items-center justify-between text-xs shadow-sm hover:border-[#AD8B73] transition-colors"
              >
                <div className="space-y-1">
                  <div className="font-bold text-sm text-[#3E2723] font-mono">
                    {cp.col1} <span className="text-[#7D5A44] font-normal">vs</span> {cp.col2}
                  </div>
                  <div className="text-xs text-[#7D5A44] font-mono">
                    Pearson r = <b className="text-[#3E2723]">{cp.pearson_coef}</b> • Spearman r = <b className="text-[#3E2723]">{cp.spearman_coef}</b>
                  </div>
                </div>

                <div className="text-right space-y-1">
                  <span className="inline-block px-3 py-1 rounded-xl text-[11px] font-bold bg-[#FFFBE9] border border-[#CEAB93]/60 text-[#3E2723]">
                    {cp.strength}
                  </span>
                  <div>
                    {cp.is_statistically_significant ? (
                      <span className="text-[10px] text-[#AD8B73] font-bold font-mono">p &lt; 0.05 (Significant)</span>
                    ) : (
                      <span className="text-[10px] text-[#7D5A44] font-mono">p = {cp.pearson_pvalue || 'N/A'}</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 3. Executed SQL Console */}
      {sql_results?.results?.length > 0 && (
        <div className="glass-card p-6 md:p-8 rounded-3xl space-y-5 shadow-glass border border-[#CEAB93]/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-xl bg-[#AD8B73]/15 text-[#3E2723] flex items-center justify-center">
                <Database className="w-5 h-5 text-[#AD8B73]" />
              </div>
              <h4 className="font-extrabold text-[#3E2723] text-sm md:text-base tracking-tight font-display">
                Executed DuckDB Analytical Queries
              </h4>
            </div>
            <span className="text-xs font-mono font-bold px-3 py-1 rounded-full bg-[#AD8B73]/15 text-[#3E2723] border border-[#CEAB93]/60">
              {sql_results.successful_queries}/{sql_results.total_queries} Successful
            </span>
          </div>

          <div className="space-y-4">
            {sql_results.results.map((sq, idx) => (
              <div
                key={`${sq.query_name || 'sql'}-${idx}`}
                className="p-5 rounded-2xl bg-white/80 border border-[#CEAB93]/40 space-y-3.5 text-xs shadow-sm hover:border-[#AD8B73] transition-colors"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center space-x-2.5">
                    <span className="font-mono font-extrabold text-sm text-[#3E2723]">{sq.query_name}</span>
                    <span className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase font-mono border ${
                      sq.execution_status === 'success'
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-300'
                        : sq.execution_status === 'failed'
                        ? 'bg-rose-50 text-rose-700 border-rose-300'
                        : 'bg-[#AD8B73]/15 text-[#3E2723] border-[#CEAB93]/60'
                    }`}>
                      {sq.execution_status}
                    </span>
                  </div>
                  <div className="flex items-center space-x-3 text-[#7D5A44] font-mono text-[11px]">
                    <span className="flex items-center space-x-1 font-semibold text-[#3E2723]">
                      <Clock className="w-3.5 h-3.5 text-[#AD8B73]" />
                      <span>{sq.execution_duration_ms}ms</span>
                    </span>
                    <span>{sq.row_count} rows</span>
                  </div>
                </div>

                <p className="text-[#7D5A44] font-normal">{sq.purpose}</p>

                {sq.error_message && (
                  <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-[11px] font-mono">
                    <span className="font-bold">Error: </span>{sq.error_message}
                  </div>
                )}

                <div className="p-4 rounded-xl bg-[#2C1810] font-mono text-[11px] text-[#FFFBE9] overflow-x-auto shadow-inner border border-[#3E2723]">
                  <code>{sq.sql}</code>
                </div>

                {sq.rows?.length > 0 && (
                  <div className="overflow-x-auto max-h-48 border border-[#CEAB93]/40 rounded-xl">
                    <table className="w-full text-left text-[11px] font-mono">
                      <thead className="bg-white border-b border-[#CEAB93]/40 text-[#3E2723] font-bold">
                        <tr>
                          {sq.columns.map((c, cIdx) => (
                            <th key={`${c}-${cIdx}`} className="py-2 px-3">{c}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#CEAB93]/30 bg-white/70">
                        {sq.rows.slice(0, 4).map((r, rIdx) => (
                          <tr key={rIdx} className="hover:bg-white/95">
                            {sq.columns.map((c, cIdx) => (
                              <td key={`${c}-${cIdx}`} className="py-2 px-3 text-[#3E2723]">
                                {r[c] !== null ? String(r[c]) : '—'}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
}
