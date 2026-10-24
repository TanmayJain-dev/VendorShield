'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '../lib/api';
import { CaseSummary } from '../types/api';
import { ShieldAlert, CheckCircle2, Clock, FileText, ArrowRight, RefreshCw, AlertTriangle, ShieldX } from 'lucide-react';

export default function Dashboard() {
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCases = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getCases();
      setCases(data);
    } catch (err: any) {
      setError(err.message || 'Failed to connect to backend server');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCases();
  }, []);

  const passCount = cases.filter(c => c.recommendation === 'PASS').length;
  const reviewCount = cases.filter(c => c.recommendation === 'MANUAL_REVIEW').length;
  const blockCount = cases.filter(c => c.recommendation === 'BLOCK').length;

  return (
    <div className="space-y-6">
      {/* Top Banner / Hero */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <span>Pre-Payment Due Diligence Queue</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Reconciling accounts payable claims against public registries via TinyFish browser research.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchCases}
            disabled={loading}
            className="flex items-center gap-1.5 text-xs text-slate-300 hover:text-white bg-slate-900 border border-slate-700/60 px-3 py-1.5 rounded-md hover:bg-slate-800 transition disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
          <Link
            href="/upload"
            className="text-xs font-semibold bg-cyan-500 hover:bg-cyan-400 text-slate-950 px-3.5 py-1.5 rounded-md transition"
          >
            + New Intake
          </Link>
        </div>
      </div>

      {/* KPI Telemetry Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-[#0f172a]/70 border border-slate-800 rounded-lg p-4">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs uppercase font-mono tracking-wider">Total Evaluated</span>
            <FileText className="h-4 w-4 text-slate-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white">{cases.length}</div>
          <span className="text-[11px] text-slate-500 font-mono">Invoices processed</span>
        </div>

        <div className="bg-[#0f172a]/70 border border-amber-900/40 rounded-lg p-4">
          <div className="flex items-center justify-between text-amber-400 mb-2">
            <span className="text-xs uppercase font-mono tracking-wider">Manual Review</span>
            <AlertTriangle className="h-4 w-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-amber-400">{reviewCount}</div>
          <span className="text-[11px] text-slate-400 font-mono">Fail-closed checkpoints</span>
        </div>

        <div className="bg-[#0f172a]/70 border border-emerald-900/40 rounded-lg p-4">
          <div className="flex items-center justify-between text-emerald-400 mb-2">
            <span className="text-xs uppercase font-mono tracking-wider">Pass Recommended</span>
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-emerald-400">{passCount}</div>
          <span className="text-[11px] text-slate-400 font-mono">Clear evidence matches</span>
        </div>

        <div className="bg-[#0f172a]/70 border border-rose-900/40 rounded-lg p-4">
          <div className="flex items-center justify-between text-rose-400 mb-2">
            <span className="text-xs uppercase font-mono tracking-wider">Block / Critical</span>
            <ShieldX className="h-4 w-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-rose-400">{blockCount}</div>
          <span className="text-[11px] text-slate-400 font-mono">Critical hard gates triggered</span>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-rose-950/40 border border-rose-800/80 rounded-lg p-4 flex items-center justify-between text-rose-200 text-xs">
          <div className="flex items-center gap-2">
            <ShieldAlert className="h-4 w-4 text-rose-400 flex-shrink-0" />
            <span>{error}</span>
          </div>
          <button
            onClick={fetchCases}
            className="px-2.5 py-1 bg-rose-900/60 hover:bg-rose-800 rounded font-mono text-[11px] transition"
          >
            Retry Connection
          </button>
        </div>
      )}

      {/* Case Queue Table */}
      <div className="bg-[#0f172a]/70 border border-slate-800 rounded-lg overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-300 font-mono">
            Active Review Dossiers
          </h2>
          <span className="text-[11px] text-slate-500 font-mono">Auto-sorted by submission time</span>
        </div>

        {loading ? (
          <div className="p-8 text-center text-xs text-slate-400 font-mono">
            Loading dossiers from backend...
          </div>
        ) : cases.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-400">
            No invoices in queue. Click <Link href="/upload" className="text-cyan-400 underline">Intake Invoice</Link> to start.
          </div>
        ) : (
          <div className="divide-y divide-slate-800/60 overflow-x-auto">
            <table className="min-w-full text-left text-xs">
              <thead className="bg-[#0b0f19]/80 text-slate-400 font-mono uppercase text-[10px]">
                <tr>
                  <th className="px-4 py-2.5">Case Reference</th>
                  <th className="px-4 py-2.5">Supplier Name</th>
                  <th className="px-4 py-2.5">Invoice Amount</th>
                  <th className="px-4 py-2.5">Status</th>
                  <th className="px-4 py-2.5">Recommendation</th>
                  <th className="px-4 py-2.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40 text-slate-200">
                {cases.map((c) => (
                  <tr key={c.case_id} className="hover:bg-slate-800/30 transition">
                    <td className="px-4 py-3 font-mono font-medium text-cyan-300">
                      {c.case_reference}
                    </td>
                    <td className="px-4 py-3 font-medium">
                      {c.supplier_name}
                    </td>
                    <td className="px-4 py-3 font-mono">
                      ₹{c.total_amount?.toLocaleString('en-IN', { minimumFractionDigits: 2 }) || '0.00'}
                    </td>
                    <td className="px-4 py-3">
                      <span className="inline-block text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                        {c.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {c.recommendation === 'PASS' && (
                        <span className="inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800/60 font-semibold">
                          <CheckCircle2 className="h-3 w-3" /> PASS
                        </span>
                      )}
                      {c.recommendation === 'MANUAL_REVIEW' && (
                        <span className="inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded bg-amber-950/80 text-amber-400 border border-amber-800/60 font-semibold">
                          <AlertTriangle className="h-3 w-3" /> MANUAL REVIEW
                        </span>
                      )}
                      {c.recommendation === 'BLOCK' && (
                        <span className="inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded bg-rose-950/80 text-rose-400 border border-rose-800/60 font-semibold">
                          <ShieldX className="h-3 w-3" /> BLOCK
                        </span>
                      )}
                      {!c.recommendation && (
                        <span className="text-[11px] text-slate-500 font-mono">PENDING RUN</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Link
                        href={`/cases/${c.case_id}`}
                        className="inline-flex items-center gap-1 text-xs text-cyan-400 hover:text-cyan-300 font-medium hover:underline"
                      >
                        <span>Open Dossier</span>
                        <ArrowRight className="h-3.5 w-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
