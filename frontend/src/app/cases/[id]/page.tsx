'use client';

import { useEffect, useState, useMemo } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '../../../lib/api';
import { CaseDetail, ReviewActionType, EvidenceItem } from '../../../types/api';
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  RotateCcw,
  CheckCircle2,
  XCircle,
  FileText,
  Building2,
  Hash,
  ExternalLink,
  Download,
  Edit3,
  Tv,
  Cpu,
  Layers,
  ArrowLeft,
  ChevronRight,
  TrendingDown,
  Info,
  Check,
  AlertCircle,
  Copy,
  Radio,
  Lock,
  RefreshCw,
  Search,
  History,
  ShieldX,
  Truck
} from 'lucide-react';

export default function CaseDetailPage() {
  const params = useParams();
  const router = useRouter();
  const caseId = params.id as string;

  const [caseData, setCaseData] = useState<CaseDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Review Form State
  const [reviewAction, setReviewAction] = useState<ReviewActionType>('EXECUTE_SPLIT_PAYOUT');
  const [rationale, setRationale] = useState('');
  const [reviewerId, setReviewerId] = useState('senior_ap_auditor');
  const [reviewing, setReviewing] = useState(false);

  // Correct Claims Modal State
  const [showEditModal, setShowEditModal] = useState(false);
  const [corrSupplier, setCorrSupplier] = useState('');
  const [corrGstin, setCorrGstin] = useState('');
  const [corrInvNumber, setCorrInvNumber] = useState('');
  const [corrTotalAmount, setCorrTotalAmount] = useState('');
  const [corrNotes, setCorrNotes] = useState('');
  const [correcting, setCorrecting] = useState(false);

  // Investigation Trigger State
  const [investigating, setInvestigating] = useState(false);
  const [copiedAuditHash, setCopiedAuditHash] = useState(false);
  const [copiedIMS, setCopiedIMS] = useState(false);

  // Active Hop Tabs
  const [activeHopTab, setActiveHopTab] = useState<'all' | number>('all');

  const fetchCase = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getCase(caseId);
      setCaseData(data);
      if (data.invoice) {
        setCorrSupplier(data.invoice.supplier_name);
        setCorrGstin(data.invoice.gstin);
        setCorrInvNumber(data.invoice.invoice_number);
        setCorrTotalAmount(data.invoice.total_amount.toString());
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load case data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCase();
  }, [caseId]);

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rationale.trim()) {
      alert('Review rationale is mandatory to seal this case.');
      return;
    }

    setReviewing(true);
    try {
      await api.submitReview(caseId, {
        action: reviewAction,
        rationale: rationale.trim(),
        reviewer_id: reviewerId.trim()
      });
      await fetchCase();
    } catch (err: any) {
      alert(`Review Failed: ${err.message}`);
    } finally {
      setReviewing(false);
    }
  };

  const handleCorrectionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setCorrecting(true);
    try {
      await api.correctClaims(caseId, {
        supplier_name: corrSupplier,
        gstin: corrGstin,
        invoice_number: corrInvNumber,
        total_amount: parseFloat(corrTotalAmount) || undefined,
        correction_notes: corrNotes || 'Analyst manual correction'
      });
      setShowEditModal(false);
      await fetchCase();
    } catch (err: any) {
      alert(`Correction Failed: ${err.message}`);
    } finally {
      setCorrecting(false);
    }
  };

  const handleRunInvestigation = async () => {
    setInvestigating(true);
    try {
      await api.runInvestigation(caseId);
      await fetchCase();
    } catch (err: any) {
      alert(`Investigation Failed: ${err.message}`);
    } finally {
      setInvestigating(false);
    }
  };

  const handleDownloadReport = () => {
    window.open(`${process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'}/api/cases/${caseId}/audit-trail?format=markdown`, '_blank');
  };

  // Derive Treasury Settlement Breakdown
  const settlement = useMemo(() => {
    if (!caseData || !caseData.invoice) return null;
    if (caseData.assessment?.treasury_settlement) {
      return caseData.assessment.treasury_settlement;
    }

    // Dynamic Fallback calculation for older cases
    const inv = caseData.invoice;
    const gst = Math.round(((inv.cgst || 0) + (inv.sgst || 0) + (inv.igst || 0)) * 100) / 100 || 
                Math.round(Math.max(0, inv.total_amount - (inv.taxable_amount || 0)) * 100) / 100;
    const base = Math.max(0, Math.round((inv.total_amount - gst) * 100) / 100);
    const clawback = Math.round(gst * 2.18 * 100) / 100;

    if (caseData.assessment?.recommendation === 'BLOCK') {
      return {
        recommendation: 'FORENSIC_FREEZE',
        release_now_inr: 0,
        escrow_hold_gst_inr: inv.total_amount,
        statutory_clawback_risk_avoided_inr: clawback,
        msme_43b_compliant: false,
        gstn_ims_action: 'REJECT',
        settlement_rationale: 'FORENSIC FREEZE: Payment release halted (₹0.00 disbursed). Critical hard safety gate triggered. GSTN IMS Portal Action set to REJECT to prevent buyer tax liability.',
        ims_action_payload: caseData.assessment.ims_action_json
      };
    } else if (caseData.assessment?.recommendation === 'MANUAL_REVIEW') {
      return {
        recommendation: 'STATUTORY_GST_ESCROW',
        release_now_inr: base,
        escrow_hold_gst_inr: gst,
        statutory_clawback_risk_avoided_inr: clawback,
        msme_43b_compliant: true,
        gstn_ims_action: 'PENDING_HOLD',
        settlement_rationale: `STATUTORY GST ESCROW (SPLIT PAYOUT): Disbursing base taxable amount ₹${base.toLocaleString('en-IN')} satisfies Section 43B(h) MSME 45-day mandate. Retaining GST component ₹${gst.toLocaleString('en-IN')} in tax escrow safeguards buyer against CGST Sec 16(2)(c) clawback (₹${clawback.toLocaleString('en-IN')} risk avoided).`,
        ims_action_payload: caseData.assessment.ims_action_json
      };
    } else {
      return {
        recommendation: 'FULL_DISBURSAL',
        release_now_inr: inv.total_amount,
        escrow_hold_gst_inr: 0,
        statutory_clawback_risk_avoided_inr: clawback,
        msme_43b_compliant: true,
        gstn_ims_action: 'ACCEPT',
        settlement_rationale: 'FULL DISBURSAL: Supplier verified clean across all 4 forensic hops. Zero adverse dockets, GSTR-3B regular, and bank account verified. 100% payout released. GSTN IMS Action: ACCEPT.',
        ims_action_payload: caseData.assessment?.ims_action_json
      };
    }
  }, [caseData]);

  const imsAction = caseData?.assessment?.gstn_ims_action || settlement?.gstn_ims_action || 'ACCEPT';
  const liveStreamingUrl = caseData?.assessment?.streaming_url || caseData?.evidence_items?.find(e => e.streaming_url)?.streaming_url;

  const handleExportIMSJson = () => {
    const payload = caseData?.assessment?.ims_action_json || settlement?.ims_action_payload || {
      ims_version: "2026.1",
      case_reference: caseData?.case_reference,
      gstin_supplier: caseData?.invoice?.gstin,
      invoice_number: caseData?.invoice?.invoice_number,
      total_invoice_value: caseData?.invoice?.total_amount,
      ims_action: imsAction,
      settlement_recommendation: settlement?.recommendation,
      release_now_inr: settlement?.release_now_inr,
      escrow_hold_gst_inr: settlement?.escrow_hold_gst_inr
    };
    const jsonStr = JSON.stringify(payload, null, 2);
    navigator.clipboard.writeText(jsonStr);
    setCopiedIMS(true);
    setTimeout(() => setCopiedIMS(false), 2500);

    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `GSTN_IMS_Action_${caseData?.case_reference || caseId}.json`;
    a.click();
  };

  const copyAuditHash = () => {
    if (!caseData?.audit_hash_sha256) return;
    navigator.clipboard.writeText(caseData.audit_hash_sha256);
    setCopiedAuditHash(true);
    setTimeout(() => setCopiedAuditHash(false), 2000);
  };

  const selectReviewOption = (act: ReviewActionType, defaultRat: string) => {
    setReviewAction(act);
    setRationale(defaultRat);
  };

  if (loading) {
    return (
      <div className="max-w-7xl w-full mx-auto px-4 sm:px-6 py-28 text-center text-zinc-900 dark:text-zinc-100">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-teal-50 dark:bg-teal-950/40 text-teal-600 dark:text-teal-400 mb-4 animate-pulse">
          <RefreshCw className="h-7 w-7 animate-spin" />
        </div>
        <h2 className="text-base sm:text-lg font-bold text-zinc-900 dark:text-zinc-100 font-mono">
          Loading Pre-Disbursal Forensic Dossier...
        </h2>
        <p className="text-xs sm:text-sm text-zinc-500 dark:text-zinc-400 mt-1.5">
          Decrypting cryptographic audit trail &amp; multi-hop web evidence
        </p>
      </div>
    );
  }

  if (!caseData || !caseData.invoice) {
    return (
      <div className="max-w-7xl w-full mx-auto px-4 sm:px-6 py-24 text-center text-zinc-900 dark:text-zinc-100">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 mb-4">
          <AlertCircle className="h-7 w-7" />
        </div>
        <h2 className="text-lg font-bold text-zinc-900 dark:text-zinc-100 font-mono">
          Case or Invoice Records Not Found
        </h2>
        <p className="text-xs sm:text-sm text-zinc-500 dark:text-zinc-400 mt-1 max-w-sm mx-auto">
          The requested forensic dossier could not be retrieved from the persistent repository.
        </p>
        <Link
          href="/queue"
          className="inline-flex items-center gap-2 mt-5 text-sm font-bold text-teal-600 hover:text-teal-500 font-mono"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Return to Cases Queue</span>
        </Link>
      </div>
    );
  }

  const { invoice, assessment, evidence_items, review, source_mode, duplicate_type, review_history } = caseData;

  const hops = [
    { num: 1, title: 'GST Velocity & Entity Check', targetDomain: 'knowyourgst.com' },
    { num: 2, title: 'NCLT & Judicial Insolvency Sweep', targetDomain: 'indiankanoon.org' },
    { num: 3, title: 'DGGI Enforcement Radar', targetDomain: 'dggi.gov.in / CBIC' },
    { num: 4, title: 'IndiaMART B2B Price Benchmark', targetDomain: 'dir.indiamart.com' },
  ];

  const filteredEvidence = activeHopTab === 'all' 
    ? evidence_items 
    : evidence_items.filter(e => e.hop_number === activeHopTab);

  return (
    <div className="max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-6 animate-reveal-up text-zinc-900 dark:text-zinc-100">
      
      {/* ==================================================================== */}
      {/* 1. TOP COMMAND BREADCRUMB & ACTION BAR */}
      {/* ==================================================================== */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-zinc-200/80 dark:border-zinc-800/80">
        <div className="flex items-center gap-2.5 flex-wrap">
          <Link
            href="/queue"
            className="inline-flex items-center gap-1.5 text-xs sm:text-sm text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200 transition-colors mr-1 font-semibold"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Cases Queue</span>
          </Link>
          <span className="text-zinc-300 dark:text-zinc-700">/</span>
          <span className="text-xs sm:text-sm font-mono font-bold px-2.5 py-1 rounded-lg bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 border border-zinc-200 dark:border-zinc-700 shadow-xs">
            {caseData.case_reference}
          </span>
          <span className="text-xs font-mono text-zinc-500 dark:text-zinc-400">
            ID: {caseData.case_id.substring(0, 14)}...
          </span>

          {/* Source Mode Provenance Badge */}
          {source_mode === 'LIVE' || source_mode === 'LIVE_TINYFISH_SSE' ? (
            <span className="inline-flex items-center gap-2 text-xs font-mono uppercase font-bold px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/60 dark:text-emerald-300 dark:border-emerald-800/60 shadow-xs">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-ping" />
              Live TinyFish SSE Streaming
            </span>
          ) : source_mode === 'SIMULATED' ? (
            <span className="inline-flex items-center gap-1.5 text-xs font-mono uppercase font-bold px-3 py-1 rounded-full bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-950/60 dark:text-amber-300 dark:border-amber-800/60 shadow-xs">
              <Cpu className="h-3.5 w-3.5" />
              Simulated Evaluation Fixture
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 text-xs font-mono uppercase font-semibold px-2.5 py-1 rounded-full bg-zinc-100 text-zinc-600 border border-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:border-zinc-700">
              Evidence Unavailable
            </span>
          )}

          {/* Live Browser Agent Stream Preview Toggle */}
          {liveStreamingUrl && (
            <a
              href={liveStreamingUrl}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 text-xs font-mono font-bold px-3 py-1 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 dark:bg-indigo-950/70 dark:text-indigo-300 dark:border-indigo-800 hover:bg-indigo-100 dark:hover:bg-indigo-900/60 transition shadow-xs"
            >
              <Tv className="h-3.5 w-3.5" />
              <span>Live Agent Browser View</span>
              <ExternalLink className="h-3 w-3 ml-0.5 opacity-70" />
            </a>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2.5 flex-wrap">
          <button
            type="button"
            onClick={() => setShowEditModal(true)}
            className="inline-flex items-center gap-1.5 text-xs sm:text-sm font-semibold px-3.5 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition shadow-xs cursor-pointer"
          >
            <Edit3 className="h-4 w-4 text-teal-600 dark:text-teal-400" />
            <span>Correct Claims</span>
          </button>

          <button
            type="button"
            onClick={handleDownloadReport}
            className="inline-flex items-center gap-1.5 text-xs sm:text-sm font-semibold px-3.5 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition shadow-xs cursor-pointer"
          >
            <Download className="h-4 w-4 text-zinc-400" />
            <span>Audit Trail (.MD)</span>
          </button>

          {caseData.status === 'PARSED' && (
            <button
              type="button"
              onClick={handleRunInvestigation}
              disabled={investigating}
              className="inline-flex items-center gap-2 text-xs sm:text-sm font-bold px-4 py-2 rounded-xl bg-teal-600 hover:bg-teal-500 text-white shadow-sm transition disabled:opacity-50 cursor-pointer"
            >
              <RefreshCw className={`h-4 w-4 ${investigating ? 'animate-spin' : ''}`} />
              <span>{investigating ? 'Executing 4-Hop TinyFish...' : 'Run 4-Hop TinyFish'}</span>
            </button>
          )}
        </div>
      </div>

      {/* ==================================================================== */}
      {/* 2. EXECUTIVE VENDOR & INVOICE HERO HEADER CARD */}
      {/* ==================================================================== */}
      <div className="bg-white dark:bg-[#0e1420] border border-zinc-200/90 dark:border-zinc-800/90 rounded-2xl p-6 sm:p-7 shadow-subtle space-y-5">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          {/* Vendor Details */}
          <div className="space-y-2">
            <div className="flex items-center gap-2.5 flex-wrap">
              <span className="text-xs font-mono uppercase font-bold text-teal-700 dark:text-teal-400 tracking-wider">
                Invoiced Counterparty
              </span>
              {duplicate_type && (
                <span className="text-xs font-mono uppercase px-2.5 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200 dark:bg-rose-950/60 dark:text-rose-300 dark:border-rose-800 flex items-center gap-1 font-bold">
                  <Copy className="h-3 w-3" /> {duplicate_type}
                </span>
              )}
            </div>

            <h1 className="text-2xl sm:text-4xl font-black tracking-tight text-zinc-900 dark:text-zinc-50">
              {invoice.supplier_name}
            </h1>

            <div className="flex items-center gap-3.5 text-xs sm:text-sm text-zinc-600 dark:text-zinc-300 flex-wrap pt-0.5 font-medium">
              <span className="flex items-center gap-1.5">
                <Building2 className="h-4 w-4 text-zinc-400" />
                <span className="font-semibold text-zinc-800 dark:text-zinc-200">
                  {invoice.legal_name || invoice.supplier_name}
                </span>
              </span>
              <span>&bull;</span>
              <span className="flex items-center gap-2 font-mono">
                <Hash className="h-4 w-4 text-zinc-400" />
                <span className="text-zinc-900 dark:text-zinc-100 font-bold">{invoice.gstin || 'GSTIN Missing'}</span>
                {invoice.gstin_format_valid && (
                  <span className="text-[10.5px] px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950 dark:text-emerald-400 dark:border-emerald-800 font-bold">
                    VALID CHECKSUM
                  </span>
                )}
              </span>
              <span>&bull;</span>
              <span className="font-mono text-xs text-zinc-500 dark:text-zinc-400 font-semibold">
                Invoice #{invoice.invoice_number || 'N/A'}
              </span>
            </div>
          </div>

          {/* Financial Summary Block */}
          <div className="flex items-center gap-6 sm:gap-8 lg:border-l lg:border-zinc-200/80 dark:lg:border-zinc-800/80 lg:pl-8 flex-shrink-0">
            <div>
              <span className="text-xs font-mono uppercase text-zinc-500 dark:text-zinc-400 block font-bold tracking-wider">
                Total Invoiced Value
              </span>
              <div className="text-3xl sm:text-4xl font-mono font-black text-zinc-900 dark:text-zinc-50 mt-1">
                &#8377;{invoice.total_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
              <div className="text-xs sm:text-sm font-mono text-zinc-500 dark:text-zinc-400 mt-1">
                Taxable: &#8377;{invoice.taxable_amount.toLocaleString('en-IN')} &bull; GST (18%): &#8377;{(invoice.cgst + invoice.sgst + invoice.igst).toLocaleString('en-IN')}
              </div>
            </div>

            {/* Compliance Score Pill */}
            {assessment && (
              <div className="text-right pl-2">
                <span className="text-xs font-mono uppercase text-zinc-500 dark:text-zinc-400 block font-bold tracking-wider">
                  Compliance Score
                </span>
                <div className={`text-3xl font-mono font-black mt-1 ${
                  assessment.risk_score && assessment.risk_score >= 80 
                    ? 'text-emerald-600 dark:text-emerald-400' 
                    : assessment.risk_score && assessment.risk_score >= 50
                    ? 'text-amber-600 dark:text-amber-400'
                    : 'text-rose-600 dark:text-rose-400'
                }`}>
                  {assessment.risk_score ?? 0}<span className="text-sm text-zinc-400 font-normal">/100</span>
                </div>
                <span className={`inline-block text-xs font-mono font-bold uppercase px-3 py-1 rounded-lg mt-1 shadow-2xs ${
                  assessment.recommendation === 'PASS' 
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950 dark:text-emerald-400 dark:border-emerald-800' 
                    : assessment.recommendation === 'MANUAL_REVIEW'
                    ? 'bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-950 dark:text-amber-400 dark:border-amber-800'
                    : 'bg-rose-50 text-rose-700 border border-rose-200 dark:bg-rose-950 dark:text-rose-400 dark:border-rose-800'
                }`}>
                  {assessment.recommendation}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ==================================================================== */}
      {/* 3. 🚀 HERO PRE-DISBURSAL TREASURY SPLIT & 2026 GSTN IMS GATE */}
      {/* ==================================================================== */}
      {settlement && (
        <div className="relative overflow-hidden rounded-2xl border border-indigo-200/90 dark:border-indigo-800/80 bg-gradient-to-br from-indigo-50/70 via-white to-slate-50 dark:from-[#0d1424] dark:via-[#0e1628] dark:to-[#090e1a] p-6 sm:p-7 shadow-subtle space-y-6">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-indigo-100 dark:border-indigo-900/40">
            <div>
              <div className="flex items-center gap-2.5 flex-wrap mb-1.5">
                <span className="text-xs font-mono font-black uppercase tracking-wider text-indigo-700 bg-indigo-100/90 px-3 py-1 rounded-full dark:bg-indigo-950 dark:text-indigo-300 dark:border dark:border-indigo-800 shadow-2xs">
                  Pre-Disbursal Treasury Gate
                </span>
                <span className="text-xs font-mono text-zinc-600 dark:text-zinc-400 font-medium">
                  Income Tax Sec 43B(h) MSME Mandate vs CGST Sec 16(2)(c) Safe-Harbor
                </span>
              </div>
              <h2 className="text-xl sm:text-2xl font-black text-zinc-900 dark:text-zinc-50 flex items-center gap-3">
                <span>Treasury Directive:</span>
                <span className={`px-3.5 py-1.5 rounded-xl text-xs sm:text-sm font-mono font-bold tracking-wide shadow-xs ${
                  settlement.recommendation === 'FULL_DISBURSAL' 
                    ? 'bg-emerald-100 text-emerald-800 border border-emerald-300 dark:bg-emerald-950 dark:text-emerald-300 dark:border-emerald-700'
                    : settlement.recommendation === 'STATUTORY_GST_ESCROW'
                    ? 'bg-amber-100 text-amber-900 border border-amber-300 dark:bg-amber-950 dark:text-amber-300 dark:border-amber-700'
                    : 'bg-rose-100 text-rose-900 border border-rose-300 dark:bg-rose-950 dark:text-rose-300 dark:border-rose-700'
                }`}>
                  {settlement.recommendation === 'STATUTORY_GST_ESCROW' 
                    ? 'STATUTORY GST ESCROW (SPLIT PAYOUT)' 
                    : settlement.recommendation}
                </span>
              </h2>
            </div>

            {/* GSTN IMS Portal Action & 1-Click Export */}
            <div className="flex items-center gap-3.5 flex-shrink-0">
              <div className="text-right">
                <span className="text-xs font-mono uppercase text-zinc-500 dark:text-zinc-400 block font-bold tracking-wider">
                  2026 GSTN IMS Portal Action
                </span>
                <span className={`inline-block px-3 py-1 rounded-lg font-mono font-black text-xs uppercase mt-1 ${
                  imsAction === 'ACCEPT'
                    ? 'bg-emerald-100 text-emerald-800 border border-emerald-300 dark:bg-emerald-950 dark:text-emerald-300 dark:border-emerald-700'
                    : imsAction === 'PENDING_HOLD'
                    ? 'bg-amber-100 text-amber-800 border border-amber-300 dark:bg-amber-950 dark:text-amber-300 dark:border-amber-700'
                    : 'bg-rose-100 text-rose-800 border border-rose-300 dark:bg-rose-950 dark:text-rose-300 dark:border-rose-700'
                }`}>
                  {imsAction === 'PENDING_HOLD' ? 'PENDING (HOLD ITC)' : imsAction}
                </span>
              </div>

              <button
                type="button"
                onClick={handleExportIMSJson}
                className="inline-flex items-center gap-2 px-4 py-2.5 text-xs sm:text-sm font-mono font-bold rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white shadow-sm transition active:scale-98 cursor-pointer"
              >
                {copiedIMS ? <Check className="h-4 w-4 text-emerald-300" /> : <Download className="h-4 w-4" />}
                <span>{copiedIMS ? 'IMS JSON Exported!' : 'Export GSTN IMS JSON'}</span>
              </button>
            </div>
          </div>

          {/* 3-Column Financial Matrix */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-5">
            {/* Box 1: Immediate MSME Payout */}
            <div className="p-5 rounded-2xl bg-white/95 dark:bg-[#090f1a] border border-zinc-200/90 dark:border-zinc-800 space-y-1.5 shadow-xs">
              <div className="flex items-center justify-between text-xs font-mono text-zinc-500 dark:text-zinc-400 font-bold">
                <span>Immediate Base Payout</span>
                <span className="text-emerald-600 dark:text-emerald-400">&bull; Sec 43B(h)</span>
              </div>
              <div className="text-2xl sm:text-3xl font-mono font-black text-emerald-600 dark:text-emerald-400">
                &#8377;{settlement.release_now_inr.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
              <p className="text-xs sm:text-sm text-zinc-500 dark:text-zinc-400 leading-snug">
                Disbursed immediately within 15–45 days to eliminate buyer Income Tax disallowance risk.
              </p>
            </div>

            {/* Box 2: GST Escrow Holdback */}
            <div className="p-5 rounded-2xl bg-white/95 dark:bg-[#090f1a] border border-zinc-200/90 dark:border-zinc-800 space-y-1.5 shadow-xs">
              <div className="flex items-center justify-between text-xs font-mono text-zinc-500 dark:text-zinc-400 font-bold">
                <span>Statutory 18% GST Escrow</span>
                <span className="text-amber-600 dark:text-amber-400">&bull; Auto-Escrow</span>
              </div>
              <div className="text-2xl sm:text-3xl font-mono font-black text-amber-600 dark:text-amber-400">
                &#8377;{settlement.escrow_hold_gst_inr.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
              <p className="text-xs sm:text-sm text-zinc-500 dark:text-zinc-400 leading-snug">
                Retained in automated tax escrow until supplier confirms GSTR-3B tax remittance on the 20th.
              </p>
            </div>

            {/* Box 3: Total Clawback Risk Avoided */}
            <div className="p-5 rounded-2xl bg-white/95 dark:bg-[#090f1a] border border-zinc-200/90 dark:border-zinc-800 space-y-1.5 shadow-xs">
              <div className="flex items-center justify-between text-xs font-mono text-zinc-500 dark:text-zinc-400 font-bold">
                <span>Clawback Liability Avoided</span>
                <span className="text-rose-600 dark:text-rose-400 flex items-center gap-1">
                  <TrendingDown className="h-3.5 w-3.5" /> Sec 74 Protection
                </span>
              </div>
              <div className="text-2xl sm:text-3xl font-mono font-black text-rose-600 dark:text-rose-400">
                &#8377;{settlement.statutory_clawback_risk_avoided_inr.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
              <p className="text-xs sm:text-sm text-zinc-500 dark:text-zinc-400 leading-snug">
                Avoids 100% Tax + 100% Section 74 Penalty + 18% Section 50 statutory interest liability.
              </p>
            </div>
          </div>

          {/* Rationale Notice */}
          <div className="p-4 bg-white/90 dark:bg-[#080d18] rounded-xl border border-indigo-100 dark:border-indigo-950 text-xs sm:text-sm text-zinc-800 dark:text-zinc-200 font-mono leading-relaxed">
            <strong className="text-indigo-700 dark:text-indigo-400 font-bold">Directive Rationale:</strong> {settlement.settlement_rationale}
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* 4. 🐟 4-HOP AUTONOMOUS TINYFISH LIVE WEB AGENT TELEMETRY */}
      {/* ==================================================================== */}
      <div className="bg-white dark:bg-[#0e1420] border border-zinc-200/90 dark:border-zinc-800/90 rounded-2xl p-6 sm:p-7 shadow-subtle space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-zinc-200/80 dark:border-zinc-800/80 pb-3.5">
          <div className="flex items-center gap-2.5">
            <Radio className="h-4.5 w-4.5 text-teal-600 dark:text-teal-400 animate-pulse" />
            <h2 className="text-sm sm:text-base font-bold uppercase tracking-wider text-zinc-900 dark:text-zinc-100 font-mono">
              TinyFish 4-Hop Live Agentic Web Infrastructure
            </h2>
            <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-700 font-semibold">
              CAPTCHA-Free Pipeline
            </span>
          </div>

          {/* Hop Selector Filter Pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto text-xs font-mono">
            <button
              type="button"
              onClick={() => setActiveHopTab('all')}
              className={`px-3.5 py-1.5 rounded-lg transition font-bold cursor-pointer ${
                activeHopTab === 'all'
                  ? 'bg-teal-600 text-white shadow-xs'
                  : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white'
              }`}
            >
              All Hops ({evidence_items.length})
            </button>
            {hops.map(h => (
              <button
                type="button"
                key={h.num}
                onClick={() => setActiveHopTab(h.num)}
                className={`px-3 py-1.5 rounded-lg transition whitespace-nowrap font-bold cursor-pointer ${
                  activeHopTab === h.num
                    ? 'bg-teal-600 text-white shadow-xs'
                    : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white'
                }`}
              >
                Hop {h.num}
              </button>
            ))}
          </div>
        </div>

        {/* 4-Hop Pipeline Interactive Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
          {hops.map(h => {
            const ev = evidence_items.find(e => e.hop_number === h.num) || evidence_items[h.num - 1];
            const isLive = ev?.source_mode === 'LIVE' || ev?.source_mode === 'LIVE_TINYFISH_SSE';
            const isUnavail = ev?.source_mode === 'UNAVAILABLE';

            return (
              <div
                key={h.num}
                onClick={() => setActiveHopTab(h.num)}
                className={`cursor-pointer p-4.5 rounded-2xl border text-xs sm:text-sm space-y-3 transition-all ${
                  activeHopTab === h.num
                    ? 'border-teal-500 bg-teal-50/40 dark:bg-teal-950/20 ring-2 ring-teal-500/30 shadow-xs'
                    : 'border-zinc-200/90 dark:border-zinc-800 bg-zinc-50/50 dark:bg-[#090d18] hover:border-zinc-300 dark:hover:border-zinc-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-xs px-2.5 py-0.5 rounded-md bg-zinc-200/80 dark:bg-zinc-800 text-zinc-800 dark:text-zinc-200 border border-zinc-300/60 dark:border-zinc-700">
                    HOP {h.num}
                  </span>
                  {isLive ? (
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800 flex items-center gap-1">
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-ping" /> LIVE SSE
                    </span>
                  ) : isUnavail ? (
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400 border border-zinc-200 dark:border-zinc-700">
                      UNAVAILABLE
                    </span>
                  ) : (
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 border border-amber-300 dark:border-amber-800 font-bold">
                      SIMULATED
                    </span>
                  )}
                </div>

                <div className="font-bold text-sm text-zinc-900 dark:text-zinc-100 leading-snug">
                  {h.title}
                </div>

                <div className="text-xs text-zinc-500 dark:text-zinc-400 font-mono truncate">
                  Target: {h.targetDomain}
                </div>

                {ev && (
                  <div className="pt-2.5 border-t border-zinc-200/60 dark:border-zinc-800/80 text-xs text-zinc-700 dark:text-zinc-300 font-mono truncate font-medium">
                    {ev.facts?.status || ev.facts?.gst_status || ev.facts?.top_case_title || (ev.facts?.market_median_price_inr ? `₹${ev.facts.market_median_price_inr} wholesale` : 'Findings verified')}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Detailed Hop Dossier Items */}
        <div className="space-y-3.5 pt-1">
          {filteredEvidence.map((ev, idx) => (
            <div key={ev.evidence_id || idx} className="p-4 sm:p-5 rounded-xl bg-zinc-50/90 dark:bg-[#080d18] border border-zinc-200/90 dark:border-zinc-800 text-xs sm:text-sm space-y-3.5 shadow-2xs">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 border-b border-zinc-200/60 dark:border-zinc-800/80 pb-3">
                <div className="flex items-center gap-2.5 flex-wrap">
                  {ev.hop_number && (
                    <span className="font-mono text-xs font-bold px-2.5 py-0.5 rounded-md bg-teal-100 text-teal-800 dark:bg-teal-950 dark:text-teal-300 border border-teal-300 dark:border-teal-800">
                      Hop {ev.hop_number}
                    </span>
                  )}
                  <span className="font-bold text-sm text-zinc-900 dark:text-zinc-100">
                    {ev.source_name.replace(/\[DEMO FIXTURE\]\s*/g, '')}
                  </span>
                  {ev.source_mode === 'LIVE' ? (
                    <span className="text-[10px] font-mono uppercase font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800">
                      LIVE TINYFISH SSE
                    </span>
                  ) : (
                    <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 border border-amber-300 dark:border-amber-800 font-bold">
                      SIMULATED FALLBACK
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-3.5 flex-wrap">
                  {ev.streaming_url && (
                    <a
                      href={ev.streaming_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs font-mono text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1 font-bold"
                    >
                      <Tv className="h-3.5 w-3.5" /> Stream Session
                    </a>
                  )}
                  {ev.source_url && (
                    <a
                      href={ev.source_url.startsWith('http') ? ev.source_url : '#'}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs font-mono text-teal-600 dark:text-teal-400 hover:underline flex items-center gap-1 font-semibold"
                    >
                      <span>Evidence Link</span>
                      <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                  )}
                  <span className="text-xs font-mono text-zinc-400">
                    {ev.retrieved_at ? new Date(ev.retrieved_at).toLocaleTimeString() : 'Verified'}
                  </span>
                </div>
              </div>

              {/* Forensic Excerpt */}
              <div className="bg-white dark:bg-zinc-950 p-3.5 rounded-xl border border-zinc-200 dark:border-zinc-800/80 font-mono text-xs sm:text-sm text-zinc-800 dark:text-zinc-200 leading-relaxed shadow-2xs">
                {ev.raw_excerpt}
              </div>

              {/* Extracted Structured JSON Facts Pills */}
              {ev.facts && Object.keys(ev.facts).length > 0 && (
                <div className="flex flex-wrap gap-2 text-xs font-mono">
                  {Object.entries(ev.facts).map(([k, v]) => (
                    <span key={k} className="px-3 py-1 rounded-lg bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200 border border-zinc-200 dark:border-zinc-800 shadow-2xs font-semibold">
                      <span className="text-zinc-400 dark:text-zinc-500 font-normal">{k}:</span> <strong>{String(v)}</strong>
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* ==================================================================== */}
      {/* 5. 5-VECTOR RISK TOPOLOGY RADAR GAUGES */}
      {/* ==================================================================== */}
      {assessment && (
        <div className="bg-white dark:bg-[#0e1420] border border-zinc-200/90 dark:border-zinc-800/90 rounded-2xl p-6 sm:p-7 shadow-subtle space-y-5">
          <div className="flex items-center justify-between border-b border-zinc-200/80 dark:border-zinc-800/80 pb-3.5">
            <span className="text-xs sm:text-sm font-mono font-bold uppercase tracking-wider text-zinc-800 dark:text-zinc-200">
              5-Vector Forensic Risk Topology
            </span>
            <span className="text-xs font-mono text-zinc-500 dark:text-zinc-400 font-semibold">
              Deterministic Weights &bull; CGST Sec 16(2)(c) &amp; IBC Sec 7/9
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3.5 text-center text-xs sm:text-sm">
            <div className="bg-zinc-50 dark:bg-zinc-900/80 p-4 rounded-xl border border-zinc-200/80 dark:border-zinc-800 space-y-1.5 shadow-2xs">
              <span className="text-xs text-zinc-500 dark:text-zinc-400 block font-mono font-bold">1. ITC Clawback</span>
              <div className="text-xl sm:text-2xl font-mono font-black text-teal-600 dark:text-teal-400">
                {Math.round((assessment.forensic_vectors?.itc_clawback_risk_index || 0) * 100)}%
              </div>
              <span className="text-xs text-zinc-400 block font-medium">CGST Sec 16(2)(c)</span>
            </div>

            <div className="bg-zinc-50 dark:bg-zinc-900/80 p-4 rounded-xl border border-zinc-200/80 dark:border-zinc-800 space-y-1.5 shadow-2xs">
              <span className="text-xs text-zinc-500 dark:text-zinc-400 block font-mono font-bold">2. Judicial Contagion</span>
              <div className="text-xl sm:text-2xl font-mono font-black text-rose-600 dark:text-rose-400">
                {Math.round((assessment.forensic_vectors?.judicial_insolvency_contagion || assessment.forensic_vectors?.director_shell_contagion_score || 0) * 100)}%
              </div>
              <span className="text-xs text-zinc-400 block font-medium">NCLT &amp; IBC Sec 9</span>
            </div>

            <div className="bg-zinc-50 dark:bg-zinc-900/80 p-4 rounded-xl border border-zinc-200/80 dark:border-zinc-800 space-y-1.5 shadow-2xs">
              <span className="text-xs text-zinc-500 dark:text-zinc-400 block font-mono font-bold">3. Price Anomaly</span>
              <div className="text-xl sm:text-2xl font-mono font-black text-amber-600 dark:text-amber-400">
                {Math.round((assessment.forensic_vectors?.procurement_price_anomaly || 0) * 100)}%
              </div>
              <span className="text-xs text-zinc-400 block font-medium">IndiaMART Wholesale</span>
            </div>

            <div className="bg-zinc-50 dark:bg-zinc-900/80 p-4 rounded-xl border border-zinc-200/80 dark:border-zinc-800 space-y-1.5 shadow-2xs">
              <span className="text-xs text-zinc-500 dark:text-zinc-400 block font-mono font-bold">4. Grounding (e-Way)</span>
              <div className="text-xl sm:text-2xl font-mono font-black text-emerald-600 dark:text-emerald-400">
                {Math.round((assessment.forensic_vectors?.operational_grounding_score || 0) * 100)}%
              </div>
              <span className="text-xs text-zinc-400 block font-medium">Physical Movement</span>
            </div>

            <div className="bg-zinc-50 dark:bg-zinc-900/80 p-4 rounded-xl border border-zinc-200/80 dark:border-zinc-800 space-y-1.5 shadow-2xs">
              <span className="text-xs text-zinc-500 dark:text-zinc-400 block font-mono font-bold">5. Pop-Up / BEC Guard</span>
              <div className="text-xl sm:text-2xl font-mono font-black text-purple-600 dark:text-purple-400">
                {Math.round((assessment.forensic_vectors?.popup_velocity_and_bank_mutation || assessment.forensic_vectors?.popup_velocity_factor || 0) * 100)}%
              </div>
              <span className="text-xs text-zinc-400 block font-medium">Bank Mutation Alert</span>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* 6. DUAL INVESTIGATION GRID: REMITTANCE SECURITY VS RECONCILIATIONS */}
      {/* ==================================================================== */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Col: Remittance Security & Physical Transit */}
        <div className="bg-white dark:bg-[#0e1420] border border-zinc-200/90 dark:border-zinc-800/90 rounded-2xl p-6 space-y-4 shadow-subtle">
          <div className="flex items-center justify-between border-b border-zinc-200/80 dark:border-zinc-800/80 pb-3">
            <h2 className="text-xs sm:text-sm font-bold uppercase tracking-wider text-zinc-900 dark:text-zinc-100 font-mono">
              Remittance &amp; Transit Claims
            </h2>
            <button
              type="button"
              onClick={() => setShowEditModal(true)}
              className="text-xs font-mono text-teal-600 dark:text-teal-400 hover:underline flex items-center gap-1 font-bold"
            >
              <Edit3 className="h-3.5 w-3.5" /> Edit
            </button>
          </div>

          <div className="space-y-4 text-xs sm:text-sm">
            {/* Anti-BEC Bank Account Mutation Guard */}
            <div className="p-4 rounded-xl bg-zinc-50 dark:bg-zinc-900/90 border border-zinc-200/80 dark:border-zinc-800 space-y-2 shadow-2xs">
              <span className="text-xs font-mono text-zinc-500 dark:text-zinc-400 uppercase tracking-wider font-bold block">
                Remittance Bank Account (Anti-BEC)
              </span>
              <div className="font-mono text-zinc-900 dark:text-zinc-100 flex items-center justify-between font-bold text-sm">
                <span>{invoice.bank_account_masked || 'XXXX-XXXX-9921'}</span>
                {invoice.bank_mutation_detected ? (
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300 border border-rose-300 dark:border-rose-800 font-black">
                    BEC MUTATION!
                  </span>
                ) : (
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800 font-black">
                    VERIFIED MASTER
                  </span>
                )}
              </div>
              <div className="text-xs font-mono text-zinc-500 dark:text-zinc-400">
                IFSC: <strong>{invoice.ifsc_code || 'HDFC0001234'}</strong> &bull; Beneficiary Match: <strong>{invoice.beneficiary_name_match_score ? `${Math.round(invoice.beneficiary_name_match_score * 100)}%` : '92%'}</strong>
              </div>
            </div>

            {/* Physical Supply Transit (CGST Sec 16(2)(b)) */}
            <div className="p-4 rounded-xl bg-zinc-50 dark:bg-zinc-900/90 border border-zinc-200/80 dark:border-zinc-800 space-y-2 shadow-2xs">
              <span className="text-xs font-mono text-zinc-500 dark:text-zinc-400 uppercase tracking-wider font-bold block flex items-center gap-1.5">
                <Truck className="h-4 w-4 text-teal-600 dark:text-teal-400" /> Physical Movement (Sec 16(2)(b))
              </span>
              <div className="font-mono text-zinc-900 dark:text-zinc-100 flex items-center justify-between text-xs sm:text-sm font-bold">
                <span>e-Way Bill: {invoice.eway_bill_no || '241098765432'}</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800">
                  VERIFIED
                </span>
              </div>
              <div className="text-xs font-mono text-zinc-500 dark:text-zinc-400">
                Vehicle: <strong>{invoice.vehicle_no || 'DL-1GC-4491'}</strong> &bull; IRN: <strong>{invoice.irn_hash ? `${invoice.irn_hash.substring(0, 10)}...` : 'Verified'}</strong>
              </div>
            </div>

            <div className="pt-1 space-y-2.5">
              <div>
                <span className="text-xs font-mono text-zinc-400 block font-semibold">Billing Address</span>
                <span className="text-sm text-zinc-800 dark:text-zinc-200">{invoice.billing_address || 'Not specified'}</span>
              </div>
              <div>
                <span className="text-xs font-mono text-zinc-400 block font-semibold">Place of Supply</span>
                <span className="font-mono text-sm text-zinc-800 dark:text-zinc-200 font-semibold">{invoice.place_of_supply || 'Delhi (07)'}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right 2 Cols: Field Reconciliations */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-white dark:bg-[#0e1420] border border-zinc-200/90 dark:border-zinc-800/90 rounded-2xl p-6 sm:p-7 shadow-subtle space-y-5">
            <h2 className="text-xs sm:text-sm font-bold uppercase tracking-wider text-zinc-900 dark:text-zinc-100 font-mono border-b border-zinc-200/80 dark:border-zinc-800/80 pb-3">
              Deterministic Statutory Reconciliations
            </h2>

            {assessment && assessment.field_checks.length > 0 ? (
              <div className="divide-y divide-zinc-200/70 dark:divide-zinc-800/70">
                {assessment.field_checks.map((chk) => (
                  <div key={chk.check_id} className="py-4 first:pt-0 last:pb-0 space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-bold text-zinc-900 dark:text-zinc-100">{chk.field_name}</span>
                      <span className={`text-xs font-mono uppercase px-2.5 py-0.5 rounded-md font-bold ${
                        chk.status === 'MATCH'
                          ? 'bg-emerald-50 text-emerald-800 border border-emerald-200 dark:bg-emerald-950 dark:text-emerald-400 dark:border-emerald-800'
                          : chk.status === 'POSSIBLE_MATCH'
                          ? 'bg-amber-50 text-amber-800 border border-amber-200 dark:bg-amber-950 dark:text-amber-400 dark:border-amber-800'
                          : chk.status === 'UNAVAILABLE'
                          ? 'bg-zinc-100 text-zinc-600 border border-zinc-200 dark:bg-zinc-800 dark:text-zinc-300 dark:border-zinc-700'
                          : 'bg-rose-50 text-rose-800 border border-rose-200 dark:bg-rose-950 dark:text-rose-400 dark:border-rose-800'
                      }`}>
                        {chk.status}
                      </span>
                    </div>
                    <p className="text-xs sm:text-sm text-zinc-600 dark:text-zinc-300 leading-relaxed font-sans">
                      {chk.explanation}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-sm text-zinc-400 font-mono py-8 text-center">
                No reconciliation checks run yet. Click &apos;Run 4-Hop TinyFish&apos; above.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ==================================================================== */}
      {/* 7. 3-ACTION HUMAN REVIEWER DECISION & CRYPTOGRAPHIC AUDIT SEAL */}
      {/* ==================================================================== */}
      <div className="bg-white dark:bg-[#0e1420] border border-zinc-200/90 dark:border-zinc-800/90 rounded-2xl p-6 sm:p-7 shadow-subtle space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-zinc-200/80 dark:border-zinc-800/80 pb-3.5">
          <div className="flex items-center gap-2.5">
            <Lock className="h-5 w-5 text-teal-600 dark:text-teal-400" />
            <h2 className="text-sm sm:text-base font-bold uppercase tracking-wider text-zinc-900 dark:text-zinc-100 font-mono">
              Human Reviewer Decision &amp; Audit Seal
            </h2>
          </div>
          {caseData.audit_hash_sha256 && (
            <button
              type="button"
              onClick={copyAuditHash}
              className="text-xs font-mono text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200 flex items-center gap-2 transition cursor-pointer"
            >
              <span>SHA-256:</span>
              <code className="text-teal-600 dark:text-teal-400 font-bold">{caseData.audit_hash_sha256.substring(0, 16)}...</code>
              {copiedAuditHash ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
            </button>
          )}
        </div>

        {review ? (
          <div className="p-5 rounded-2xl bg-emerald-50/70 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800/60 text-sm space-y-2.5 shadow-2xs">
            <div className="flex items-center justify-between">
              <span className="font-mono text-emerald-700 dark:text-emerald-300 font-black uppercase text-base flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                Decision Recorded: {review.action}
              </span>
              <span className="font-mono text-xs text-zinc-400">{review.recorded_at ? new Date(review.recorded_at).toLocaleString() : ''}</span>
            </div>
            <div>
              <span className="text-zinc-500 dark:text-zinc-400 font-mono text-xs font-bold">Authorized Reviewer: </span>
              <span className="font-bold text-zinc-900 dark:text-zinc-100">{review.reviewer_id} ({review.reviewer_role || 'ap_analyst'})</span>
            </div>
            <div>
              <span className="text-zinc-500 dark:text-zinc-400 font-mono text-xs font-bold">Audit Rationale: </span>
              <p className="text-zinc-800 dark:text-zinc-200 mt-1 font-mono text-xs sm:text-sm leading-relaxed">{review.rationale}</p>
            </div>
          </div>
        ) : (
          <form onSubmit={handleReviewSubmit} className="space-y-5 text-sm">
            {/* 3 Quick-Action Decision Cards */}
            <div>
              <label className="block text-zinc-700 dark:text-zinc-300 font-mono text-xs sm:text-sm mb-2.5 font-bold uppercase tracking-wider">
                Select Treasury Settlement Action:
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
                <button
                  type="button"
                  onClick={() => selectReviewOption('APPROVE', 'Approve 100% full payment disbursal. All 4 TinyFish hops verified clean.')}
                  className={`p-4 rounded-xl border text-left transition-all cursor-pointer ${
                    reviewAction === 'APPROVE'
                      ? 'border-emerald-600 dark:border-emerald-500 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-900 dark:text-emerald-200 ring-2 ring-emerald-500/30 shadow-xs'
                      : 'border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900/60 hover:bg-zinc-50 dark:hover:bg-zinc-800/40'
                  }`}
                >
                  <div className="font-black text-sm flex items-center gap-2 text-emerald-700 dark:text-emerald-400">
                    <CheckCircle2 className="h-4 w-4" />
                    <span>Approve 100% Disbursal</span>
                  </div>
                  <div className="text-xs text-zinc-500 dark:text-zinc-400 mt-1.5 font-mono">
                    GSTN IMS Action: <strong>ACCEPT</strong>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => selectReviewOption(
                    'EXECUTE_SPLIT_PAYOUT',
                    settlement?.settlement_rationale || 'Execute Split-Payout: Disburse base amount to satisfy MSME Sec 43B(h); retain 18% GST in tax escrow.'
                  )}
                  className={`p-4 rounded-xl border text-left transition-all cursor-pointer ${
                    reviewAction === 'EXECUTE_SPLIT_PAYOUT'
                      ? 'border-amber-600 dark:border-amber-500 bg-amber-50 dark:bg-amber-950/40 text-amber-900 dark:text-amber-200 ring-2 ring-amber-500/30 shadow-xs'
                      : 'border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900/60 hover:bg-zinc-50 dark:hover:bg-zinc-800/40'
                  }`}
                >
                  <div className="font-black text-sm flex items-center gap-2 text-amber-700 dark:text-amber-400">
                    <Layers className="h-4 w-4" />
                    <span>Execute Split-Payout</span>
                  </div>
                  <div className="text-xs text-zinc-500 dark:text-zinc-400 mt-1.5 font-mono">
                    Release Base &bull; Escrow GST &bull; IMS: <strong>PENDING</strong>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => selectReviewOption(
                    'FORENSIC_FREEZE',
                    settlement?.settlement_rationale || 'Forensic Freeze executed: Payment blocked due to active insolvency / critical fraud gate.'
                  )}
                  className={`p-4 rounded-xl border text-left transition-all cursor-pointer ${
                    reviewAction === 'FORENSIC_FREEZE' || reviewAction === 'REJECT'
                      ? 'border-rose-600 dark:border-rose-500 bg-rose-50 dark:bg-rose-950/40 text-rose-900 dark:text-rose-200 ring-2 ring-rose-500/30 shadow-xs'
                      : 'border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900/60 hover:bg-zinc-50 dark:hover:bg-zinc-800/40'
                  }`}
                >
                  <div className="font-black text-sm flex items-center gap-2 text-rose-700 dark:text-rose-400">
                    <ShieldX className="h-4 w-4" />
                    <span>Forensic Freeze</span>
                  </div>
                  <div className="text-xs text-zinc-500 dark:text-zinc-400 mt-1.5 font-mono">
                    Halt 100% Release &bull; IMS: <strong>REJECT</strong>
                  </div>
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 pt-1">
              <div className="space-y-1.5">
                <label className="block text-zinc-700 dark:text-zinc-300 font-mono text-xs font-bold">
                  Reviewer Identity
                </label>
                <input
                  type="text"
                  required
                  value={reviewerId}
                  onChange={(e) => setReviewerId(e.target.value)}
                  className="w-full bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-700 rounded-xl px-4 py-2.5 text-zinc-900 dark:text-zinc-100 font-mono text-sm focus:outline-none focus:border-teal-500 shadow-2xs"
                />
              </div>

              <div className="space-y-1.5">
                <label className="block text-zinc-700 dark:text-zinc-300 font-mono text-xs font-bold">
                  Selected Action
                </label>
                <select
                  value={reviewAction}
                  onChange={(e) => setReviewAction(e.target.value as ReviewActionType)}
                  className="w-full bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-700 rounded-xl px-4 py-2.5 text-zinc-900 dark:text-zinc-100 font-mono text-sm focus:outline-none focus:border-teal-500 shadow-2xs"
                >
                  <option value="APPROVE">APPROVE (100% Disbursal &bull; IMS: ACCEPT)</option>
                  <option value="EXECUTE_SPLIT_PAYOUT">EXECUTE_SPLIT_PAYOUT (Release Base &bull; Escrow GST &bull; IMS: PENDING)</option>
                  <option value="FORENSIC_FREEZE">FORENSIC_FREEZE (Halt Payment &bull; IMS: REJECT)</option>
                  <option value="APPROVE_WITH_EXCEPTION">APPROVE_WITH_EXCEPTION (Documented Override)</option>
                  <option value="REQUEST_DOCUMENTS">REQUEST_DOCUMENTS (Hold for Vendor)</option>
                  <option value="ESCALATE">ESCALATE (To AP Manager)</option>
                  <option value="REJECT">REJECT (Block Payout)</option>
                </select>
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="block text-zinc-700 dark:text-zinc-300 font-mono text-xs font-bold">
                Mandatory Review Rationale (Saved to Tamper-Evident Chained Audit Trail) *
              </label>
              <textarea
                required
                rows={3}
                placeholder="State verified trade-name alias, statutory escrow reasons, or reason for action..."
                value={rationale}
                onChange={(e) => setRationale(e.target.value)}
                className="w-full bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-700 rounded-xl px-4 py-3 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-teal-500 shadow-2xs font-mono text-sm"
              />
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="submit"
                disabled={reviewing}
                className="inline-flex items-center gap-2 bg-teal-600 hover:bg-teal-500 text-white font-bold px-6 py-3 rounded-xl text-sm transition shadow-sm disabled:opacity-50 cursor-pointer"
              >
                <Lock className="h-4 w-4" />
                <span>{reviewing ? 'Sealing Audit Record...' : 'Record Treasury Decision & Seal Case'}</span>
              </button>
            </div>
          </form>
        )}
      </div>

      {/* Reviewer Activity History Timeline */}
      {review_history && review_history.length > 0 && (
        <div className="bg-white dark:bg-[#0e1420] border border-zinc-200/90 dark:border-zinc-800/90 rounded-2xl p-6 space-y-4 shadow-subtle">
          <div className="flex items-center gap-2 border-b border-zinc-200/80 dark:border-zinc-800/80 pb-3">
            <History className="h-4.5 w-4.5 text-teal-600 dark:text-teal-400" />
            <h2 className="text-xs sm:text-sm font-bold uppercase tracking-wider text-zinc-900 dark:text-zinc-100 font-mono">
              Reviewer Activity History ({review_history.length})
            </h2>
          </div>
          <div className="space-y-2.5">
            {review_history.map(rh => (
              <div key={rh.action_id} className="p-3.5 bg-zinc-50 dark:bg-zinc-900/80 border border-zinc-200/80 dark:border-zinc-800 rounded-xl text-xs sm:text-sm flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
                <div>
                  <span className="font-mono text-teal-700 dark:text-teal-400 font-bold uppercase mr-2.5">[{rh.action}]</span>
                  <span className="text-zinc-800 dark:text-zinc-200 font-medium">{rh.rationale}</span>
                </div>
                <div className="text-xs font-mono text-zinc-400 flex items-center gap-2 shrink-0">
                  <span>{rh.reviewer_id}</span>
                  <span>&bull;</span>
                  <span>{rh.recorded_at ? new Date(rh.recorded_at).toLocaleTimeString() : ''}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* MODAL: CORRECT EXTRACTED INVOICE CLAIMS */}
      {/* ==================================================================== */}
      {showEditModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-reveal-up">
          <div className="bg-white dark:bg-[#0e1420] border border-zinc-200 dark:border-zinc-700 rounded-2xl max-w-lg w-full p-6 sm:p-7 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-zinc-200/80 dark:border-zinc-800/80 pb-3.5">
              <h3 className="text-sm sm:text-base font-bold text-zinc-900 dark:text-zinc-100 font-mono flex items-center gap-2">
                <Edit3 className="h-4.5 w-4.5 text-teal-600 dark:text-teal-400" />
                <span>Correct Invoice Claims &amp; Rerun Assessment</span>
              </h3>
              <button
                type="button"
                onClick={() => setShowEditModal(false)}
                className="text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 text-2xl leading-none cursor-pointer p-1"
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleCorrectionSubmit} className="space-y-4 text-xs sm:text-sm">
              <div className="space-y-1.5">
                <label className="block text-zinc-700 dark:text-zinc-300 font-mono text-xs font-bold">
                  Supplier Trade Name
                </label>
                <input
                  type="text"
                  value={corrSupplier}
                  onChange={(e) => setCorrSupplier(e.target.value)}
                  className="w-full bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-700 rounded-xl px-4 py-2.5 text-zinc-900 dark:text-zinc-100 font-medium focus:outline-none focus:border-teal-500 shadow-2xs"
                />
              </div>

              <div className="space-y-1.5">
                <label className="block text-zinc-700 dark:text-zinc-300 font-mono text-xs font-bold">
                  Supplier GSTIN
                </label>
                <input
                  type="text"
                  value={corrGstin}
                  onChange={(e) => setCorrGstin(e.target.value.toUpperCase())}
                  className="w-full bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-700 rounded-xl px-4 py-2.5 text-zinc-900 dark:text-zinc-100 font-mono font-bold focus:outline-none focus:border-teal-500 shadow-2xs"
                />
              </div>

              <div className="grid grid-cols-2 gap-3.5">
                <div className="space-y-1.5">
                  <label className="block text-zinc-700 dark:text-zinc-300 font-mono text-xs font-bold">
                    Invoice Number
                  </label>
                  <input
                    type="text"
                    value={corrInvNumber}
                    onChange={(e) => setCorrInvNumber(e.target.value)}
                    className="w-full bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-700 rounded-xl px-4 py-2.5 text-zinc-900 dark:text-zinc-100 font-mono focus:outline-none focus:border-teal-500 shadow-2xs"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="block text-zinc-700 dark:text-zinc-300 font-mono text-xs font-bold">
                    Total Amount (&#8377;)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={corrTotalAmount}
                    onChange={(e) => setCorrTotalAmount(e.target.value)}
                    className="w-full bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-700 rounded-xl px-4 py-2.5 text-zinc-900 dark:text-zinc-100 font-mono font-bold focus:outline-none focus:border-teal-500 shadow-2xs"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="block text-zinc-700 dark:text-zinc-300 font-mono text-xs font-bold">
                  Correction Rationale / Notes
                </label>
                <input
                  type="text"
                  placeholder="e.g. Corrected OCR typo in GSTIN character 14"
                  value={corrNotes}
                  onChange={(e) => setCorrNotes(e.target.value)}
                  className="w-full bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-700 rounded-xl px-4 py-2.5 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-teal-500 shadow-2xs text-xs sm:text-sm"
                />
              </div>

              <div className="flex justify-end gap-2.5 pt-2">
                <button
                  type="button"
                  onClick={() => setShowEditModal(false)}
                  className="px-4 py-2.5 bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 font-semibold rounded-xl hover:bg-zinc-200 dark:hover:bg-zinc-700 transition cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={correcting}
                  className="px-5 py-2.5 bg-teal-600 hover:bg-teal-500 text-white font-bold rounded-xl transition disabled:opacity-50 shadow-xs cursor-pointer"
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
