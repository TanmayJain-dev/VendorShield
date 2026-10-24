'use client';

import { use, useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '../../../lib/api';
import { Case, ReviewActionType, CheckStatus } from '../../../types/api';
import {
  ArrowLeft,
  RotateCcw,
  Download,
  Lock,
  ExternalLink,
  AlertCircle,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  ShieldCheck,
  ShieldAlert,
  ShieldX,
  FileText,
  Building2,
  Database,
  Globe,
  UserCheck,
  Check
} from 'lucide-react';

export default function CaseDossierPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const caseId = resolvedParams.id;

  const [caseData, setCaseData] = useState<Case | null>(null);
  const [loading, setLoading] = useState(true);
  const [investigating, setInvestigating] = useState(false);
  const [reviewing, setReviewing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Review Form State
  const [reviewerId, setReviewerId] = useState('analyst_prachi');
  const [reviewAction, setReviewAction] = useState<ReviewActionType>('APPROVE_WITH_EXCEPTION');
  const [rationale, setRationale] = useState('');

  const fetchCase = async () => {
    setLoading(true);
    try {
      const data = await api.getCase(caseId);
      setCaseData(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load case record.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCase();
  }, [caseId]);

  const handleRunInvestigation = async () => {
    setInvestigating(true);
    setError(null);
    try {
      const updated = await api.triggerInvestigation(caseId);
      setCaseData(updated);
    } catch (err: any) {
      setError(err.message || 'TinyFish investigation encountered an error.');
    } finally {
      setInvestigating(false);
    }
  };

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setReviewing(true);
    setError(null);
    try {
      const updated = await api.submitReview(caseId, {
        reviewer_id: reviewerId,
        action: reviewAction,
        rationale: rationale,
        requested_documents: [],
      });
      setCaseData(updated);
    } catch (err: any) {
      setError(err.message || 'Failed to record review decision.');
    } finally {
      setReviewing(false);
    }
  };

  const handleDownloadReport = async () => {
    try {
      const reportMd = await api.getAuditReport(caseId);
      const blob = new Blob([reportMd], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `VendorShield_Audit_${caseData?.case_reference || caseId}.md`;
      a.click();
    } catch (err: any) {
      alert('Could not download audit report: ' + err.message);
    }
  };

  const formatINR = (val?: number) => {
    if (val === undefined || val === null) return '₹0.00';
    return `₹${val.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  if (loading) {
    return (
      <div className="py-24 text-center space-y-3 text-xs text-zinc-500 animate-reveal-up">
        <RotateCcw className="h-6 w-6 animate-spin mx-auto text-teal-600 dark:text-teal-400" />
        <p className="font-medium text-zinc-700 dark:text-zinc-300">Retrieving evidence dossier {caseId}...</p>
      </div>
    );
  }

  if (!caseData || !caseData.invoice) {
    return (
      <div className="py-20 text-center space-y-3">
        <p className="text-xs text-rose-600 dark:text-rose-400 font-medium">Case or invoice claim not found.</p>
        <Link href="/queue" className="text-xs text-teal-700 dark:text-teal-400 font-semibold hover:underline">
          &larr; Return to Cases Queue
        </Link>
      </div>
    );
  }

  const { invoice, assessment, evidence_items, review, source_mode } = caseData;

  return (
    <div className="max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-6 animate-reveal-up">
      {/* Top Breadcrumb & Cryptographic Fingerprint */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs pb-1">
        <Link
          href="/queue"
          className="inline-flex items-center space-x-1.5 text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200 transition-colors font-medium"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to Verification Queue</span>
        </Link>

        {caseData.audit_hash_sha256 && (
          <div className="flex items-center space-x-1.5 text-[11px] text-zinc-400 font-mono bg-zinc-100/60 dark:bg-zinc-900/60 px-2.5 py-1 rounded-md border border-zinc-200/60 dark:border-zinc-800/60">
            <Lock className="h-3 w-3 text-teal-600 dark:text-teal-400" />
            <span className="text-zinc-500">SHA-256:</span>
            <code className="text-zinc-700 dark:text-zinc-300 font-semibold">
              {caseData.audit_hash_sha256.substring(0, 20)}...
            </code>
          </div>
        )}
      </div>

      {/* Case Header & Actions Bar */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 pb-5 border-b border-zinc-200/90 dark:border-zinc-800/90">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <span className="font-mono text-xs font-bold text-teal-700 dark:text-teal-400">
              {caseData.case_reference}
            </span>
            <span className="text-zinc-300 dark:text-zinc-700">&bull;</span>
            <span className="font-mono text-[11px] text-zinc-400">
              {caseData.case_id}
            </span>
            <span className="text-zinc-300 dark:text-zinc-700">&bull;</span>
            <span className="text-[11px] font-semibold text-zinc-600 dark:text-zinc-400">
              {source_mode === 'SIMULATED' ? 'Simulated Evidence' : 'Live TinyFish'}
            </span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
            {invoice.supplier_name}
          </h1>
          <div className="text-xs text-zinc-500 dark:text-zinc-400">
            Invoice #{invoice.invoice_number} &bull; Total Claimed: <strong className="text-zinc-900 dark:text-zinc-100 font-mono">{formatINR(invoice.total_amount)}</strong>
          </div>
        </div>

        <div className="flex items-center space-x-2.5 shrink-0">
          <button
            type="button"
            onClick={handleDownloadReport}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-semibold text-zinc-700 dark:text-zinc-300 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800/80 transition-colors shadow-subtle"
          >
            <Download className="h-3.5 w-3.5" />
            <span>Export Audit Trail</span>
          </button>

          {caseData.status === 'PARSED' && (
            <button
              type="button"
              onClick={handleRunInvestigation}
              disabled={investigating}
              className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-md text-xs font-semibold text-white bg-teal-700 hover:bg-teal-600 dark:bg-teal-600 dark:hover:bg-teal-500 transition-colors shadow-subtle disabled:opacity-50"
            >
              <RotateCcw className={`h-3.5 w-3.5 ${investigating ? 'animate-spin' : ''}`} />
              <span>{investigating ? 'Running TinyFish...' : 'Run Investigation'}</span>
            </button>
          )}

          {caseData.status !== 'PARSED' && !review && (
            <button
              type="button"
              onClick={handleRunInvestigation}
              disabled={investigating}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium text-zinc-700 dark:text-zinc-300 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-colors disabled:opacity-50"
            >
              <RotateCcw className={`h-3.5 w-3.5 ${investigating ? 'animate-spin' : ''}`} />
              <span>Re-run Investigation</span>
            </button>
          )}
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="p-3.5 rounded-lg bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/60 text-xs text-rose-800 dark:text-rose-300 flex items-center space-x-2">
          <AlertCircle className="h-4 w-4 text-rose-600 dark:text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Recommendation Banner — High-Contrast Authoritative Verdict */}
      {assessment ? (
        <div
          className={`p-5 sm:p-6 rounded-xl border text-xs space-y-3.5 shadow-subtle ${
            assessment.recommendation === 'PASS'
              ? 'border-emerald-300 dark:border-emerald-800/80 bg-emerald-50/70 dark:bg-emerald-950/30 text-emerald-950 dark:text-emerald-100'
              : assessment.recommendation === 'MANUAL_REVIEW'
              ? 'border-amber-300 dark:border-amber-800/80 bg-amber-50/70 dark:bg-amber-950/30 text-amber-950 dark:text-amber-100'
              : 'border-rose-300 dark:border-rose-800/80 bg-rose-50/70 dark:bg-rose-950/30 text-rose-950 dark:text-rose-100'
          }`}
        >
          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
            <div className="space-y-1.5">
              <div className="flex items-center space-x-2">
                {assessment.recommendation === 'PASS' && <ShieldCheck className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />}
                {assessment.recommendation === 'MANUAL_REVIEW' && <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400" />}
                {assessment.recommendation === 'BLOCK' && <ShieldAlert className="h-5 w-5 text-rose-600 dark:text-rose-400" />}
                <span className="font-bold text-sm tracking-tight uppercase">
                  VERDICT: {assessment.recommendation.replace(/_/g, ' ')}
                </span>
                <span className="text-zinc-400">&bull;</span>
                <span className="font-mono font-bold text-xs">
                  Risk Score: {assessment.risk_score ?? '—'}/100
                </span>
              </div>
              <p className="text-xs opacity-90 max-w-2xl leading-relaxed">
                {assessment.recommendation === 'MANUAL_REVIEW'
                  ? 'Field discrepancies or unverified claims detected. Fail-closed policy requires authorized sign-off.'
                  : assessment.recommendation === 'BLOCK'
                  ? 'Hard safety gate triggered. Suspended entity status or severe mismatch identified. Capital release halted.'
                  : 'All critical claims reconciled against authoritative public registers. Ready for human authorization.'}
              </p>
            </div>

            <div className="text-right text-[11px] text-zinc-500 dark:text-zinc-400 font-mono self-start sm:self-auto shrink-0">
              <div>Rule Engine v{assessment.ruleset_version}</div>
              <div>Completeness: {assessment.evidence_completeness}</div>
            </div>
          </div>

          {/* Reason Code Tags */}
          {assessment.reason_codes.length > 0 && (
            <div className="flex flex-wrap gap-1.5 pt-1">
              {assessment.reason_codes.map((rc) => (
                <span
                  key={rc}
                  className="px-2 py-0.5 rounded font-mono text-[10px] bg-white/80 dark:bg-black/30 border border-current opacity-80"
                >
                  {rc}
                </span>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-900/30 text-xs text-zinc-500 flex items-center justify-between">
          <span>Awaiting TinyFish evidence collection and deterministic risk evaluation.</span>
          <button
            onClick={handleRunInvestigation}
            disabled={investigating}
            className="px-3 py-1 rounded bg-teal-600 text-white font-medium text-xs hover:bg-teal-500"
          >
            {investigating ? 'Running...' : 'Run Investigation'}
          </button>
        </div>
      )}

      {/* Main Split Grid: Claims vs. Reconciliations */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Left Column: Supplier Claim Profile Card */}
        <div className="bg-white dark:bg-[#0e1420] border border-zinc-200/90 dark:border-zinc-800/90 rounded-xl p-5 space-y-4 shadow-subtle">
          <div className="text-xs font-semibold text-zinc-900 dark:text-zinc-100 pb-2 border-b border-zinc-100 dark:border-zinc-800/80">
            Invoice Claim Profile
          </div>

          <div className="space-y-3.5 text-xs">
            <div>
              <div className="text-[11px] text-zinc-400 font-medium">Declared Supplier</div>
              <div className="font-semibold text-zinc-900 dark:text-zinc-100 mt-0.5">
                {invoice.supplier_name}
              </div>
              {invoice.legal_name && (
                <div className="text-[11px] text-zinc-500">Legal: {invoice.legal_name}</div>
              )}
            </div>

            <div>
              <div className="text-[11px] text-zinc-400 font-medium">Supplier GSTIN</div>
              <div className="mt-0.5 flex items-center space-x-2">
                <span className="font-mono font-bold text-teal-700 dark:text-teal-300">
                  {invoice.gstin || 'Not extracted'}
                </span>
                {invoice.gstin_format_valid !== undefined && (
                  <span
                    className={`text-[9.5px] px-1.5 py-0.2 rounded font-semibold ${
                      invoice.gstin_format_valid
                        ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400'
                        : 'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-400'
                    }`}
                  >
                    {invoice.gstin_format_valid ? 'Luhn Valid' : 'Format Invalid'}
                  </span>
                )}
              </div>
            </div>

            <div>
              <div className="text-[11px] text-zinc-400 font-medium">Financial Breakdown</div>
              <div className="mt-0.5 space-y-1 font-medium text-zinc-900 dark:text-zinc-100 tabular-nums">
                <div className="font-bold text-sm">Total: {formatINR(invoice.total_amount)}</div>
                <div className="text-[11px] text-zinc-500">
                  Taxable: {formatINR(invoice.taxable_amount)}
                </div>
                {(invoice.cgst > 0 || invoice.sgst > 0 || invoice.igst > 0) && (
                  <div className="text-[10.5px] text-zinc-400 font-mono">
                    Tax: CGST {formatINR(invoice.cgst)} &bull; SGST {formatINR(invoice.sgst)} &bull; IGST {formatINR(invoice.igst)}
                  </div>
                )}
              </div>
            </div>

            <div>
              <div className="text-[11px] text-zinc-400 font-medium">Remittance Account</div>
              <div className="mt-0.5 font-mono text-zinc-700 dark:text-zinc-300 text-[11px]">
                {invoice.bank_account_masked || 'N/A'} (IFSC: {invoice.ifsc_code || 'N/A'})
              </div>
            </div>

            <div>
              <div className="text-[11px] text-zinc-400 font-medium">Billing Address</div>
              <div className="mt-0.5 text-zinc-600 dark:text-zinc-300 text-[11.5px] leading-relaxed">
                {invoice.billing_address || 'Not specified on invoice document'}
              </div>
            </div>
          </div>
        </div>

        {/* Center/Right Columns: Reconciliations & Evidence */}
        <div className="lg:col-span-2 space-y-6">
          {/* Section 2: Reconciled Checks */}
          <div className="bg-white dark:bg-[#0e1420] border border-zinc-200/90 dark:border-zinc-800/90 rounded-xl p-5 space-y-4 shadow-subtle">
            <div className="flex items-center justify-between pb-2 border-b border-zinc-100 dark:border-zinc-800/80">
              <span className="text-xs font-semibold text-zinc-900 dark:text-zinc-100">
                Deterministic Field Reconciliations
              </span>
              <span className="text-[11px] text-zinc-400 font-mono">
                {assessment?.field_checks.length ?? 0} checkpoints evaluated
              </span>
            </div>

            {assessment && assessment.field_checks.length > 0 ? (
              <div className="divide-y divide-zinc-100 dark:divide-zinc-800/60">
                {assessment.field_checks.map((chk) => (
                  <div key={chk.check_id} className="py-3.5 first:pt-0 last:pb-0 space-y-2 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-zinc-900 dark:text-zinc-100">
                        {chk.field_name}
                      </span>
                      <span
                        className={`inline-flex items-center space-x-1 text-[10px] font-semibold px-2 py-0.5 rounded border ${
                          chk.status === 'MATCH'
                            ? 'text-emerald-800 bg-emerald-50 border-emerald-200 dark:text-emerald-300 dark:bg-emerald-950/40 dark:border-emerald-800/60'
                            : chk.status === 'POSSIBLE_MATCH' || chk.status === 'STALE_OR_UNCLEAR'
                            ? 'text-amber-800 bg-amber-50 border-amber-200 dark:text-amber-300 dark:bg-amber-950/40 dark:border-amber-800/60'
                            : chk.status === 'MISMATCH'
                            ? 'text-rose-800 bg-rose-50 border-rose-200 dark:text-rose-300 dark:bg-rose-950/40 dark:border-rose-800/60'
                            : 'text-slate-700 bg-slate-100 border-slate-200 dark:text-slate-300 dark:bg-slate-800/60 dark:border-slate-700'
                        }`}
                      >
                        {chk.status === 'MATCH' && <CheckCircle2 className="h-3 w-3 text-emerald-600 dark:text-emerald-400" />}
                        {(chk.status === 'POSSIBLE_MATCH' || chk.status === 'STALE_OR_UNCLEAR') && <AlertTriangle className="h-3 w-3 text-amber-600 dark:text-amber-400" />}
                        {chk.status === 'MISMATCH' && <XCircle className="h-3 w-3 text-rose-600 dark:text-rose-400" />}
                        {(chk.status === 'NOT_FOUND' || chk.status === 'UNAVAILABLE' || chk.status === 'NOT_APPLICABLE') && <HelpCircle className="h-3 w-3 text-slate-500" />}
                        <span>{chk.status.replace(/_/g, ' ')}</span>
                      </span>
                    </div>

                    <p className="text-zinc-600 dark:text-zinc-300 leading-relaxed text-[11.5px]">
                      {chk.explanation}
                    </p>

                    {(chk.invoice_value || chk.evidence_value) && (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1 text-[11px]">
                        {chk.invoice_value && (
                          <div className="p-2.5 rounded-lg bg-zinc-50 dark:bg-zinc-900 border border-zinc-200/70 dark:border-zinc-800/70">
                            <span className="text-[10px] text-zinc-400 font-semibold block uppercase">Invoice Value</span>
                            <span className="font-mono font-medium text-zinc-800 dark:text-zinc-200">{chk.invoice_value}</span>
                          </div>
                        )}
                        {chk.evidence_value && (
                          <div className="p-2.5 rounded-lg bg-zinc-50 dark:bg-zinc-900 border border-zinc-200/70 dark:border-zinc-800/70">
                            <span className="text-[10px] text-zinc-400 font-semibold block uppercase">Public Evidence Value</span>
                            <span className="font-mono font-medium text-zinc-800 dark:text-zinc-200">{chk.evidence_value}</span>
                          </div>
                        )}
                      </div>
                    )}

                    {chk.source_url && (
                      <div className="pt-0.5">
                        <a
                          href={chk.source_url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center space-x-1 text-[11px] text-teal-700 dark:text-teal-400 hover:underline font-medium"
                        >
                          <span>Evidence Source Citation</span>
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-6 text-center text-xs text-zinc-400">
                No checkpoints generated yet. Run the TinyFish investigation above.
              </div>
            )}
          </div>

          {/* Section 3: Evidence Provenance Log */}
          {evidence_items.length > 0 && (
            <div className="bg-white dark:bg-[#0e1420] border border-zinc-200/90 dark:border-zinc-800/90 rounded-xl p-5 space-y-4 shadow-subtle">
              <div className="flex items-center justify-between pb-2 border-b border-zinc-100 dark:border-zinc-800/80 text-xs">
                <span className="font-semibold text-zinc-900 dark:text-zinc-100">
                  Raw Evidence Provenance Trail ({evidence_items.length})
                </span>
                <span className="text-[11px] text-zinc-400 font-mono">Public Web Citations</span>
              </div>

              <div className="space-y-3">
                {evidence_items.map((ev) => (
                  <div
                    key={ev.evidence_id}
                    className="p-3.5 rounded-lg border border-zinc-200/70 dark:border-zinc-800/70 bg-zinc-50/50 dark:bg-zinc-900/30 text-xs space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-zinc-900 dark:text-zinc-100">
                        {ev.source_name}
                      </span>
                      <span className="text-[10px] text-zinc-400 font-mono">
                        {ev.retrieved_at}
                      </span>
                    </div>

                    <p className="font-mono text-[11px] text-zinc-700 dark:text-zinc-300 bg-white dark:bg-zinc-950 p-2.5 rounded-md border border-zinc-200/60 dark:border-zinc-900 leading-relaxed whitespace-pre-wrap">
                      {ev.raw_excerpt}
                    </p>

                    {ev.source_url && (
                      <a
                        href={ev.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center space-x-1 text-[11px] text-teal-700 dark:text-teal-400 hover:underline pt-0.5 truncate max-w-full font-medium"
                      >
                        <span className="truncate">{ev.source_url}</span>
                        <ExternalLink className="h-3 w-3 shrink-0" />
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Section 4: Human Reviewer Decision & Sign-Off Card */}
      <div className="bg-white dark:bg-[#0e1420] border border-zinc-200/90 dark:border-zinc-800/90 rounded-xl p-5 sm:p-6 space-y-4 shadow-subtle">
        <div className="flex items-center justify-between pb-3 border-b border-zinc-100 dark:border-zinc-800/80">
          <div className="flex items-center space-x-2">
            <Lock className="h-4 w-4 text-teal-600 dark:text-teal-400" />
            <span className="text-xs font-bold text-zinc-900 dark:text-zinc-100">
              Human Reviewer Authorization &amp; Cryptographic Audit Seal
            </span>
          </div>
          <span className="text-[11px] text-zinc-400 font-medium">
            Mandatory Human Dual-Custody
          </span>
        </div>

        {review ? (
          <div className="p-4 rounded-xl border border-emerald-300 dark:border-emerald-800/80 bg-emerald-50/40 dark:bg-emerald-950/20 text-xs space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="font-bold text-emerald-800 dark:text-emerald-300 flex items-center space-x-1.5">
                <Check className="h-4 w-4 text-emerald-600" />
                <span>Decision Recorded: {review.action.replace(/_/g, ' ')}</span>
              </span>
              <span className="text-[11px] text-zinc-400 font-mono">{review.recorded_at}</span>
            </div>
            <div className="text-zinc-700 dark:text-zinc-300">
              <span className="text-zinc-400">Authorized Reviewer:</span> <strong className="font-mono">{review.reviewer_id}</strong>
            </div>
            <div className="text-zinc-800 dark:text-zinc-200 pt-2 border-t border-emerald-200 dark:border-emerald-900/60">
              <span className="text-zinc-400 block text-[11px] font-semibold">Audit Rationale:</span>
              <p className="mt-1 leading-relaxed">{review.rationale}</p>
            </div>
          </div>
        ) : (
          <form onSubmit={handleReviewSubmit} className="space-y-4 text-xs">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-zinc-700 dark:text-zinc-300 mb-1 font-medium">
                  Reviewer Identifier <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={reviewerId}
                  onChange={(e) => setReviewerId(e.target.value)}
                  className="w-full px-3 py-2 font-mono bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-1 focus:ring-teal-500 font-semibold"
                />
              </div>

              <div>
                <label className="block text-zinc-700 dark:text-zinc-300 mb-1 font-medium">
                  Sign-Off Action <span className="text-rose-500">*</span>
                </label>
                <select
                  value={reviewAction}
                  onChange={(e) => setReviewAction(e.target.value as ReviewActionType)}
                  className="w-full px-3 py-2 bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-1 focus:ring-teal-500 font-semibold cursor-pointer"
                >
                  <option value="APPROVE">APPROVE (Clean Pass)</option>
                  <option value="APPROVE_WITH_EXCEPTION">APPROVE_WITH_EXCEPTION (Documented Override)</option>
                  <option value="REQUEST_DOCUMENTS">REQUEST_DOCUMENTS (Hold for Vendor)</option>
                  <option value="ESCALATE">ESCALATE (To AP Manager)</option>
                  <option value="REJECT">REJECT (Halt Payment)</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-zinc-700 dark:text-zinc-300 mb-1 font-medium">
                Audit Rationale &amp; Exception Documentation <span className="text-rose-500">*</span>
              </label>
              <textarea
                required
                rows={3}
                placeholder="Document your verification findings and justification for this sign-off decision..."
                value={rationale}
                onChange={(e) => setRationale(e.target.value)}
                className="w-full px-3 py-2 bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-1 focus:ring-teal-500 font-sans text-xs leading-relaxed"
              />
            </div>

            <div className="flex items-center justify-between pt-1">
              <span className="text-[11px] text-zinc-400">
                Action will be sealed with a SHA-256 cryptographic digest.
              </span>
              <button
                type="submit"
                disabled={reviewing || rationale.trim().length < 5}
                className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-lg text-xs font-semibold text-white bg-emerald-700 hover:bg-emerald-600 dark:bg-emerald-600 dark:hover:bg-emerald-500 transition-all duration-200 shadow-sm hover:shadow-emerald-500/20 active:scale-95 disabled:opacity-50"
              >
                <Lock className="h-3.5 w-3.5" />
                <span>{reviewing ? 'Sealing Case...' : 'Authorize & Seal Case'}</span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
