import React from 'react';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  GitCommit,
  Database,
  CheckCircle2,
  Clock,
  Code
} from 'lucide-react';

export default function StatisticsTab({ report }) {
  if (!report) return null;

  const { statistics, sql_results } = report;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* 1. Univariate Moments & Quantiles Table */}
      {statistics?.univariate_metrics?.length > 0 && (
        <div className="p-6 rounded-3xl bg-surface border border-border shadow-sm space-y-4">
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-4 h-4 text-primary" />
            <h4 className="font-bold text-text-primary text-sm tracking-tight">
              Univariate Moments & Quantile Distribution Summary
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
                  <th className="py-2.5 px-3">P25</th>
                  <th className="py-2.5 px-3">P75</th>
                  <th className="py-2.5 px-3">IQR</th>
                  <th className="py-2.5 px-3">Skewness</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {statistics.univariate_metrics.map((um) => (
                  <tr key={um.column_name} className="hover:bg-surface-accent/10 transition-colors">
                    <td className="py-2.5 px-3 font-semibold text-text-primary font-mono">{um.column_name}</td>
                    <td className="py-2.5 px-3 text-text-secondary">{um.mean.toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-text-secondary">{um.median.toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-text-secondary">{um.min.toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-text-secondary">{um.max.toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-text-secondary">{um.std.toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-text-secondary">{um.p25.toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-text-secondary">{um.p75.toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-text-secondary">{um.iqr.toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-text-secondary">{um.skewness !== null ? um.skewness : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 2. Correlation Pairs Matrix */}
      {statistics?.correlation_results?.length > 0 && (
        <div className="p-6 rounded-3xl bg-surface border border-border shadow-sm space-y-4">
          <div className="flex items-center space-x-2">
            <GitCommit className="w-4 h-4 text-primary" />
            <h4 className="font-bold text-text-primary text-sm tracking-tight">
              Bivariate Correlation Matrix & Significance
            </h4>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {statistics.correlation_results.map((cp, idx) => (
              <div
                key={idx}
                className="p-4 rounded-2xl bg-surface-accent/15 border border-border flex items-center justify-between text-xs"
              >
                <div className="space-y-1">
                  <div className="font-semibold text-text-primary font-mono">
                    {cp.col1} <span className="text-text-secondary">vs</span> {cp.col2}
                  </div>
                  <div className="text-[11px] text-text-secondary">
                    Pearson r = <b>{cp.pearson_coef}</b> • Spearman r = <b>{cp.spearman_coef}</b>
                  </div>
                </div>

                <div className="text-right space-y-1">
                  <span className="inline-block px-2 py-0.5 rounded-md text-[10px] font-bold bg-surface border border-border text-text-primary">
                    {cp.strength}
                  </span>
                  <div>
                    {cp.is_statistically_significant ? (
                      <span className="text-[10px] text-primary font-semibold">p &lt; 0.05 (Sig)</span>
                    ) : (
                      <span className="text-[10px] text-text-secondary">p = {cp.pearson_pvalue || 'N/A'}</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 3. Executed SQL Queries Log */}
      {sql_results?.results?.length > 0 && (
        <div className="p-6 rounded-3xl bg-surface border border-border shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Database className="w-4 h-4 text-primary" />
              <h4 className="font-bold text-text-primary text-sm tracking-tight">
                Executed DuckDB Analytical Queries
              </h4>
            </div>
            <span className="text-xs text-text-secondary font-mono">
              {sql_results.successful_queries}/{sql_results.total_queries} Successful
            </span>
          </div>

          <div className="space-y-4">
            {sql_results.results.map((sq, idx) => (
              <div
                key={idx}
                className="p-4 rounded-2xl bg-surface-accent/10 border border-border space-y-3 text-xs"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono font-bold text-text-primary">{sq.query_name}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-md bg-primary/10 text-primary border border-primary/20 font-bold uppercase">
                      {sq.execution_status}
                    </span>
                  </div>
                  <div className="flex items-center space-x-3 text-text-secondary font-mono text-[11px]">
                    <span className="flex items-center space-x-1">
                      <Clock className="w-3 h-3" />
                      <span>{sq.execution_duration_ms}ms</span>
                    </span>
                    <span>{sq.row_count} rows</span>
                  </div>
                </div>

                <p className="text-text-secondary">{sq.purpose}</p>

                <div className="p-3 rounded-xl bg-surface-accent/30 font-mono text-[11px] text-text-primary overflow-x-auto border border-border">
                  <code>{sq.sql}</code>
                </div>

                {sq.rows?.length > 0 && (
                  <div className="overflow-x-auto max-h-40 border border-border/60 rounded-xl">
                    <table className="w-full text-left text-[11px]">
                      <thead className="bg-surface-accent/20 border-b border-border text-text-secondary font-mono">
                        <tr>
                          {sq.columns.map((c) => (
                            <th key={c} className="py-1.5 px-2">{c}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/60">
                        {sq.rows.slice(0, 3).map((r, rIdx) => (
                          <tr key={rIdx} className="hover:bg-surface-accent/10">
                            {sq.columns.map((c) => (
                              <td key={c} className="py-1.5 px-2 font-mono text-text-secondary">
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
