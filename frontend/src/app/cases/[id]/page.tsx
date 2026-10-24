'use client';

import { use, useEffect, useState } from 'react';
import { api } from '../../../lib/api';
import { Case, ReviewActionType, InvoiceCorrection } from '../../../types/api';
import { 
  ShieldAlert, 
  CheckCircle2, 
  AlertTriangle, 
  ShieldX, 
  ExternalLink, 
  RefreshCw, 
  Download, 
  Lock,
  Cpu,
  Edit3,
  Copy,
  History,
  Info
} from 'lucide-react';

export default function CaseDossierPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const caseId = resolvedParams.id;

  const [caseData, setCaseData] = useState<Case | null>(null);
  const [loading, setLoading] = useState(true);
  const [investigating, setInvestigating] = useState(false);
  const [reviewing, setReviewing] = useState(false);
  const [correcting, setCorrecting] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Review Form State
  const [reviewerId, setReviewerId] = useState('analyst_prachi');
  const [reviewAction, setReviewAction] = useState<ReviewActionType>('APPROVE_WITH_EXCEPTION');
  const [rationale, setRationale] = useState('');

  // Correction Form State
  const [corrSupplier, setCorrSupplier] = useState('');
  const [corrLegalName, setCorrLegalName] = useState('');
  const [corrGstin, setCorrGstin] = useState('');
  const [corrInvNumber, setCorrInvNumber] = useState('');
  const [corrTotalAmount, setCorrTotalAmount] = useState('');
  const [corrTaxableAmount, setCorrTaxableAmount] = useState('');
  const [corrNotes, setCorrNotes] = useState('');

  const fetchCase = async () => {
    setLoading(true);
    try {
      const data = await api.getCase(caseId);
      setCaseData(data);
      if (data.invoice) {
        setCorrSupplier(data.invoice.supplier_name || '');
        setCorrLegalName(data.invoice.legal_name || '');
        setCorrGstin(data.invoice.gstin || '');
        setCorrInvNumber(data.invoice.invoice_number || '');
        setCorrTotalAmount(data.invoice.total_amount ? String(data.invoice.total_amount) : '');
        setCorrTaxableAmount(data.invoice.taxable_amount ? String(data.invoice.taxable_amount) : '');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load case');
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
      setError(err.message || 'Investigation failed');
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
        requested_documents: []
      });
      setCaseData(updated);
    } catch (err: any) {
      setError(err.message || 'Failed to submit review');
    } finally {
      setReviewing(false);
    }
  };

  const handleCorrectionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setCorrecting(true);
    setError(null);
    try {
      const payload: InvoiceCorrection = {
        corrected_supplier_name: corrSupplier.trim() || undefined,
        corrected_legal_name: corrLegalName.trim() || undefined,
        corrected_gstin: corrGstin.trim() ? corrGstin.trim().toUpperCase() : undefined,
        corrected_invoice_number: corrInvNumber.trim() || undefined,
        corrected_total_amount: corrTotalAmount ? parseFloat(corrTotalAmount) : undefined,
        corrected_taxable_amount: corrTaxableAmount ? parseFloat(corrTaxableAmount) : undefined,
        correction_notes: corrNotes.trim() || 'Manual reviewer correction',
        reviewer_id: reviewerId
      };
      const updated = await api.correctInvoice(caseId, payload);
      setCaseData(updated);
      setShowEditModal(false);
    } catch (err: any) {
      setError(err.message || 'Failed to apply invoice corrections');
    } finally {
      setCorrecting(false);
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

  if (loading) {
    return (
      <div className="py-20 text-center text-xs font-mono text-slate-400">
        Loading case evidence dossier...
      </div>
    );
  }

  if (!caseData || !caseData.invoice) {
    return (
      <div className="py-20 text-center text-xs text-rose-400 font-mono">
        Case or invoice data not found.
      </div>
    );
  }

  const { invoice, assessment, evidence_items, review, source_mode, duplicate_type, review_history } = caseData;

  return (
    <div className="space-y-6">
      {/* Top Header & Telemetry */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2.5 flex-wrap">
            <span className="text-xs uppercase font-mono px-2 py-0.5 rounded bg-slate-800 text-cyan-400 border border-slate-700">
              {caseData.case_reference}
            </span>
            <span className="text-xs font-mono text-slate-400">Case ID: {caseData.case_id}</span>
            {source_mode === 'SIMULATED' ? (
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-amber-950/60 text-amber-400 border border-amber-800/60">
                Simulated Evidence Mode
              </span>
            ) : source_mode === 'LIVE' ? (
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800/60 flex items-center gap-1">
                <Cpu className="h-3 w-3" /> Live TinyFish Research
              </span>
            ) : (
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                Evidence Unavailable
              </span>
            )}
            {duplicate_type && (
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-rose-950/80 text-rose-300 border border-rose-800 flex items-center gap-1">
                <Copy className="h-3 w-3" /> {duplicate_type}
              </span>
            )}
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-white mt-1.5 flex items-center gap-2">
            <span>{invoice.supplier_name}</span>
            <span className="text-sm font-mono text-slate-400 font-normal">
              (&#8377;{invoice.total_amount.toLocaleString('en-IN')})
            </span>
          </h1>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowEditModal(true)}
            className="flex items-center gap-1.5 text-xs text-cyan-300 hover:text-white bg-slate-900 border border-cyan-800/60 px-3 py-1.5 rounded-md hover:bg-slate-800 transition"
          >
            <Edit3 className="h-3.5 w-3.5 text-cyan-400" />
            <span>Correct Claims</span>
          </button>

          <button
            onClick={handleDownloadReport}
            className="flex items-center gap-1.5 text-xs text-slate-300 hover:text-white bg-slate-900 border border-slate-700 px-3 py-1.5 rounded-md hover:bg-slate-800 transition"
          >
            <Download className="h-3.5 w-3.5 text-slate-400" />
            <span>Export Audit Trail</span>
          </button>

          {caseData.status === 'PARSED' && (
            <button
              onClick={handleRunInvestigation}
              disabled={investigating}
              className="flex items-center gap-2 text-xs font-semibold bg-cyan-500 hover:bg-cyan-400 text-slate-950 px-4 py-1.5 rounded-md transition disabled:opacity-50"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${investigating ? 'animate-spin' : ''}`} />
              <span>{investigating ? 'Running TinyFish...' : 'Run Investigation'}</span>
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="p-3 bg-rose-950/60 border border-rose-800 rounded text-rose-300 text-xs">
          {error}
        </div>
      )}

      {/* Duplicate Notice Banner */}
      {duplicate_type && (
        <div className="p-3 bg-amber-950/40 border border-amber-800 rounded-lg text-amber-200 text-xs flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-amber-400 flex-shrink-0" />
          <span>
            <strong>Duplicate Alert:</strong> Detected {duplicate_type} (Previous Case: {caseData.duplicate_of_case_id || 'System Archive'}). Please verify if this is an intentional reissue or duplicate submission before approval.
          </span>
        </div>
      )}

      {/* Scanned Image / OCR Alert */}
      {invoice.is_scanned_image && (
        <div className="p-3 bg-blue-950/40 border border-blue-800/80 rounded-lg text-blue-200 text-xs flex items-center gap-2">
          <Info className="h-4 w-4 text-blue-400 flex-shrink-0" />
          <span>
            <strong>Scanned Document:</strong> {invoice.ocr_status_message || 'Document has no native text layer. Review extracted values and use Correct Claims if necessary.'}
          </span>
        </div>
      )}

      {/* Recommendation Banner */}
      {assessment && (
        <div className={`rounded-xl p-5 border ${
          assessment.recommendation === 'PASS' 
            ? 'bg-emerald-950/30 border-emerald-800/70' 
            : assessment.recommendation === 'MANUAL_REVIEW'
            ? 'bg-amber-950/30 border-amber-800/70'
            : 'bg-rose-950/30 border-rose-800/70'
        }`}>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-start gap-3.5">
              {assessment.recommendation === 'PASS' && <CheckCircle2 className="h-6 w-6 text-emerald-400 flex-shrink-0 mt-0.5" />}
              {assessment.recommendation === 'MANUAL_REVIEW' && <AlertTriangle className="h-6 w-6 text-amber-400 flex-shrink-0 mt-0.5" />}
              {assessment.recommendation === 'BLOCK' && <ShieldX className="h-6 w-6 text-rose-400 flex-shrink-0 mt-0.5" />}
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-bold tracking-wide uppercase font-mono text-white">
                    Recommendation: {assessment.recommendation}
                  </h2>
                  <span className="text-xs font-mono text-slate-400">
                    &bull; Policy Compliance Score: <strong className="text-white">{assessment.risk_score}</strong>/100
                  </span>
                </div>
                <p className="text-xs text-slate-300 mt-1">
                  {assessment.recommendation === 'MANUAL_REVIEW' 
                    ? 'Discrepancies, missing evidence, or unverified fields detected. Fail-closed policy requires authorized human sign-off before payment.'
                    : assessment.recommendation === 'BLOCK'
                    ? 'Critical hard safety gate triggered. Suspended registration, duplicate invoice, or critical identity conflict detected.'
                    : 'Required claims reconciled with public evidence. Human sign-off required to finalize.'}
                </p>
                <p className="text-[11px] font-mono text-slate-400 mt-1">
                  {assessment.score_explanation}
                </p>

                {/* Reason Codes */}
                {assessment.reason_codes.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {assessment.reason_codes.map(rc => (
                      <span key={rc} className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900/90 text-amber-300 border border-amber-800/50">
                        {rc}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="text-right font-mono text-[11px] text-slate-400">
              <div>Rule Engine v{assessment.ruleset_version}</div>
              <div>Evidence: <strong className="text-slate-300">{assessment.evidence_completeness}</strong></div>
            </div>
          </div>
        </div>
      )}

      {/* Grid: Invoice Claims vs Reconciled Evidence */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Invoice Raw Claims */}
        <div className="bg-[#0f172a]/70 border border-slate-800 rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-300 font-mono">
              1. Extracted Invoice Claims
            </h2>
            <button
              onClick={() => setShowEditModal(true)}
              className="text-[11px] font-mono text-cyan-400 hover:underline flex items-center gap-1"
            >
              <Edit3 className="h-3 w-3" /> Edit
            </button>
          </div>
          <div className="space-y-3 text-xs">
            <div>
              <span className="text-[11px] font-mono text-slate-500 block">Supplier Trade Name</span>
              <span className="font-semibold text-white">{invoice.supplier_name}</span>
            </div>
            {invoice.legal_name && (
              <div>
                <span className="text-[11px] font-mono text-slate-500 block">Declared Legal Name</span>
                <span className="font-mono text-slate-300">{invoice.legal_name}</span>
              </div>
            )}
            <div>
              <span className="text-[11px] font-mono text-slate-500 block">GSTIN</span>
              <div className="flex items-center gap-2">
                <span className="font-mono text-cyan-300">{invoice.gstin || 'Not provided'}</span>
                {invoice.gstin_format_valid && (
                  <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 font-mono">
                    CHECKSUM VALID
                  </span>
                )}
              </div>
            </div>
            <div>
              <span className="text-[11px] font-mono text-slate-500 block">Invoice Total &amp; Tax</span>
              <span className="font-mono text-white">
                &#8377;{invoice.total_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })} (Taxable: &#8377;{invoice.taxable_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })})
              </span>
            </div>
            <div>
              <span className="text-[11px] font-mono text-slate-500 block">Tax Breakdown</span>
              <span className="font-mono text-slate-300 text-[11px]">
                CGST: &#8377;{invoice.cgst.toLocaleString('en-IN')} | SGST: &#8377;{invoice.sgst.toLocaleString('en-IN')} | IGST: &#8377;{invoice.igst.toLocaleString('en-IN')}
              </span>
            </div>
            <div>
              <span className="text-[11px] font-mono text-slate-500 block">Bank Account &amp; IFSC</span>
              <span className="font-mono text-slate-300">
                {invoice.bank_account_masked || 'N/A'} | IFSC: {invoice.ifsc_code || 'N/A'}
              </span>
            </div>
            <div>
              <span className="text-[11px] font-mono text-slate-500 block">Billing Address</span>
              <span className="text-slate-300">{invoice.billing_address || 'Not specified'}</span>
            </div>
          </div>
        </div>

        {/* Center & Right: Reconciled Checks & Provenance */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-[#0f172a]/70 border border-slate-800 rounded-lg p-5 space-y-4">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-300 font-mono border-b border-slate-800 pb-2">
              2. Deterministic Field Reconciliations
            </h2>

            {assessment && assessment.field_checks.length > 0 ? (
              <div className="divide-y divide-slate-800/60">
                {assessment.field_checks.map((chk) => (
                  <div key={chk.check_id} className="py-3 first:pt-0 last:pb-0 space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-slate-200">{chk.field_name}</span>
                      <div className="flex items-center gap-2">
                        {chk.source_mode && (
                          <span className="text-[9px] font-mono uppercase px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700">
                            {chk.source_mode}
                          </span>
                        )}
                        <span className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded font-semibold ${
                          chk.status === 'MATCH'
                            ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                            : chk.status === 'POSSIBLE_MATCH'
                            ? 'bg-amber-950 text-amber-400 border border-amber-800'
                            : chk.status === 'UNAVAILABLE'
                            ? 'bg-slate-800 text-slate-300 border border-slate-700'
                            : 'bg-rose-950 text-rose-400 border border-rose-800'
                        }`}>
                          {chk.status}
                        </span>
                      </div>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed">
                      {chk.explanation}
                    </p>
                    {chk.source_url && (
                      <div className="pt-1">
                        <a
                          href={chk.source_url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-[11px] font-mono text-cyan-400 hover:underline"
                        >
                          <span>Evidence Source Link</span>
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-slate-400 font-mono py-4">
                No reconciliation checks run yet. Click &apos;Run Investigation&apos; above.
              </div>
            )}
          </div>

          {/* Discovered Evidence Dossier View */}
          {evidence_items.length > 0 && (
            <div className="bg-[#0f172a]/70 border border-slate-800 rounded-lg p-5 space-y-3">
              <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-300 font-mono border-b border-slate-800 pb-2">
                3. Evidence Dossier &amp; Provenance Trail
              </h2>
              <div className="space-y-3">
                {evidence_items.map(ev => (
                  <div key={ev.evidence_id} className="p-3 bg-[#0b0f19] border border-slate-800 rounded text-xs space-y-1.5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-cyan-300">{ev.source_name}</span>
                        {ev.is_fallback ? (
                          <span className="text-[9px] font-mono uppercase px-1.5 py-0.2 rounded bg-amber-950 text-amber-400 border border-amber-800">
                            Simulated Fallback
                          </span>
                        ) : (
                          <span className="text-[9px] font-mono uppercase px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700">
                            {ev.source_mode || 'SIMULATED'}
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] font-mono text-slate-500">{ev.retrieved_at}</span>
                    </div>
                    {ev.fallback_reason && (
                      <p className="text-[11px] text-amber-300 font-mono">
                        Fallback notice: {ev.fallback_reason}
                      </p>
                    )}
                    <p className="text-slate-300 font-mono text-[11px] bg-slate-950 p-2 rounded border border-slate-900 leading-relaxed">
                      {ev.raw_excerpt}
                    </p>
                    {ev.match_rationale && (
                      <p className="text-[11px] text-slate-400 italic">
                        Rationale: {ev.match_rationale}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Reviewer Activity History Timeline */}
      {review_history && review_history.length > 0 && (
        <div className="bg-[#0f172a]/70 border border-slate-800 rounded-lg p-5 space-y-3">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
            <History className="h-4 w-4 text-cyan-400" />
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-300 font-mono">
              Reviewer Activity History ({review_history.length})
            </h2>
          </div>
          <div className="space-y-2">
            {review_history.map(rh => (
              <div key={rh.action_id} className="p-3 bg-[#0b0f19] border border-slate-800 rounded text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <span className="font-mono text-emerald-400 font-bold uppercase mr-2">[{rh.action}]</span>
                  <span className="text-slate-200">{rh.rationale}</span>
                </div>
                <div className="text-[11px] font-mono text-slate-400 flex items-center gap-2">
                  <span>{rh.reviewer_id}</span>
                  <span>&bull;</span>
                  <span>{rh.recorded_at}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Reviewer Action / Sign-Off Box */}
      <div className="bg-[#0f172a]/90 border border-slate-700 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Lock className="h-4 w-4 text-cyan-400" />
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-200 font-mono">
              4. Human Reviewer Decision &amp; Audit Seal
            </h2>
          </div>
          {caseData.audit_hash_sha256 && (
            <span className="text-[11px] font-mono text-slate-400">
              SHA-256: <code className="text-cyan-300">{caseData.audit_hash_sha256.substring(0, 16)}...</code>
            </span>
          )}
        </div>

        {review ? (
          <div className="p-4 bg-slate-900/80 border border-slate-700/80 rounded-lg text-xs space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-mono text-emerald-400 font-bold uppercase">
                &check; Decision Recorded: {review.action}
              </span>
              <span className="font-mono text-slate-500">{review.recorded_at}</span>
            </div>
            <div>
              <span className="text-slate-400 font-mono text-[11px]">Reviewer: </span>
              <span className="text-white font-medium">{review.reviewer_id} ({review.reviewer_role || 'ap_analyst'})</span>
            </div>
            <div>
              <span className="text-slate-400 font-mono text-[11px]">Audit Rationale: </span>
              <p className="text-slate-200 mt-0.5">{review.rationale}</p>
            </div>
          </div>
        ) : (
          <form onSubmit={handleReviewSubmit} className="space-y-4 text-xs">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-slate-400 font-mono text-[11px] mb-1">
                  Reviewer Identity
                </label>
                <input
                  type="text"
                  required
                  value={reviewerId}
                  onChange={(e) => setReviewerId(e.target.value)}
                  className="w-full bg-[#0b0f19] border border-slate-700 rounded px-3 py-2 text-white font-mono focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-mono text-[11px] mb-1">
                  Review Action
                </label>
                <select
                  value={reviewAction}
                  onChange={(e) => setReviewAction(e.target.value as ReviewActionType)}
                  className="w-full bg-[#0b0f19] border border-slate-700 rounded px-3 py-2 text-white font-mono focus:outline-none focus:border-cyan-500"
                >
                  <option value="APPROVE">APPROVE (Clean Pass)</option>
                  <option value="APPROVE_WITH_EXCEPTION">APPROVE_WITH_EXCEPTION (Documented Override)</option>
                  <option value="REQUEST_DOCUMENTS">REQUEST_DOCUMENTS (Hold for Vendor)</option>
                  <option value="ESCALATE">ESCALATE (To AP Manager)</option>
                  <option value="REJECT">REJECT (Block Payment)</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-slate-400 font-mono text-[11px] mb-1">
                Mandatory Review Rationale (Saved to Tamper-Evident Chained Audit Trail) *
              </label>
              <textarea
                required
                rows={2}
                placeholder="State verified trade-name alias, cancelled cheque verification, or reason for action..."
                value={rationale}
                onChange={(e) => setRationale(e.target.value)}
                className="w-full bg-[#0b0f19] border border-slate-700 rounded px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={reviewing}
                className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold px-4 py-2 rounded text-xs transition disabled:opacity-50"
              >
                {reviewing ? 'Sealing Audit Record...' : 'Record Decision & Seal Case'}
              </button>
            </div>
          </form>
        )}
      </div>

      {/* Modal: Correct Extracted Invoice Claims */}
      {showEditModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-[#0f172a] border border-slate-700 rounded-xl max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
                <Edit3 className="h-4 w-4 text-cyan-400" />
                <span>Correct Invoice Claims &amp; Rerun Assessment</span>
              </h3>
              <button
                onClick={() => setShowEditModal(false)}
                className="text-slate-400 hover:text-white text-xs"
              >
                &times; Close
              </button>
            </div>

            <form onSubmit={handleCorrectionSubmit} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-mono text-[11px] mb-1">Supplier Trade Name</label>
                <input
                  type="text"
                  value={corrSupplier}
                  onChange={(e) => setCorrSupplier(e.target.value)}
                  className="w-full bg-[#0b0f19] border border-slate-700 rounded px-3 py-1.5 text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-mono text-[11px] mb-1">Supplier GSTIN</label>
                <input
                  type="text"
                  value={corrGstin}
                  onChange={(e) => setCorrGstin(e.target.value.toUpperCase())}
                  className="w-full bg-[#0b0f19] border border-slate-700 rounded px-3 py-1.5 text-white font-mono focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-mono text-[11px] mb-1">Invoice Number</label>
                  <input
                    type="text"
                    value={corrInvNumber}
                    onChange={(e) => setCorrInvNumber(e.target.value)}
                    className="w-full bg-[#0b0f19] border border-slate-700 rounded px-3 py-1.5 text-white font-mono focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-mono text-[11px] mb-1">Total Amount (&#8377;)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={corrTotalAmount}
                    onChange={(e) => setCorrTotalAmount(e.target.value)}
                    className="w-full bg-[#0b0f19] border border-slate-700 rounded px-3 py-1.5 text-white font-mono focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 font-mono text-[11px] mb-1">Correction Rationale / Notes</label>
                <input
                  type="text"
                  placeholder="e.g. Corrected OCR typo in GSTIN character 14"
                  value={corrNotes}
                  onChange={(e) => setCorrNotes(e.target.value)}
                  className="w-full bg-[#0b0f19] border border-slate-700 rounded px-3 py-1.5 text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowEditModal(false)}
                  className="px-3 py-1.5 bg-slate-800 text-slate-300 rounded hover:bg-slate-700 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={correcting}
                  className="px-4 py-1.5 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold rounded transition disabled:opacity-50"
                >
                  {correcting ? 'Saving & Reassessing...' : 'Apply & Rerun Assessment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
