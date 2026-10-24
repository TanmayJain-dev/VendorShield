'use client';

import { useEffect, useState, useMemo } from 'react';
import Link from 'next/link';
import { api } from '../../lib/api';
import { CaseSummary } from '../../types/api';
import {
  RotateCcw,
  Plus,
  Search,
  ArrowUpRight,
  AlertCircle,
  ShieldCheck,
  AlertTriangle,
  ShieldAlert,
  Clock,
  ArrowLeft,
  X,
  FileText,
  Download,
  Filter
} from 'lucide-react';

export default function QueuePage() {
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'MANUAL_REVIEW' | 'PASS' | 'BLOCK' | 'PENDING'>('ALL');
  const [includeDemo, setIncludeDemo] = useState(true);

  const fetchCases = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getCases(includeDemo);
      setCases(data);
    } catch (err: any) {
      setError(err.message || 'Failed to connect to backend server.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCases();
  }, [includeDemo]);

  const passCount = useMemo(() => cases.filter((c) => c.recommendation === 'PASS').length, [cases]);
  const reviewCount = useMemo(() => cases.filter((c) => c.recommendation === 'MANUAL_REVIEW').length, [cases]);
  const blockCount = useMemo(() => cases.filter((c) => c.recommendation === 'BLOCK').length, [cases]);
  const pendingCount = useMemo(() => cases.filter((c) => !c.recommendation).length, [cases]);

  const filteredCases = useMemo(() => {
    return cases.filter((c) => {
      if (statusFilter === 'PASS' && c.recommendation !== 'PASS') return false;
      if (statusFilter === 'MANUAL_REVIEW' && c.recommendation !== 'MANUAL_REVIEW') return false;
      if (statusFilter === 'BLOCK' && c.recommendation !== 'BLOCK') return false;
      if (statusFilter === 'PENDING' && c.recommendation) return false;

      if (!includeDemo && (c.is_demo || c.source_mode === 'DEMO')) return false;

      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const refMatch = c.case_reference.toLowerCase().includes(q);
        const nameMatch = c.supplier_name.toLowerCase().includes(q);
        const invMatch = c.invoice_number?.toLowerCase().includes(q);
        const gstinMatch = c.gstin_claim?.toLowerCase().includes(q);
        const idMatch = c.case_id.toLowerCase().includes(q);
        return refMatch || nameMatch || invMatch || gstinMatch || idMatch;
      }
      return true;
    });
  }, [cases, statusFilter, includeDemo, searchQuery]);

  const exportCsv = () => {
    const headers = [
      'Case Reference',
      'Case ID',
      'Supplier Name',
      'GSTIN Claim',
      'Invoice Number',
      'Gross Amount (INR)',
      'Recommendation',
      'Policy Index Score',
      'Review Status',
      'Is Demo',
      'Created At'
    ];
    const rows = filteredCases.map((c) => [
      `"${c.case_reference}"`,
      `"${c.case_id}"`,
      `"${(c.supplier_name || '').replace(/"/g, '""')}"`,
      `"${c.gstin_claim || ''}"`,
      `"${c.invoice_number || ''}"`,
      c.total_amount || 0,
      c.recommendation || 'PENDING',
      c.risk_score ?? '',
      c.review_status || 'AWAITING_REVIEW',
      c.is_demo || c.source_mode === 'DEMO' ? 'YES' : 'NO',
      `"${c.created_at || ''}"`
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `VendorShield_Queue_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-6 animate-reveal-up">
      {/* Header & Primary Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Link
              href="/"
              className="inline-flex items-center space-x-1 text-xs text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200 transition-colors mr-2"
            >
              <ArrowLeft className="h-3 w-3" />
              <span>Back to Overview</span>
            </Link>
            <span className="text-[11px] px-2 py-0.5 rounded-full font-semibold bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 border border-teal-200 dark:border-teal-800/60">
              Live AP Pipeline
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 mt-1.5">
            Verification Queue
          </h1>
          <p className="text-xs sm:text-sm text-zinc-500 dark:text-zinc-400 mt-1 max-w-2xl leading-relaxed">
            Autonomous due-diligence dossiers, extracted claims reconciliation, and governed pre-payment risk recommendations.
          </p>
        </div>

        <div className="flex items-center space-x-2.5 shrink-0 flex-wrap">
          <button
            onClick={exportCsv}
            disabled={filteredCases.length === 0}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium text-zinc-700 dark:text-zinc-300 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800/60 transition-colors shadow-subtle disabled:opacity-50"
            title="Download CSV of current queue"
          >
            <Download className="h-3.5 w-3.5 text-zinc-400" />
            <span>Export CSV</span>
          </button>

          <button
            onClick={fetchCases}
            disabled={loading}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium text-zinc-700 dark:text-zinc-300 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800/60 transition-colors shadow-subtle disabled:opacity-50"
          >
            <RotateCcw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          <Link
            href="/upload"
            className="group inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-md text-xs font-semibold text-white bg-teal-700 hover:bg-teal-600 dark:bg-teal-600 dark:hover:bg-teal-500 transition-all duration-200 shadow-sm hover:shadow-teal-500/20 active:scale-95"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Intake Invoice</span>
          </Link>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        {/* Metric 1: Total */}
        <div className="bg-white dark:bg-[#0e1420] border border-zinc-200/90 dark:border-zinc-800/90 rounded-xl p-4 shadow-subtle">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
              Total Invoices
            </span>
            <FileText className="h-3.5 w-3.5 text-zinc-400" />
          </div>
          <div className="text-2xl sm:text-3xl font-bold text-zinc-900 dark:text-zinc-100 mt-2 tabular-nums">
            {cases.length}
          </div>
          <div className="text-[11px] text-zinc-400 mt-1">Under due diligence review</div>
        </div>

        {/* Metric 2: Pass */}
        <div className="bg-white dark:bg-[#0e1420] border border-zinc-200/90 dark:border-zinc-800/90 rounded-xl p-4 shadow-subtle">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-emerald-700 dark:text-emerald-400">
              Low Risk (Pass)
            </span>
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          </div>
          <div className="text-2xl sm:text-3xl font-bold text-emerald-700 dark:text-emerald-400 mt-2 tabular-nums">
            {passCount}
          </div>
          <div className="text-[11px] text-zinc-400 mt-1">Grounded &amp; verified clean</div>
        </div>

        {/* Metric 3: Manual Review */}
        <div className="bg-white dark:bg-[#0e1420] border border-zinc-200/90 dark:border-zinc-800/90 rounded-xl p-4 shadow-subtle">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-amber-700 dark:text-amber-400">
              Manual Review
            </span>
            <span className="w-2 h-2 rounded-full bg-amber-500" />
          </div>
          <div className="text-2xl sm:text-3xl font-bold text-amber-700 dark:text-amber-400 mt-2 tabular-nums">
            {reviewCount}
          </div>
          <div className="text-[11px] text-zinc-400 mt-1">Fails closed (Requires Registry/Signoff)</div>
        </div>

        {/* Metric 4: Block */}
        <div className="bg-white dark:bg-[#0e1420] border border-zinc-200/90 dark:border-zinc-800/90 rounded-xl p-4 shadow-subtle">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-rose-700 dark:text-rose-400">
              High Risk (Block)
            </span>
            <span className="w-2 h-2 rounded-full bg-rose-500" />
          </div>
          <div className="text-2xl sm:text-3xl font-bold text-rose-700 dark:text-rose-400 mt-2 tabular-nums">
            {blockCount}
          </div>
          <div className="text-[11px] text-zinc-400 mt-1">Confirmed defects or cancelled GST</div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white dark:bg-[#0e1420] border border-zinc-200/90 dark:border-zinc-800/90 rounded-xl p-3 shadow-subtle flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-zinc-400" />
          <input
            type="text"
            placeholder="Search by vendor name, invoice reference, GSTIN, or Case ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-8 py-1.5 text-xs bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-200 dark:border-zinc-800 rounded-md text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none focus:ring-1 focus:ring-teal-500 transition-colors"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 p-0.5 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200"
              aria-label="Clear search query"
            >
              <X className="h-3 w-3" />
            </button>
          )}
        </div>

        {/* Demo Cases Toggle & Status Filter */}
        <div className="flex items-center gap-2 flex-wrap">
          <label className="inline-flex items-center space-x-1.5 text-xs text-zinc-600 dark:text-zinc-400 cursor-pointer select-none px-2 py-1 border border-zinc-200 dark:border-zinc-800 rounded-lg bg-zinc-50 dark:bg-zinc-900/40">
            <input
              type="checkbox"
              checked={includeDemo}
              onChange={(e) => setIncludeDemo(e.target.checked)}
              className="rounded border-zinc-300 text-teal-600 focus:ring-teal-500 h-3.5 w-3.5"
            />
            <span>Show Demo Cases</span>
          </label>

          {/* Status Filter Buttons */}
          <div className="flex items-center space-x-1 border border-zinc-200 dark:border-zinc-800 rounded-lg p-0.5 bg-zinc-50 dark:bg-zinc-900/40 text-xs shrink-0">
            {(['ALL', 'PASS', 'MANUAL_REVIEW', 'BLOCK', 'PENDING'] as const).map((status) => (
              <button
                key={status}
                onClick={() => setStatusFilter(status)}
                className={`px-2 py-1 rounded-md text-[11px] font-semibold transition-all ${
                  statusFilter === status
                    ? 'bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 shadow-sm'
                    : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-300'
                }`}
              >
                {status === 'ALL'
                  ? `All (${cases.length})`
                  : status === 'PASS'
                  ? `Pass (${passCount})`
                  : status === 'MANUAL_REVIEW'
                  ? `Review (${reviewCount})`
                  : status === 'BLOCK'
                  ? `Block (${blockCount})`
                  : `Pending (${pendingCount})`}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Cases Table */}
      <div className="bg-white dark:bg-[#0e1420] border border-zinc-200/90 dark:border-zinc-800/90 rounded-xl shadow-subtle overflow-hidden">
        {error && (
          <div className="p-4 bg-rose-50 dark:bg-rose-950/20 border-b border-rose-200 dark:border-rose-900/50 flex items-center space-x-2 text-rose-800 dark:text-rose-300 text-xs">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-zinc-200/80 dark:border-zinc-800/80 bg-zinc-50/75 dark:bg-zinc-900/40 text-zinc-500 dark:text-zinc-400 font-semibold text-[11px] uppercase tracking-wider">
                <th className="py-3 px-4">Case Reference</th>
                <th className="py-3 px-4">Supplier Identity</th>
                <th className="py-3 px-4">Invoice / Amount</th>
                <th className="py-3 px-4">Recommendation</th>
                <th className="py-3 px-4">Policy Index</th>
                <th className="py-3 px-4">Review Status</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-200/70 dark:divide-zinc-800/70 text-zinc-700 dark:text-zinc-300">
              {loading && cases.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-14 text-center text-zinc-400 text-xs">
                    <div className="flex flex-col items-center justify-center space-y-2.5">
                      <RotateCcw className="h-5 w-5 animate-spin text-teal-600 dark:text-teal-400" />
                      <span>Loading verification pipeline...</span>
                    </div>
                  </td>
                </tr>
              ) : filteredCases.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-14 text-center text-zinc-400 text-xs">
                    <div className="space-y-1">
                      <p className="font-medium text-zinc-600 dark:text-zinc-300">No matching dossiers found</p>
                      <p className="text-[11px]">Try adjusting your search query, demo toggle, or status filter.</p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredCases.map((c) => {
                  const isCaseDemo = c.is_demo || c.source_mode === 'DEMO';
                  return (
                    <tr
                      key={c.case_id}
                      className="hover:bg-zinc-50/80 dark:hover:bg-zinc-850/40 transition-colors group"
                    >
                      {/* Reference */}
                      <td className="py-3.5 px-4">
                        <div className="flex items-center space-x-1.5">
                          <Link
                            href={`/cases/${c.case_id}`}
                            className="font-mono text-xs font-semibold text-teal-700 dark:text-teal-400 hover:underline block"
                          >
                            {c.case_reference}
                          </Link>
                          {isCaseDemo && (
                            <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-amber-500/15 text-amber-500 border border-amber-500/30 font-semibold">
                              DEMO DATA
                            </span>
                          )}
                        </div>
                        <span className="text-[10px] text-zinc-400">
                          {c.created_at ? new Date(c.created_at).toLocaleDateString() : 'Recent'}
                        </span>
                      </td>

                      {/* Supplier Identity */}
                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-zinc-900 dark:text-zinc-100">
                          {c.supplier_name}
                        </div>
                        <div className="text-[10px] font-mono text-zinc-400">
                          {c.gstin_claim || 'GSTIN unextracted'}
                        </div>
                      </td>

                      {/* Invoice Details */}
                      <td className="py-3.5 px-4">
                        <div className="font-mono text-zinc-800 dark:text-zinc-200">
                          {c.invoice_number || 'N/A'}
                        </div>
                        <div className="text-[11.5px] font-bold text-zinc-900 dark:text-zinc-100 tabular-nums">
                          {c.total_amount ? `₹${c.total_amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '₹0.00'}
                        </div>
                      </td>

                      {/* Recommendation */}
                      <td className="py-3.5 px-4">
                        {c.recommendation === 'PASS' ? (
                          <span className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded text-[10.5px] font-semibold bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-700/60 shadow-sm">
                            <ShieldCheck className="h-3 w-3 text-emerald-600 dark:text-emerald-400" />
                            <span>PASS</span>
                          </span>
                        ) : c.recommendation === 'MANUAL_REVIEW' ? (
                          <span className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded text-[10.5px] font-semibold bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-700/60 shadow-sm">
                            <AlertTriangle className="h-3 w-3 text-amber-600 dark:text-amber-400" />
                            <span>MANUAL REVIEW</span>
                          </span>
                        ) : c.recommendation === 'BLOCK' ? (
                          <span className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded text-[10.5px] font-semibold bg-rose-50 dark:bg-rose-950/40 text-rose-800 dark:text-rose-300 border border-rose-300 dark:border-rose-700/60 shadow-sm">
                            <ShieldAlert className="h-3 w-3 text-rose-600 dark:text-rose-400" />
                            <span>BLOCK</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded text-[10.5px] font-medium bg-slate-100 dark:bg-slate-800/80 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                            <Clock className="h-3 w-3 text-slate-400" />
                            <span>PENDING</span>
                          </span>
                        )}
                      </td>

                      {/* Risk Score / Policy Index */}
                      <td className="py-3.5 px-4">
                        {c.risk_score !== undefined && c.risk_score !== null ? (
                          <div className="flex items-center space-x-2">
                            <div className="text-xs font-mono font-bold tabular-nums text-zinc-900 dark:text-zinc-100">
                              {c.risk_score}
                              <span className="text-[10px] text-zinc-400 font-sans font-normal">/100</span>
                            </div>
                            <div className="w-14 h-1.5 bg-zinc-100 dark:bg-zinc-800 rounded-full overflow-hidden">
                              <div
                                className={`h-full ${
                                  c.risk_score >= 60
                                    ? 'bg-rose-500'
                                    : c.risk_score >= 25
                                    ? 'bg-amber-500'
                                    : 'bg-emerald-500'
                                }`}
                                style={{ width: `${Math.min(100, c.risk_score)}%` }}
                              />
                            </div>
                          </div>
                        ) : (
                          <span className="text-zinc-400 text-[11px]">—</span>
                        )}
                      </td>

                      {/* Review Status */}
                      <td className="py-3.5 px-4 text-[11px]">
                        {c.review_status === 'APPROVED' ? (
                          <span className="text-emerald-700 dark:text-emerald-400 font-semibold">Approved</span>
                        ) : c.review_status === 'REJECTED' ? (
                          <span className="text-rose-700 dark:text-rose-400 font-semibold">Rejected</span>
                        ) : c.review_status === 'FLAGGED' ? (
                          <span className="text-amber-700 dark:text-amber-400 font-semibold">Flagged Exception</span>
                        ) : (
                          <span className="text-zinc-400">Awaiting Sign-off</span>
                        )}
                      </td>

                      {/* Action */}
                      <td className="py-3.5 px-4 text-right">
                        <Link
                          href={`/cases/${c.case_id}`}
                          className="group inline-flex items-center space-x-1 px-3 py-1 rounded-md text-[11px] font-semibold text-teal-700 dark:text-teal-400 bg-teal-50 dark:bg-teal-950/20 hover:bg-teal-100 dark:hover:bg-teal-900/40 border border-teal-200 dark:border-teal-800/60 transition-colors shadow-subtle"
                        >
                          <span>Open Dossier</span>
                          <ArrowUpRight className="h-3 w-3 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                        </Link>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
