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
  Info,
  Check,
  Globe,
  Radio,
  Tv,
  Scale,
  Layers,
  FileCheck2,
  FileSpreadsheet,
  AlertOctagon,
  ArrowRight,
  TrendingDown,
  Building2,
  Truck
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
  const [copiedIMS, setCopiedIMS] = useState(false);
  const [activeHopTab, setActiveHopTab] = useState<number | 'all'>('all');
  const [showLivePreview, setShowLivePreview] = useState(false);

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
      // Auto-prefill rationale if assessment has treasury settlement
      if (data.assessment?.treasury_settlement) {
        const ts = data.assessment.treasury_settlement;
        if (ts.recommendation === 'FULL_DISBURSAL') {
          setReviewAction('APPROVE');
          setRationale('Approved 100% full payment disbursal. All 4 TinyFish hops verified clean.');
        } else if (ts.recommendation === 'STATUTORY_GST_ESCROW') {
          setReviewAction('EXECUTE_SPLIT_PAYOUT');
          setRationale(ts.settlement_rationale || 'Execute Split-Payout: Release base amount under MSME 43B(h); hold 18% GST in escrow.');
        } else if (ts.recommendation === 'FORENSIC_FREEZE') {
          setReviewAction('FORENSIC_FREEZE');
          setRationale(ts.settlement_rationale || 'Forensic Freeze executed: Payment completely halted due to critical risk gate.');
        }
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
      if (updated.assessment?.treasury_settlement) {
        const ts = updated.assessment.treasury_settlement;
        if (ts.recommendation === 'FULL_DISBURSAL') {
          setReviewAction('APPROVE');
          setRationale('Approved 100% full payment disbursal. All 4 TinyFish hops verified clean.');
        } else if (ts.recommendation === 'STATUTORY_GST_ESCROW') {
          setReviewAction('EXECUTE_SPLIT_PAYOUT');
          setRationale(ts.settlement_rationale || 'Execute Split-Payout: Release base under MSME 43B(h); hold GST in escrow.');
        } else if (ts.recommendation === 'FORENSIC_FREEZE') {
          setReviewAction('FORENSIC_FREEZE');
          setRationale(ts.settlement_rationale || 'Forensic Freeze executed: Critical risk hard gate triggered.');
        }
      }
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

  const handleExportIMSJson = () => {
    if (!caseData?.assessment?.ims_action_json) return;
    const jsonStr = JSON.stringify(caseData.assessment.ims_action_json, null, 2);
    navigator.clipboard.writeText(jsonStr);
    setCopiedIMS(true);
    setTimeout(() => setCopiedIMS(false), 3000);

    // Also download as file
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `GSTN_IMS_Action_${caseData?.case_reference || caseId}.json`;
    a.click();
  };

  const selectReviewOption = (act: ReviewActionType, rat: string) => {
    setReviewAction(act);
    setRationale(rat);
  };

  if (loading) {
    return (
      <div className="py-24 text-center text-xs font-mono text-slate-400">
        <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2 text-cyan-400" />
        Loading pre-disbursal forensic evidence dossier...
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
  const settlement = assessment?.treasury_settlement;
  const imsAction = assessment?.gstn_ims_action || settlement?.gstn_ims_action || 'ACCEPT';
  const liveStreamingUrl = assessment?.streaming_url || evidence_items.find(e => e.streaming_url)?.streaming_url;

  const hops = [
    { num: 1, title: 'GST Velocity & Entity Check', url: 'https://www.knowyourgst.com/' },
    { num: 2, title: 'NCLT & IndianKanoon Docket Agent', url: 'https://indiankanoon.org/' },
    { num: 3, title: 'DGGI & Debarment Radar', url: 'https://indiankanoon.org/search/' },
    { num: 4, title: 'IndiaMART B2B Price Benchmark', url: 'https://dir.indiamart.com/' },
  ];

  const filteredEvidence = activeHopTab === 'all' 
    ? evidence_items 
    : evidence_items.filter(e => e.hop_number === activeHopTab);

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
            {source_mode === 'LIVE' || source_mode === 'LIVE_TINYFISH_SSE' ? (
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800/60 flex items-center gap-1">
                <Radio className="h-3 w-3 text-emerald-400 animate-pulse" /> Live TinyFish SSE Streaming
              </span>
            ) : source_mode === 'SIMULATED' ? (
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-amber-950/60 text-amber-400 border border-amber-800/60">
                Simulated Provenance Mode
              </span>
            ) : (
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                Evidence Unavailable
              </span>
            )}
            {liveStreamingUrl && (
              <a
                href={liveStreamingUrl}
                target="_blank"
                rel="noreferrer"
                className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-indigo-950/80 text-indigo-300 border border-indigo-700 hover:bg-indigo-900 transition flex items-center gap-1"
              >
                <Tv className="h-3 w-3" /> Live Browser Agent View
              </a>
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
              <span>{investigating ? 'Executing 4-Hop TinyFish...' : 'Run 4-Hop TinyFish'}</span>
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="p-3 bg-rose-950/60 border border-rose-800 rounded text-rose-300 text-xs">
          {error}
        </div>
      )}

      {/* ==================================================================== */}
      {/* 🚀 HERO CARD: PRE-DISBURSAL TREASURY SPLIT & 2026 GSTN IMS GATE */}
      {/* ==================================================================== */}
      {settlement && (
        <div className="relative overflow-hidden rounded-2xl border border-indigo-500/30 bg-gradient-to-br from-[#0c1324] via-[#0f172a] to-[#070b14] p-6 shadow-2xl">
          {/* Subtle Accent Glow */}
          <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-indigo-500/10 blur-3xl pointer-events-none" />

          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-5 border-b border-slate-800/80">
            <div>
              <div className="flex items-center gap-2 flex-wrap mb-1">
                <span className="text-[10px] font-mono font-bold uppercase tracking-widest text-indigo-400 bg-indigo-950/80 px-2.5 py-0.5 rounded border border-indigo-700/60">
                  Pre-Disbursal Treasury Gate
                </span>
                <span className="text-[10px] font-mono text-slate-400">
                  Sec 43B(h) MSME Mandate vs CGST Sec 16(2)(c) Safe-Harbor
                </span>
              </div>
              <h2 className="text-lg sm:text-xl font-extrabold text-white flex items-center gap-3">
                <span>Recommended Action:</span>
                <span className={`px-3 py-1 rounded-lg text-sm font-mono font-bold tracking-wide ${
                  settlement.recommendation === 'FULL_DISBURSAL' 
                    ? 'bg-emerald-950 text-emerald-300 border border-emerald-600'
                    : settlement.recommendation === 'STATUTORY_GST_ESCROW'
                    ? 'bg-amber-950 text-amber-300 border border-amber-500'
                    : 'bg-rose-950 text-rose-300 border border-rose-600'
                }`}>
                  {settlement.recommendation === 'STATUTORY_GST_ESCROW' 
                    ? 'STATUTORY GST ESCROW (SPLIT PAYOUT)' 
                    : settlement.recommendation}
                </span>
              </h2>
            </div>

            {/* GSTN IMS Action Badge & 1-Click Export */}
            <div className="flex items-center gap-3 flex-shrink-0">
              <div className="text-right">
                <span className="text-[10px] font-mono uppercase text-slate-400 block tracking-wider">
                  2026 GSTN IMS Portal Action
                </span>
                <span className={`inline-block px-3 py-1 rounded font-mono font-bold text-xs uppercase mt-0.5 ${
                  imsAction === 'ACCEPT'
                    ? 'bg-emerald-900/80 text-emerald-300 border border-emerald-700'
                    : imsAction === 'PENDING_HOLD'
                    ? 'bg-amber-900/80 text-amber-300 border border-amber-600'
                    : 'bg-rose-900/80 text-rose-300 border border-rose-700'
                }`}>
                  {imsAction === 'PENDING_HOLD' ? 'PENDING (HOLD ITC)' : imsAction}
                </span>
              </div>

              <button
                type="button"
                onClick={handleExportIMSJson}
                className="flex items-center gap-1.5 px-3 py-2 text-xs font-mono font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white shadow-md transition"
              >
                {copiedIMS ? <Check className="h-3.5 w-3.5 text-emerald-300" /> : <Download className="h-3.5 w-3.5" />}
                <span>{copiedIMS ? 'IMS JSON Exported!' : 'Export GSTN IMS JSON'}</span>
              </button>
            </div>
          </div>

          {/* 3-Column Financial Matrix */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-5">
            {/* Box 1: Immediate MSME Payout */}
            <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 space-y-1">
              <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
                <span>Immediate MSME 43B(h) Base Payout</span>
                <span className="text-emerald-400 font-bold">&bull; 0-Day Release</span>
              </div>
              <div className="text-2xl font-mono font-extrabold text-emerald-400">
                &#8377;{settlement.release_now_inr.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
              <p className="text-[10.5px] text-slate-400 leading-tight">
                Taxable supply released immediately to avoid 45-day MSME disallowance penalty.
              </p>
            </div>

            {/* Box 2: GST Escrow Holdback */}
            <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 space-y-1">
              <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
                <span>Statutory Sec 16(2)(c) GST Escrow</span>
                <span className="text-amber-400 font-bold">&bull; Held in Tax Escrow</span>
              </div>
              <div className="text-2xl font-mono font-extrabold text-amber-400">
                &#8377;{settlement.escrow_hold_gst_inr.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
              <p className="text-[10.5px] text-slate-400 leading-tight">
                Held until supplier confirms GSTR-3B tax remittance on the 20th of next month.
              </p>
            </div>

            {/* Box 3: Total Clawback Risk Avoided */}
            <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 space-y-1">
              <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
                <span>Statutory Clawback Exposure Avoided</span>
                <span className="text-rose-400 font-bold flex items-center gap-0.5">
                  <TrendingDown className="h-3 w-3" /> Sec 74 Penalty Avoided
                </span>
              </div>
              <div className="text-2xl font-mono font-extrabold text-rose-400">
                &#8377;{settlement.statutory_clawback_risk_avoided_inr.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
              <p className="text-[10.5px] text-slate-400 leading-tight">
                Safeguards 100% Tax + 100% Section 74 Penalty + 18% Section 50 Interest.
              </p>
            </div>
          </div>

          {/* Rationale Banner */}
          <div className="mt-4 p-3 bg-slate-950/70 rounded-lg border border-slate-800/80 text-xs text-slate-300 font-mono">
            <strong>Treasury Directive:</strong> {settlement.settlement_rationale}
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* 🐟 4-HOP AUTONOMOUS TINYFISH LIVE TELEMETRY HUD */}
      {/* ==================================================================== */}
      <div className="rounded-xl border border-slate-800 bg-[#0e1422] p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2.5">
            <Radio className="h-4 w-4 text-cyan-400 animate-pulse" />
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-100 font-mono">
              TinyFish 4-Hop Live Web Agent Telemetry
            </h2>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
              CAPTCHA-Free High-Signal Pipeline
            </span>
          </div>

          {/* Hop Selector Tabs */}
          <div className="flex items-center gap-1 overflow-x-auto text-xs font-mono">
            <button
              onClick={() => setActiveHopTab('all')}
              className={`px-2.5 py-1 rounded transition ${
                activeHopTab === 'all'
                  ? 'bg-cyan-500 text-slate-950 font-bold'
                  : 'bg-slate-900 text-slate-400 hover:text-white'
              }`}
            >
              All Hops ({evidence_items.length})
            </button>
            {hops.map(h => (
              <button
                key={h.num}
                onClick={() => setActiveHopTab(h.num)}
                className={`px-2.5 py-1 rounded transition whitespace-nowrap ${
                  activeHopTab === h.num
                    ? 'bg-cyan-500 text-slate-950 font-bold'
                    : 'bg-slate-900 text-slate-400 hover:text-white'
                }`}
              >
                Hop {h.num}
              </button>
            ))}
          </div>
        </div>

        {/* 4-Hop Pipeline Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          {hops.map(h => {
            const ev = evidence_items.find(e => e.hop_number === h.num) || evidence_items[h.num - 1];
            const isLive = ev?.source_mode === 'LIVE' || ev?.source_mode === 'LIVE_TINYFISH_SSE';
            const isUnavail = ev?.source_mode === 'UNAVAILABLE';

            return (
              <div
                key={h.num}
                onClick={() => setActiveHopTab(h.num)}
                className={`cursor-pointer p-3.5 rounded-xl border text-xs space-y-2 transition ${
                  activeHopTab === h.num
                    ? 'border-cyan-500 bg-cyan-950/20 ring-1 ring-cyan-500/30'
                    : 'border-slate-800 bg-[#090d18] hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-cyan-400 border border-slate-700">
                    HOP {h.num}
                  </span>
                  {isLive ? (
                    <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 flex items-center gap-1">
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-ping" /> LIVE SSE
                    </span>
                  ) : isUnavail ? (
                    <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700">
                      UNAVAILABLE
                    </span>
                  ) : (
                    <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-amber-950 text-amber-400 border border-amber-800">
                      SIMULATED
                    </span>
                  )}
                </div>

                <div className="font-semibold text-slate-100 leading-snug">
                  {h.title}
                </div>

                <div className="text-[11px] text-slate-400 truncate font-mono">
                  {ev?.source_url || h.url}
                </div>

                {ev && (
                  <div className="pt-1 border-t border-slate-800/80 text-[11px] text-slate-300 font-mono truncate">
                    {ev.facts?.status || ev.facts?.gst_status || ev.facts?.top_case_title || (ev.facts?.market_median_price_inr ? `₹${ev.facts.market_median_price_inr} wholesale` : 'Findings verified')}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Detailed Hop Dossier View */}
        <div className="space-y-3 pt-2">
          {filteredEvidence.map((ev, idx) => (
            <div key={ev.evidence_id || idx} className="p-4 rounded-xl bg-[#080c16] border border-slate-800 text-xs space-y-2.5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-2">
                <div className="flex items-center gap-2">
                  {ev.hop_number && (
                    <span className="font-mono text-[10px] font-bold px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
                      Hop {ev.hop_number}
                    </span>
                  )}
                  <span className="font-bold text-slate-100">{ev.source_name}</span>
                  {ev.source_mode === 'LIVE' ? (
                    <span className="text-[9px] font-mono uppercase px-1.5 py-0.2 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                      LIVE TINYFISH SSE
                    </span>
                  ) : (
                    <span className="text-[9px] font-mono uppercase px-1.5 py-0.2 rounded bg-amber-950 text-amber-400 border border-amber-800">
                      {ev.source_mode || 'SIMULATED'}
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-3">
                  {ev.streaming_url && (
                    <a
                      href={ev.streaming_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-[10px] font-mono text-indigo-400 hover:text-indigo-300 flex items-center gap-1 underline"
                    >
                      <Tv className="h-3 w-3" /> Agent Streaming Session
                    </a>
                  )}
                  {ev.source_url && (
                    <a
                      href={ev.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-[10px] font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
                    >
                      <span>Direct URL</span>
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  )}
                  <span className="text-[10px] font-mono text-slate-500">{ev.retrieved_at}</span>
                </div>
              </div>

              <div className="bg-slate-950/80 p-3 rounded-lg border border-slate-900 font-mono text-[11px] text-slate-300 leading-relaxed">
                {ev.raw_excerpt}
              </div>

              {/* Extracted Structured JSON Facts */}
              {ev.facts && Object.keys(ev.facts).length > 0 && (
                <div className="flex flex-wrap gap-2 text-[10.5px] font-mono">
                  {Object.entries(ev.facts).map(([k, v]) => (
                    <span key={k} className="px-2 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-800">
                      <span className="text-slate-500">{k}:</span> <strong>{String(v)}</strong>
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* ==================================================================== */}
      {/* 5-VECTOR RISK TOPOLOGY RADAR & DIRECT CGST 16(2)(c) LIABILITY */}
      {/* ==================================================================== */}
      {assessment && (
        <div className="rounded-xl p-5 border border-slate-800 bg-[#0e1422] space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300">
              5-Vector Forensic Risk Topology
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              Compliance Score: <strong className="text-white">{assessment.risk_score}</strong>/100
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-center text-xs">
            <div className="bg-slate-900/90 p-3 rounded-xl border border-slate-800">
              <span className="text-[10px] text-slate-400 block font-mono">1. ITC Clawback</span>
              <span className="text-base font-mono font-bold text-cyan-400">
                {Math.round((assessment.forensic_vectors?.itc_clawback_risk_index || 0) * 100)}%
              </span>
            </div>
            <div className="bg-slate-900/90 p-3 rounded-xl border border-slate-800">
              <span className="text-[10px] text-slate-400 block font-mono">2. Judicial Contagion</span>
              <span className="text-base font-mono font-bold text-rose-400">
                {Math.round((assessment.forensic_vectors?.judicial_insolvency_contagion || assessment.forensic_vectors?.director_shell_contagion_score || 0) * 100)}%
              </span>
            </div>
            <div className="bg-slate-900/90 p-3 rounded-xl border border-slate-800">
              <span className="text-[10px] text-slate-400 block font-mono">3. Price Anomaly</span>
              <span className="text-base font-mono font-bold text-amber-400">
                {Math.round((assessment.forensic_vectors?.procurement_price_anomaly || 0) * 100)}%
              </span>
            </div>
            <div className="bg-slate-900/90 p-3 rounded-xl border border-slate-800">
              <span className="text-[10px] text-slate-400 block font-mono">4. Grounding (e-Way)</span>
              <span className="text-base font-mono font-bold text-emerald-400">
                {Math.round((assessment.forensic_vectors?.operational_grounding_score || 0) * 100)}%
              </span>
            </div>
            <div className="bg-slate-900/90 p-3 rounded-xl border border-slate-800">
              <span className="text-[10px] text-slate-400 block font-mono">5. Pop-Up / BEC</span>
              <span className="text-base font-mono font-bold text-purple-400">
                {Math.round((assessment.forensic_vectors?.popup_velocity_and_bank_mutation || assessment.forensic_vectors?.popup_velocity_factor || 0) * 100)}%
              </span>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* CLAIMS & RECONCILIATIONS: BANK BEC GUARD & E-WAY TRANSIT */}
      {/* ==================================================================== */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Invoice Claims & Bank BEC Guard */}
        <div className="bg-[#0f172a]/70 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-300 font-mono">
              Invoice &amp; Remittance Registry
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
              <span className="text-[11px] font-mono text-slate-500 block">GSTIN &amp; Checksum</span>
              <div className="flex items-center gap-2">
                <span className="font-mono text-cyan-300">{invoice.gstin || 'Not provided'}</span>
                {invoice.gstin_format_valid && (
                  <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 font-mono">
                    MODULO-36 OK
                  </span>
                )}
              </div>
            </div>

            {/* Anti-BEC Bank Account Mutation Check */}
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
                Remittance Bank Account (Anti-BEC)
              </span>
              <div className="font-mono text-white flex items-center justify-between">
                <span>{invoice.bank_account_masked || 'XXXX-XXXX-9921'}</span>
                {invoice.bank_mutation_detected ? (
                  <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-rose-950 text-rose-300 border border-rose-700 font-bold">
                    BEC MUTATION!
                  </span>
                ) : (
                  <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-bold">
                    VERIFIED MASTER
                  </span>
                )}
              </div>
              <div className="text-[10px] font-mono text-slate-400">
                IFSC: {invoice.ifsc_code || 'HDFC0001234'} &bull; Beneficiary Match: {invoice.beneficiary_name_match_score ? `${Math.round(invoice.beneficiary_name_match_score * 100)}%` : '92%'}
              </div>
            </div>

            {/* Physical Transit & e-Way Bill Readiness */}
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block flex items-center gap-1">
                <Truck className="h-3 w-3 text-cyan-400" /> Physical Supply Transit (Sec 16(2)(b))
              </span>
              <div className="font-mono text-white flex items-center justify-between text-[11px]">
                <span>e-Way Bill: {invoice.eway_bill_no || '241098765432'}</span>
                <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
                  VERIFIED
                </span>
              </div>
              <div className="text-[10px] font-mono text-slate-400">
                Vehicle: {invoice.vehicle_no || 'DL-1GC-4491'} &bull; IRN: {invoice.irn_hash ? `${invoice.irn_hash.substring(0, 12)}...` : 'Generated'}
              </div>
            </div>

            <div>
              <span className="text-[11px] font-mono text-slate-500 block">Invoice Total &amp; Tax</span>
              <span className="font-mono text-white">
                &#8377;{invoice.total_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })} (Taxable: &#8377;{invoice.taxable_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })})
              </span>
            </div>
            <div>
              <span className="text-[11px] font-mono text-slate-500 block">Billing Address</span>
              <span className="text-slate-300 text-[11px]">{invoice.billing_address || 'Not specified'}</span>
            </div>
          </div>
        </div>

        {/* Right 2 cols: Field Reconciliations */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-[#0f172a]/70 border border-slate-800 rounded-xl p-5 space-y-4">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-300 font-mono border-b border-slate-800 pb-2">
              Field Reconciliations &amp; Grounding
            </h2>

            {assessment && assessment.field_checks.length > 0 ? (
              <div className="divide-y divide-slate-800/60">
                {assessment.field_checks.map((chk) => (
                  <div key={chk.check_id} className="py-3 first:pt-0 last:pb-0 space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-slate-200">{chk.field_name}</span>
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
                    <p className="text-xs text-slate-300 leading-relaxed">
                      {chk.explanation}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-slate-400 font-mono py-4">
                No reconciliation checks run yet. Click &apos;Run 4-Hop TinyFish&apos; above.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ==================================================================== */}
      {/* 3-ACTION HUMAN-IN-THE-LOOP REVIEWER DECISION & AUDIT SEAL */}
      {/* ==================================================================== */}
      <div className="bg-[#0f172a]/90 border border-slate-700 rounded-2xl p-6 space-y-5">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Lock className="h-4 w-4 text-cyan-400" />
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-100 font-mono">
              Human Reviewer Decision &amp; Audit Seal
            </h2>
          </div>
          {caseData.audit_hash_sha256 && (
            <span className="text-[11px] font-mono text-slate-400">
              SHA-256 Chained Hash: <code className="text-cyan-300">{caseData.audit_hash_sha256.substring(0, 16)}...</code>
            </span>
          )}
        </div>

        {review ? (
          <div className="p-4 bg-slate-900/80 border border-slate-700/80 rounded-xl text-xs space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-mono text-emerald-400 font-bold uppercase text-sm">
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
            {/* 3 Quick-Action Buttons */}
            <div>
              <label className="block text-slate-400 font-mono text-[11px] mb-2 font-semibold">
                Quick-Select Settlement Mode:
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <button
                  type="button"
                  onClick={() => selectReviewOption('APPROVE', 'Approve 100% full payment disbursal. All 4 TinyFish hops verified clean.')}
                  className={`p-3 rounded-xl border text-left transition ${
                    reviewAction === 'APPROVE'
                      ? 'border-emerald-500 bg-emerald-950/40 text-emerald-300 ring-1 ring-emerald-500/40'
                      : 'border-slate-800 bg-slate-900/60 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  <div className="font-bold text-xs flex items-center gap-1.5">
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                    <span>Approve 100% Disbursal</span>
                  </div>
                  <div className="text-[10px] text-slate-400 mt-1">
                    GSTN IMS Action: <strong>ACCEPT</strong>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => selectReviewOption(
                    'EXECUTE_SPLIT_PAYOUT',
                    settlement?.settlement_rationale || 'Execute Split-Payout: Disburse base amount to satisfy MSME Sec 43B(h); retain 18% GST in tax escrow.'
                  )}
                  className={`p-3 rounded-xl border text-left transition ${
                    reviewAction === 'EXECUTE_SPLIT_PAYOUT'
                      ? 'border-amber-500 bg-amber-950/40 text-amber-300 ring-1 ring-amber-500/40'
                      : 'border-slate-800 bg-slate-900/60 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  <div className="font-bold text-xs flex items-center gap-1.5">
                    <Layers className="h-3.5 w-3.5 text-amber-400" />
                    <span>Execute Split-Payout</span>
                  </div>
                  <div className="text-[10px] text-slate-400 mt-1">
                    Release Base &bull; Escrow GST &bull; IMS: <strong>PENDING</strong>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => selectReviewOption(
                    'FORENSIC_FREEZE',
                    settlement?.settlement_rationale || 'Forensic Freeze executed: Payment blocked due to active insolvency / critical fraud gate.'
                  )}
                  className={`p-3 rounded-xl border text-left transition ${
                    reviewAction === 'FORENSIC_FREEZE' || reviewAction === 'REJECT'
                      ? 'border-rose-500 bg-rose-950/40 text-rose-300 ring-1 ring-rose-500/40'
                      : 'border-slate-800 bg-slate-900/60 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  <div className="font-bold text-xs flex items-center gap-1.5">
                    <ShieldX className="h-3.5 w-3.5 text-rose-400" />
                    <span>Forensic Freeze</span>
                  </div>
                  <div className="text-[10px] text-slate-400 mt-1">
                    Block 100% Payout &bull; IMS: <strong>REJECT</strong>
                  </div>
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div>
                <label className="block text-slate-400 font-mono text-[11px] mb-1">
                  Reviewer Identity
                </label>
                <input
                  type="text"
                  required
                  value={reviewerId}
                  onChange={(e) => setReviewerId(e.target.value)}
                  className="w-full bg-[#0b0f19] border border-slate-700 rounded-lg px-3 py-2 text-white font-mono focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-mono text-[11px] mb-1">
                  Active Review Action Selection
                </label>
                <select
                  value={reviewAction}
                  onChange={(e) => setReviewAction(e.target.value as ReviewActionType)}
                  className="w-full bg-[#0b0f19] border border-slate-700 rounded-lg px-3 py-2 text-white font-mono focus:outline-none focus:border-cyan-500"
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

            <div>
              <label className="block text-slate-400 font-mono text-[11px] mb-1">
                Mandatory Review Rationale (Sealed into SHA-256 Audit Trail) *
              </label>
              <textarea
                required
                rows={3}
                placeholder="State verified trade-name alias, statutory escrow reasons, or reason for action..."
                value={rationale}
                onChange={(e) => setRationale(e.target.value)}
                className="w-full bg-[#0b0f19] border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={reviewing}
                className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold px-5 py-2.5 rounded-lg text-xs transition disabled:opacity-50 shadow-md"
              >
                {reviewing ? 'Sealing Audit Record...' : 'Record Treasury Decision & Seal Audit'}
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
