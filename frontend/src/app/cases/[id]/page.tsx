'use client';

import { use, useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '../../../lib/api';
import { 
  Case, 
  ReviewActionType, 
  InvoiceCorrection, 
  ExplainVerdictResponse, 
  AuditVerifyResponse,
  ManualGstinEvidenceRequest
} from '../../../types/api';
import { 
  AlertCircle,
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
  Info,
  Check,
  FileText,
  ShieldCheck,
  ArrowLeft,
  ChevronDown,
  Layers,
  Search
} from 'lucide-react';

export default function CaseDossierPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const caseId = resolvedParams.id;

  const [caseData, setCaseData] = useState<Case | null>(null);
  const [loading, setLoading] = useState(true);
  const [investigating, setInvestigating] = useState(false);
  const [reviewing, setReviewing] = useState(false);
  const [correcting, setCorrecting] = useState(false);
  const [submittingManualGst, setSubmittingManualGst] = useState(false);
  const [verifyingAudit, setVerifyingAudit] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showManualGstModal, setShowManualGstModal] = useState(false);
  const [viewMode, setViewMode] = useState<'dossier' | 'extraction'>('dossier');
  const [copiedGstin, setCopiedGstin] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Verdict Explanation State
  const [explanation, setExplanation] = useState<ExplainVerdictResponse | null>(null);

  // Audit Chain Verification State
  const [auditVerifyResult, setAuditVerifyResult] = useState<AuditVerifyResponse | null>(null);

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

  // Manual GST Evidence Form State
  const [manualGstLegalName, setManualGstLegalName] = useState('');
  const [manualGstTradeName, setManualGstTradeName] = useState('');
  const [manualGstStatus, setManualGstStatus] = useState('Active');
  const [manualGstRegDate, setManualGstRegDate] = useState('2021-04-01');
  const [manualGstTaxpayerType, setManualGstTaxpayerType] = useState('Regular');
  const [manualGstNotes, setManualGstNotes] = useState('Verified on public GST Search Taxpayer portal');

  const fetchCase = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getCase(caseId);
      setCaseData(data);
      if (data.status === 'PARSED') {
        setViewMode('extraction');
      }
      if (data.invoice) {
        setCorrSupplier(data.invoice.supplier_name || '');
        setCorrLegalName(data.invoice.legal_name || '');
        setCorrGstin(data.invoice.gstin || '');
        setCorrInvNumber(data.invoice.invoice_number || '');
        setCorrTotalAmount(data.invoice.total_amount ? String(data.invoice.total_amount) : '');
        setCorrTaxableAmount(data.invoice.taxable_amount ? String(data.invoice.taxable_amount) : '');
        
        setManualGstLegalName(data.invoice.legal_name || data.invoice.supplier_name || '');
        setManualGstTradeName(data.invoice.supplier_name || '');
      }

      // If assessed, also fetch explanation
      if (data.assessment) {
        api.explainVerdict(caseId).then(setExplanation).catch(() => {});
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
    setSuccessMsg(null);
    try {
      const updated = await api.triggerInvestigation(caseId);
      setCaseData(updated);
      setViewMode('dossier');
      setSuccessMsg('Investigation checks and rule assessment completed.');
      api.explainVerdict(caseId).then(setExplanation).catch(() => {});
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
    setSuccessMsg(null);
    try {
      const updated = await api.submitReview(caseId, {
        reviewer_id: reviewerId,
        action: reviewAction,
        rationale: rationale,
        requested_documents: []
      });
      setCaseData(updated);
      setSuccessMsg(`Review recorded: ${reviewAction}. Case audit record sealed.`);
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
    setSuccessMsg(null);
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
      setSuccessMsg('Invoice claims corrected and assessment updated.');
      api.explainVerdict(caseId).then(setExplanation).catch(() => {});
    } catch (err: any) {
      setError(err.message || 'Failed to apply invoice corrections');
    } finally {
      setCorrecting(false);
    }
  };

  const handleManualGstSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!caseData?.invoice?.gstin) {
      setError('Cannot submit registry details without a valid GSTIN.');
      return;
    }
    setSubmittingManualGst(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const payload: ManualGstinEvidenceRequest = {
        gstin: caseData.invoice.gstin,
        legal_name: manualGstLegalName.trim(),
        trade_name: manualGstTradeName.trim() || undefined,
        status: manualGstStatus,
        registration_date: manualGstRegDate.trim() || undefined,
        taxpayer_type: manualGstTaxpayerType,
        source_url: 'https://services.gst.gov.in/services/searchtp',
        notes: manualGstNotes.trim() || undefined,
        reviewer_id: reviewerId
      };
      const updated = await api.submitManualGstinEvidence(caseId, payload);
      setCaseData(updated);
      setShowManualGstModal(false);
      setSuccessMsg('Attested GST portal evidence recorded. Assessment automatically re-run.');
      api.explainVerdict(caseId).then(setExplanation).catch(() => {});
    } catch (err: any) {
      setError(err.message || 'Failed to submit GST registry evidence');
    } finally {
      setSubmittingManualGst(false);
    }
  };

  const handleVerifyAuditChain = async () => {
    setVerifyingAudit(true);
    try {
      const res = await api.verifyAuditChain(caseId);
      setAuditVerifyResult(res);
    } catch (err: any) {
      setError(err.message || 'Audit chain verification failed');
    } finally {
      setVerifyingAudit(false);
    }
  };

  const handleCopyGstin = () => {
    if (caseData?.invoice?.gstin) {
      navigator.clipboard.writeText(caseData.invoice.gstin);
      setCopiedGstin(true);
      setTimeout(() => setCopiedGstin(false), 2000);
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

  const { invoice, assessment, evidence_items = [], review, source_mode, duplicate_type, review_history = [] } = caseData;
  const isCaseDemo = caseData.is_demo || source_mode === 'DEMO';

  // Helper for provenance badge rendering
  const renderProvenanceChip = (status?: string) => {
    switch (status) {
      case 'EXTRACTED_QR':
        return <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-purple-950/80 text-purple-300 border border-purple-800">QR Code</span>;
      case 'EXTRACTED_LLM':
        return <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-blue-950/80 text-blue-300 border border-blue-800">LLM Extracted</span>;
      case 'EXTRACTED_REGEX':
        return <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-teal-950/80 text-teal-300 border border-teal-800">Text Layer</span>;
      case 'MANUALLY_CORRECTED':
        return <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-amber-950/80 text-amber-300 border border-amber-800">Manual Edit</span>;
      case 'CALCULATED':
        return <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-300 border border-slate-700">Calculated</span>;
      case 'INFERRED':
        return <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-indigo-950/80 text-indigo-300 border border-indigo-800">Inferred</span>;
      case 'CONFLICT':
        return <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-rose-950/80 text-rose-300 border border-rose-800">Conflict</span>;
      default:
        return <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700">Standard</span>;
    }
  };

  return (
    <div className="space-y-6 animate-reveal-up">
      {/* Top Header & Telemetry */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <Link
            href="/queue"
            className="inline-flex items-center space-x-1 text-xs text-slate-400 hover:text-slate-200 transition-colors mb-2"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Back to Cases Queue</span>
          </Link>
          <div className="flex items-center gap-2.5 flex-wrap">
            <span className="text-xs uppercase font-mono px-2 py-0.5 rounded bg-slate-800 text-cyan-400 border border-slate-700">
              {caseData.case_reference}
            </span>
            <span className="text-xs font-mono text-slate-400">Case ID: {caseData.case_id}</span>
            {isCaseDemo && (
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-amber-500/15 text-amber-500 border border-amber-500/30 font-semibold">
                DEMO DATA
              </span>
            )}
            {source_mode === 'SIMULATED' ? (
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-amber-950/60 text-amber-400 border border-amber-800/60">
                Simulated Evidence Mode
              </span>
            ) : source_mode === 'LIVE' ? (
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800/60 flex items-center gap-1">
                <Cpu className="h-3 w-3" /> Live Registry Connected
              </span>
            ) : (
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                Registry Unavailable (Fails Closed)
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
              (&#8377;{invoice.total_amount ? invoice.total_amount.toLocaleString('en-IN') : '0'})
            </span>
          </h1>
        </div>

        {/* View Mode Switcher and Actions */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Extraction Review vs Dossier View Switch */}
          <div className="flex items-center space-x-1 border border-slate-700 rounded-lg p-0.5 bg-slate-900 text-xs">
            <button
              onClick={() => setViewMode('extraction')}
              className={`px-3 py-1.5 rounded-md font-mono text-[11px] transition ${
                viewMode === 'extraction'
                  ? 'bg-cyan-600 text-white font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Extraction Review
            </button>
            <button
              onClick={() => setViewMode('dossier')}
              className={`px-3 py-1.5 rounded-md font-mono text-[11px] transition ${
                viewMode === 'dossier'
                  ? 'bg-cyan-600 text-white font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Evidence Dossier
            </button>
          </div>

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
              className="flex items-center gap-2 text-xs font-semibold bg-cyan-500 hover:bg-cyan-400 text-slate-950 px-4 py-1.5 rounded-md transition disabled:opacity-50 shadow-md"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${investigating ? 'animate-spin' : ''}`} />
              <span>{investigating ? 'Evaluating Pipeline...' : 'Confirm & Run Checks'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Feedback Alerts */}
      {error && (
        <div className="p-3 bg-rose-950/60 border border-rose-800 rounded text-rose-300 text-xs flex items-center space-x-2">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {successMsg && (
        <div className="p-3 bg-emerald-950/60 border border-emerald-800 rounded text-emerald-300 text-xs flex items-center space-x-2">
          <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
          <span>{successMsg}</span>
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

      {/* Extraction Conflict Alert Banner */}
      {invoice.extraction_conflicts && invoice.extraction_conflicts.length > 0 && (
        <div className="p-3 bg-rose-950/40 border border-rose-800 rounded-lg text-rose-200 text-xs flex items-center gap-2">
          <ShieldAlert className="h-4 w-4 text-rose-400 flex-shrink-0" />
          <span>
            <strong>Extraction Conflict Detected:</strong> Discrepancies exist between QR code payload, text layers, or LLM output. Verify document before payment sign-off.
          </span>
        </div>
      )}

      {/* =========================================================================
          VIEW MODE 1: SIDE-BY-SIDE EXTRACTION REVIEW (BEFORE OR AFTER CHECKS)
      ========================================================================= */}
      {viewMode === 'extraction' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between bg-slate-900/80 p-3 rounded-lg border border-slate-800 text-xs">
            <div className="flex items-center space-x-2">
              <span className="font-semibold text-white">Side-by-Side Extraction Review:</span>
              <span className="text-slate-400">Compare original file against extracted structured claims and provenance.</span>
            </div>
            {caseData.status === 'PARSED' && (
              <button
                onClick={handleRunInvestigation}
                disabled={investigating}
                className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold px-4 py-1.5 rounded text-xs transition disabled:opacity-50"
              >
                {investigating ? 'Running Verification...' : 'Confirm & Run Checks'}
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left: Original File Preview */}
            <div className="bg-[#0f172a]/90 border border-slate-800 rounded-xl p-4 flex flex-col h-[650px]">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <span className="text-xs font-mono font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                  <FileText className="h-4 w-4 text-cyan-400" />
                  <span>Original Uploaded Invoice Document</span>
                </span>
                <a
                  href={api.getCaseFileUrl(caseId)}
                  target="_blank"
                  rel="noreferrer"
                  className="text-[11px] font-mono text-cyan-400 hover:underline flex items-center gap-1"
                >
                  <span>Open Fullscreen</span>
                  <ExternalLink className="h-3 w-3" />
                </a>
              </div>
              <div className="flex-1 mt-3 bg-slate-950 rounded-lg overflow-hidden border border-slate-800/80 flex items-center justify-center">
                {caseData.file_sha256 ? (
                  <iframe
                    src={api.getCaseFileUrl(caseId)}
                    title="Invoice PDF / Image Viewer"
                    className="w-full h-full border-0"
                  />
                ) : (
                  <div className="text-center p-6 text-slate-500 font-mono text-xs space-y-2">
                    <FileText className="h-8 w-8 mx-auto text-slate-600" />
                    <div>Manual Intake Case</div>
                    <div className="text-[10px]">No physical PDF or image file was uploaded with this dossier.</div>
                  </div>
                )}
              </div>
            </div>

            {/* Right: Extracted Fields with Provenance & Confidence */}
            <div className="bg-[#0f172a]/90 border border-slate-800 rounded-xl p-5 space-y-4 overflow-y-auto max-h-[650px]">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <div>
                  <h3 className="text-xs font-mono font-semibold text-slate-200 uppercase tracking-wider">
                    Extracted Claims &amp; Layer Provenance
                  </h3>
                  <p className="text-[11px] text-slate-400">Precedence hierarchy: QR &gt; LLM &gt; Regex</p>
                </div>
                <button
                  onClick={() => setShowEditModal(true)}
                  className="text-xs font-mono text-cyan-400 hover:underline flex items-center gap-1"
                >
                  <Edit3 className="h-3.5 w-3.5" /> Edit
                </button>
              </div>

              <div className="space-y-3 text-xs">
                {/* Supplier Name */}
                <div className="p-2.5 rounded bg-[#0b0f19] border border-slate-800 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-slate-400 text-[11px]">Supplier Trade Name</span>
                    {renderProvenanceChip(invoice.extraction_metadata?.['supplier_name']?.status)}
                  </div>
                  <div className="font-semibold text-white">{invoice.supplier_name}</div>
                </div>

                {/* Legal Name */}
                <div className="p-2.5 rounded bg-[#0b0f19] border border-slate-800 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-slate-400 text-[11px]">Legal Entity Name</span>
                    {renderProvenanceChip(invoice.extraction_metadata?.['legal_name']?.status)}
                  </div>
                  <div className="font-mono text-slate-300">{invoice.legal_name || 'Not separately declared'}</div>
                </div>

                {/* GSTIN */}
                <div className="p-2.5 rounded bg-[#0b0f19] border border-slate-800 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-slate-400 text-[11px]">Supplier GSTIN</span>
                    <div className="flex items-center gap-1.5">
                      {renderProvenanceChip(invoice.extraction_metadata?.['gstin']?.status)}
                      {invoice.gstin_format_valid && (
                        <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                          Mod-36 OK
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="font-mono text-cyan-300 font-semibold">{invoice.gstin || 'Missing'}</div>
                </div>

                {/* Buyer GSTIN */}
                <div className="p-2.5 rounded bg-[#0b0f19] border border-slate-800 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-slate-400 text-[11px]">Buyer GSTIN</span>
                    {renderProvenanceChip(invoice.extraction_metadata?.['buyer_gstin']?.status)}
                  </div>
                  <div className="font-mono text-slate-300">{invoice.buyer_gstin || 'Not extracted / Intra-company'}</div>
                </div>

                {/* Invoice Number & Date */}
                <div className="grid grid-cols-2 gap-2">
                  <div className="p-2.5 rounded bg-[#0b0f19] border border-slate-800 space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-slate-400 text-[11px]">Invoice #</span>
                      {renderProvenanceChip(invoice.extraction_metadata?.['invoice_number']?.status)}
                    </div>
                    <div className="font-mono text-white">{invoice.invoice_number || 'N/A'}</div>
                  </div>
                  <div className="p-2.5 rounded bg-[#0b0f19] border border-slate-800 space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-slate-400 text-[11px]">Invoice Date</span>
                      {renderProvenanceChip(invoice.extraction_metadata?.['invoice_date']?.status)}
                    </div>
                    <div className="font-mono text-white">{invoice.invoice_date || 'N/A'}</div>
                  </div>
                </div>

                {/* Amounts Breakdown */}
                <div className="p-2.5 rounded bg-[#0b0f19] border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-slate-400 text-[11px]">Financial Amounts</span>
                    {renderProvenanceChip(invoice.extraction_metadata?.['total_amount']?.status)}
                  </div>
                  <div className="flex items-baseline justify-between font-mono">
                    <span className="text-slate-400">Taxable Base:</span>
                    <span className="text-white">&#8377;{invoice.taxable_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                  </div>
                  <div className="flex items-baseline justify-between font-mono text-[11px] text-slate-400">
                    <span>CGST: &#8377;{invoice.cgst.toLocaleString('en-IN')} | SGST: &#8377;{invoice.sgst.toLocaleString('en-IN')} | IGST: &#8377;{invoice.igst.toLocaleString('en-IN')}</span>
                  </div>
                  <div className="border-t border-slate-800 pt-1.5 flex items-baseline justify-between font-mono font-bold">
                    <span className="text-cyan-400">Gross Total:</span>
                    <span className="text-white text-sm">&#8377;{invoice.total_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                  </div>
                </div>

                {/* Bank Account & IFSC */}
                <div className="p-2.5 rounded bg-[#0b0f19] border border-slate-800 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-slate-400 text-[11px]">Bank Account &amp; IFSC</span>
                    {renderProvenanceChip(invoice.extraction_metadata?.['bank_account_masked']?.status)}
                  </div>
                  <div className="font-mono text-slate-300">
                    Account: {invoice.bank_account_masked || 'Not extracted'} | IFSC: {invoice.ifsc_code || 'Not extracted'}
                  </div>
                </div>

                {/* e-Invoice QR Status */}
                {invoice.qr_signature_status && (
                  <div className="p-2.5 rounded bg-[#0b0f19] border border-slate-800 space-y-1">
                    <span className="font-mono text-slate-400 text-[11px] block">e-Invoice B2B QR Code</span>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-cyan-300 font-semibold">{invoice.qr_signature_status}</span>
                      {invoice.irn && <span className="font-mono text-[10px] text-slate-400 truncate max-w-xs">IRN: {invoice.irn}</span>}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          VIEW MODE 2: FULL EVIDENCE DOSSIER & VERDICT
      ========================================================================= */}
      {viewMode === 'dossier' && (
        <div className="space-y-6">
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
                    <div className="flex items-center gap-2 flex-wrap">
                      <h2 className="text-sm font-bold tracking-wide uppercase font-mono text-white">
                        Recommendation: {assessment.recommendation}
                      </h2>
                      <span className="text-xs font-mono text-slate-400">
                        &bull; Policy Index (Heuristic): <strong className="text-white">{assessment.risk_score}</strong>/100
                      </span>
                      {isCaseDemo && (
                        <span className="text-[10px] font-mono px-2 py-0.2 rounded bg-amber-500/20 text-amber-400 border border-amber-500/30">
                          DEMO SCENARIO
                        </span>
                      )}
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
                    {assessment.reason_codes && assessment.reason_codes.length > 0 && (
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

                <div className="text-right font-mono text-[11px] text-slate-400 shrink-0">
                  <div>Rule Engine v{assessment.ruleset_version}</div>
                  <div>Evidence Completeness: <strong className="text-slate-300">{assessment.evidence_completeness}</strong></div>
                </div>
              </div>

              {/* Explain Verdict: Why this verdict & What would change it */}
              {explanation && (
                <div className="mt-4 pt-4 border-t border-slate-800/80 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                  <div className="p-3 bg-slate-900/70 rounded-lg border border-slate-800 space-y-1.5">
                    <span className="text-cyan-400 font-semibold uppercase text-[10.5px] block">
                      Why This Verdict
                    </span>
                    <ul className="space-y-1 text-slate-300 text-[11px] list-disc list-inside">
                      {explanation.why_this_verdict.map((reason, idx) => (
                        <li key={idx} className="leading-relaxed">{reason}</li>
                      ))}
                    </ul>
                  </div>

                  <div className="p-3 bg-slate-900/70 rounded-lg border border-slate-800 space-y-1.5">
                    <span className="text-amber-400 font-semibold uppercase text-[10.5px] block">
                      What Would Change It
                    </span>
                    <ul className="space-y-1 text-slate-300 text-[11px] list-disc list-inside">
                      {explanation.what_would_change_it.map((step, idx) => (
                        <li key={idx} className="leading-relaxed">{step}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {/* Decision Support & Limitations Banner */}
              <div className="mt-3 px-3 py-1.5 rounded bg-slate-900/60 border border-slate-800 text-[10px] text-slate-400 font-mono">
                <strong>DECISION-SUPPORT NOTICE:</strong> Policy index scores are deterministic heuristics based on explicit business rules; they are not calibrated statistical fraud probabilities.
              </div>

              {/* Direct Rupee Financial Liability (CGST Sec 16(2)(c)) */}
              {assessment.itc_exposure && (
                <div className="mt-4 pt-4 border-t border-slate-800/80 bg-slate-950/60 rounded-lg p-3.5 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
                  <div>
                    <span className="text-[10px] font-mono uppercase text-slate-400 block tracking-wider">
                      Illustrative Estimation &bull; CGST Sec 16(2)(c) &amp; Sec 16(4)
                    </span>
                    <div className="text-white font-medium mt-0.5">
                      Claimed GST: <strong className="text-cyan-300 font-mono">&#8377;{assessment.itc_exposure.tax_amount_claimed.toLocaleString('en-IN')}</strong> &bull; Potential Liability: <strong className="text-rose-400 font-mono">&#8377;{assessment.itc_exposure.total_financial_liability_inr.toLocaleString('en-IN')}</strong> (tax clawback + interest/penalty projection)
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1 italic">
                      &ldquo;{assessment.itc_exposure.cfo_advisory}&rdquo;
                    </p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <span className={`px-2 py-0.5 rounded font-mono text-[10px] font-bold uppercase ${
                      assessment.itc_exposure.risk_tier === 'CRITICAL' ? 'bg-rose-950 text-rose-300 border border-rose-800' :
                      assessment.itc_exposure.risk_tier === 'HIGH' ? 'bg-amber-950 text-amber-300 border border-amber-800' :
                      'bg-emerald-950 text-emerald-300 border border-emerald-800'
                    }`}>
                      ITC TIER: {assessment.itc_exposure.risk_tier}
                    </span>
                  </div>
                </div>
              )}
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
                    {invoice.gstin && (
                      <button
                        onClick={handleCopyGstin}
                        className="text-[10px] font-mono text-slate-400 hover:text-white flex items-center gap-0.5"
                        title="Copy GSTIN"
                      >
                        {copiedGstin ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                      </button>
                    )}
                    {invoice.gstin_format_valid && (
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 font-mono">
                        CHECKSUM OK
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

              {/* Portal Lookup Button (C2.1 manual evidence prompt) */}
              <div className="pt-3 border-t border-slate-800 space-y-2">
                <button
                  type="button"
                  onClick={() => setShowManualGstModal(true)}
                  className="w-full py-2 px-3 rounded-lg text-xs font-semibold bg-teal-900/40 hover:bg-teal-900/60 border border-teal-700 text-teal-300 transition flex items-center justify-center gap-1.5"
                >
                  <Search className="h-3.5 w-3.5" />
                  <span>Add GST Registry Details</span>
                </button>
                <div className="flex items-center justify-between text-[11px] text-slate-400">
                  <button onClick={handleCopyGstin} className="hover:text-white flex items-center gap-1">
                    <Copy className="h-3 w-3" /> Copy GSTIN
                  </button>
                  <a
                    href="https://services.gst.gov.in/services/searchtp"
                    target="_blank"
                    rel="noreferrer"
                    className="hover:text-cyan-300 flex items-center gap-1 text-cyan-400"
                  >
                    <span>GST Search Taxpayer</span>
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
              </div>
            </div>

            {/* Center & Right: Reconciled Checks & Provenance */}
            <div className="lg:col-span-2 space-y-4">
              <div className="bg-[#0f172a]/70 border border-slate-800 rounded-lg p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-300 font-mono">
                    2. Deterministic Field Reconciliations
                  </h2>
                  <span className="text-[11px] text-slate-400 font-mono">
                    Grey = Not Checked / Unavailable (Never Red)
                  </span>
                </div>

                {assessment && assessment.field_checks && assessment.field_checks.length > 0 ? (
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
                              {chk.status === 'UNAVAILABLE' ? 'NOT CHECKED / UNAVAILABLE' : chk.status}
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
                    No reconciliation checks run yet. Click &apos;Confirm &amp; Run Checks&apos; above.
                  </div>
                )}
              </div>

              {/* Discovered Evidence Dossier View */}
              {evidence_items.length > 0 && (
                <div className="bg-[#0f172a]/70 border border-slate-800 rounded-lg p-5 space-y-3">
                  <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-300 font-mono border-b border-slate-800 pb-2">
                    3. Evidence Dossier &amp; Registry Citations
                  </h2>
                  <div className="space-y-3">
                    {evidence_items.map(ev => (
                      <div key={ev.evidence_id} className="p-3 bg-[#0b0f19] border border-slate-800 rounded text-xs space-y-1.5">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-cyan-300">{ev.source_name}</span>
                            <span className="text-[9px] font-mono uppercase px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700">
                              {ev.source_mode || 'SIMULATED'}
                            </span>
                          </div>
                          <span className="text-[10px] font-mono text-slate-500">{ev.retrieved_at}</span>
                        </div>
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

          {/* Reviewer Action / Sign-Off Box & Cryptographic Audit Verification */}
          <div className="bg-[#0f172a]/90 border border-slate-700 rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3 flex-wrap gap-2">
              <div className="flex items-center gap-2">
                <Lock className="h-4 w-4 text-cyan-400" />
                <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-200 font-mono">
                  4. Reviewer Decision &amp; Audit Seal
                </h2>
              </div>
              
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={handleVerifyAuditChain}
                  disabled={verifyingAudit}
                  className="px-2.5 py-1 text-[11px] font-mono rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 transition"
                >
                  {verifyingAudit ? 'Verifying...' : 'Verify Audit Chain'}
                </button>

                {caseData.audit_hash_sha256 && (
                  <span className="text-[11px] font-mono text-slate-400">
                    SHA-256: <code className="text-cyan-300">{caseData.audit_hash_sha256.substring(0, 16)}...</code>
                  </span>
                )}
              </div>
            </div>

            {/* Audit Chain Verification Result Display */}
            {auditVerifyResult && (
              <div className={`p-3 rounded-lg text-xs font-mono border ${
                auditVerifyResult.chain_valid
                  ? 'bg-emerald-950/40 border-emerald-800 text-emerald-300'
                  : 'bg-rose-950/40 border-rose-800 text-rose-300'
              }`}>
                <div className="flex items-center justify-between">
                  <span>{auditVerifyResult.chain_valid ? '✓ SHA-256 Hash Chain Verified Intact' : '⚠ Cryptographic Audit Chain Mismatch'}</span>
                  <span>Events Verified: {auditVerifyResult.total_events}</span>
                </div>
                <div className="text-[11px] text-slate-400 mt-1">{auditVerifyResult.detail}</div>
              </div>
            )}

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
                  <span className="text-white font-medium">{review.reviewer_id} ({review.reviewer_role || 'reviewer'})</span>
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
                      Reviewer Identity (Derived from Bearer Token)
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
        </div>
      )}

      {/* =========================================================================
          MODAL 1: ADD GST REGISTRY DETAILS (C2.1 FORM)
      ========================================================================= */}
      {showManualGstModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="bg-[#0f172a] border border-slate-700 rounded-xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
                <Search className="h-4 w-4 text-teal-400" />
                <span>Enter Attested GST Registry Evidence</span>
              </h3>
              <button
                onClick={() => setShowManualGstModal(false)}
                className="text-slate-400 hover:text-white text-xs font-mono"
              >
                &times; Close
              </button>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              Copy the invoice GSTIN, search on the official GST portal, and record the returned taxpayer registration facts. Submitting will update the case evidence and automatically re-run assessment checks.
            </p>

            <div className="p-2.5 rounded bg-slate-900 border border-slate-800 flex items-center justify-between text-xs font-mono">
              <span className="text-slate-400">GSTIN: <strong className="text-cyan-300">{invoice.gstin || 'None'}</strong></span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleCopyGstin}
                  className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px]"
                >
                  {copiedGstin ? 'Copied!' : 'Copy GSTIN'}
                </button>
                <a
                  href="https://services.gst.gov.in/services/searchtp"
                  target="_blank"
                  rel="noreferrer"
                  className="px-2 py-1 rounded bg-teal-900/60 hover:bg-teal-800 text-teal-300 text-[11px] flex items-center gap-1"
                >
                  <span>Open GST Portal</span>
                  <ExternalLink className="h-3 w-3" />
                </a>
              </div>
            </div>

            <form onSubmit={handleManualGstSubmit} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-mono text-[11px] mb-1">
                  Registered Legal Name *
                </label>
                <input
                  type="text"
                  required
                  value={manualGstLegalName}
                  onChange={(e) => setManualGstLegalName(e.target.value)}
                  placeholder="e.g. Apex Global Logistics Private Limited"
                  className="w-full bg-[#0b0f19] border border-slate-700 rounded px-3 py-1.5 text-white focus:outline-none focus:border-teal-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-mono text-[11px] mb-1">
                  Registered Trade Name
                </label>
                <input
                  type="text"
                  value={manualGstTradeName}
                  onChange={(e) => setManualGstTradeName(e.target.value)}
                  placeholder="e.g. Apex Courier"
                  className="w-full bg-[#0b0f19] border border-slate-700 rounded px-3 py-1.5 text-white focus:outline-none focus:border-teal-500 font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-mono text-[11px] mb-1">
                    GSTIN Status *
                  </label>
                  <select
                    value={manualGstStatus}
                    onChange={(e) => setManualGstStatus(e.target.value)}
                    className="w-full bg-[#0b0f19] border border-slate-700 rounded px-3 py-1.5 text-white font-mono focus:outline-none focus:border-teal-500"
                  >
                    <option value="Active">Active</option>
                    <option value="Cancelled">Cancelled</option>
                    <option value="Suspended">Suspended</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 font-mono text-[11px] mb-1">
                    Registration Date
                  </label>
                  <input
                    type="date"
                    value={manualGstRegDate}
                    onChange={(e) => setManualGstRegDate(e.target.value)}
                    className="w-full bg-[#0b0f19] border border-slate-700 rounded px-3 py-1.5 text-white font-mono focus:outline-none focus:border-teal-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 font-mono text-[11px] mb-1">
                  Attestation / Audit Notes
                </label>
                <input
                  type="text"
                  value={manualGstNotes}
                  onChange={(e) => setManualGstNotes(e.target.value)}
                  className="w-full bg-[#0b0f19] border border-slate-700 rounded px-3 py-1.5 text-white focus:outline-none focus:border-teal-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowManualGstModal(false)}
                  className="px-3 py-1.5 bg-slate-800 text-slate-300 rounded hover:bg-slate-700 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingManualGst || !manualGstLegalName.trim()}
                  className="px-4 py-1.5 bg-teal-600 hover:bg-teal-500 text-white font-semibold rounded transition disabled:opacity-50"
                >
                  {submittingManualGst ? 'Saving & Reassessing...' : 'Record Evidence & Re-assess'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* =========================================================================
          MODAL 2: CORRECT EXTRACTED INVOICE CLAIMS
      ========================================================================= */}
      {showEditModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="bg-[#0f172a] border border-slate-700 rounded-xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
                <Edit3 className="h-4 w-4 text-cyan-400" />
                <span>Correct Invoice Claims &amp; Rerun Assessment</span>
              </h3>
              <button
                onClick={() => setShowEditModal(false)}
                className="text-slate-400 hover:text-white text-xs font-mono"
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
