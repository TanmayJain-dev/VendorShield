'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  Shield,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  AlertCircle,
  ArrowRight,
  ArrowUpRight,
  CheckCircle2,
  XCircle,
  FileText,
  Search,
  Lock,
  ExternalLink,
  ChevronRight,
  Database,
  Globe,
  Building2,
  Layers,
  Sparkles,
  Info,
  Clock,
  Check,
  Cpu,
  FileCheck,
  Fingerprint,
  Scale,
  UserCheck,
  FileSearch,
  Activity,
  Workflow
} from 'lucide-react';
import { Hero3DScene } from '../components/Hero3DScene';

export default function HomePage() {
  const [activeStep, setActiveStep] = useState(1);
  const [activeSequenceStep, setActiveSequenceStep] = useState<'invoice' | 'evidence' | 'reconciliation' | 'review' | 'decision'>('reconciliation');
  const [selectedCaseTab, setSelectedCaseTab] = useState<'claims' | 'evidence' | 'reconciliation'>('reconciliation');

  return (
    <div className="w-full flex flex-col bg-background text-foreground transition-colors overflow-hidden">
      {/* =========================================================================
          HERO SECTION — "Know Your Vendor Before You Pay"
      ========================================================================= */}
      <section className="relative w-full pt-12 pb-20 sm:pt-20 sm:pb-28 border-b border-zinc-200/80 dark:border-zinc-800/80 bg-gradient-to-b from-zinc-50/50 via-background to-background dark:from-[#090e17]/80 dark:via-background dark:to-background">
        {/* Cinematic ambient background glow */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[350px] bg-teal-500/10 dark:bg-teal-500/15 rounded-full blur-3xl pointer-events-none -z-10" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
            {/* Left Content (Cols 1-7) */}
            <div className="lg:col-span-7 space-y-6 sm:space-y-8 text-left">
              {/* Trust Badge */}
              <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium bg-zinc-100 dark:bg-zinc-800/80 border border-zinc-200/80 dark:border-zinc-700/80 text-zinc-800 dark:text-zinc-200 shadow-sm animate-reveal-up">
                <span className="w-2 h-2 rounded-full bg-teal-500 animate-pulse" />
                <span className="font-semibold text-teal-700 dark:text-teal-400">VendorShield AI</span>
                <span className="text-zinc-400">&bull;</span>
                <span className="text-zinc-500 dark:text-zinc-400">B2B Vendor Due Diligence & ITC Sentinel</span>
              </div>

              {/* Main Headline */}
              <div className="space-y-3">
                <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 leading-[1.12]">
                  Know Your Vendor <br className="hidden sm:inline" />
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-700 via-teal-600 to-emerald-600 dark:from-teal-300 dark:via-teal-400 dark:to-emerald-400">
                    Before You Pay.
                  </span>
                </h1>
                <p className="text-base sm:text-lg text-zinc-600 dark:text-zinc-300 max-w-2xl leading-relaxed">
                  Turn invoice claims into evidence-backed vendor reviews before payment.
                </p>
              </div>

              {/* CTA Action Row */}
              <div className="flex flex-wrap items-center gap-3 pt-2">
                <Link
                  href="/queue"
                  className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-lg text-sm font-semibold text-white bg-teal-700 hover:bg-teal-600 dark:bg-teal-600 dark:hover:bg-teal-500 transition-all shadow-md hover:shadow-teal-500/20 active:scale-95"
                >
                  <span>Explore the Platform</span>
                  <ArrowRight className="h-4 w-4" />
                </Link>

                <a
                  href="#sequence"
                  className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-lg text-sm font-medium text-zinc-700 dark:text-zinc-300 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800/60 transition-colors shadow-subtle active:scale-95"
                >
                  <span>See How It Works</span>
                  <ChevronRight className="h-4 w-4 text-zinc-400" />
                </a>
              </div>

              {/* Restrained Trust Statement */}
              <div className="pt-4 border-t border-zinc-200/80 dark:border-zinc-800/80 flex flex-wrap items-center gap-y-2 gap-x-6 text-xs text-zinc-500 dark:text-zinc-400">
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                  <span className="font-medium text-zinc-700 dark:text-zinc-300">Evidence-grounded</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-teal-500" />
                  <span className="font-medium text-zinc-700 dark:text-zinc-300">Citation-checked</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-zinc-400 dark:bg-zinc-500" />
                  <span className="font-medium text-zinc-700 dark:text-zinc-300">Fail-closed</span>
                </div>
                <div className="flex items-center space-x-1.5 text-zinc-400">
                  <Lock className="h-3 w-3" />
                  <span>SHA-256 Audit Trail</span>
                </div>
              </div>
            </div>

            {/* Right 3D Visual Scene (Cols 8-12) */}
            <div className="lg:col-span-5 flex justify-center lg:justify-end">
              <Hero3DScene />
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          INTERACTIVE PRODUCT FLOW: INVOICE → EVIDENCE → RECONCILE → REVIEW → DECIDE
      ========================================================================= */}
      <section id="sequence" className="py-16 sm:py-20 border-b border-zinc-200/80 dark:border-zinc-800/80 bg-white dark:bg-[#0a0f18] scroll-mt-14">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="text-center max-w-3xl mx-auto space-y-2 mb-10">
            <span className="text-xs font-semibold uppercase tracking-wider text-teal-700 dark:text-teal-400">
              Interactive Execution Pipeline
            </span>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
              Visual Risk-Verification Sequence
            </h2>
            <p className="text-xs sm:text-sm text-zinc-500 dark:text-zinc-400">
              Follow how an incoming invoice is investigated across public web registries, reconciled, and surfaced for human payment release.
            </p>
          </div>

          {/* Interactive Step Navigator */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 sm:gap-3 p-1.5 rounded-xl bg-zinc-100 dark:bg-zinc-900/60 border border-zinc-200 dark:border-zinc-800 mb-6 text-xs">
            <button
              type="button"
              onClick={() => setActiveSequenceStep('invoice')}
              className={`p-3 rounded-lg font-medium transition-all text-left flex items-center justify-between ${
                activeSequenceStep === 'invoice'
                  ? 'bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 shadow-sm'
                  : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-300'
              }`}
            >
              <span className="truncate">1. INVOICE</span>
              <FileText className="h-3.5 w-3.5 text-zinc-400 shrink-0" />
            </button>

            <button
              type="button"
              onClick={() => setActiveSequenceStep('evidence')}
              className={`p-3 rounded-lg font-medium transition-all text-left flex items-center justify-between ${
                activeSequenceStep === 'evidence'
                  ? 'bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 shadow-sm'
                  : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-300'
              }`}
            >
              <span className="truncate">2. PUBLIC EVIDENCE</span>
              <Globe className="h-3.5 w-3.5 text-sky-500 shrink-0" />
            </button>

            <button
              type="button"
              onClick={() => setActiveSequenceStep('reconciliation')}
              className={`p-3 rounded-lg font-medium transition-all text-left flex items-center justify-between ${
                activeSequenceStep === 'reconciliation'
                  ? 'bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 shadow-sm'
                  : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-300'
              }`}
            >
              <span className="truncate">3. RECONCILIATION</span>
              <Cpu className="h-3.5 w-3.5 text-teal-500 shrink-0" />
            </button>

            <button
              type="button"
              onClick={() => setActiveSequenceStep('review')}
              className={`p-3 rounded-lg font-medium transition-all text-left flex items-center justify-between ${
                activeSequenceStep === 'review'
                  ? 'bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 shadow-sm'
                  : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-300'
              }`}
            >
              <span className="truncate">4. RISK REVIEW</span>
              <Scale className="h-3.5 w-3.5 text-amber-500 shrink-0" />
            </button>

            <button
              type="button"
              onClick={() => setActiveSequenceStep('decision')}
              className={`p-3 rounded-lg font-medium transition-all text-left flex items-center justify-between col-span-2 sm:col-span-1 ${
                activeSequenceStep === 'decision'
                  ? 'bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 shadow-sm'
                  : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-300'
              }`}
            >
              <span className="truncate">5. HUMAN DECISION</span>
              <UserCheck className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
            </button>
          </div>

          {/* Sequence Detail Showcase Card */}
          <div className="bg-zinc-50/70 dark:bg-[#0c121e] border border-zinc-200/90 dark:border-zinc-800/90 rounded-2xl p-6 sm:p-8 shadow-subtle transition-all">
            {activeSequenceStep === 'invoice' && (
              <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
                <div className="md:col-span-7 space-y-3">
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-zinc-200 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300">
                    STAGE 01 — INGESTION
                  </span>
                  <h3 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">
                    Extract Claims &amp; Validate Mathematical Format
                  </h3>
                  <p className="text-xs sm:text-sm text-zinc-600 dark:text-zinc-400 leading-relaxed">
                    The supplier PDF enters the pipeline. VendorShield extracts the declared supplier identity, invoice amount, remittance bank IFSC, and GSTIN. It immediately runs a Luhn-mod-36 checksum verification to ensure the 15-character GSTIN is mathematically authentic.
                  </p>
                  <div className="pt-2 flex items-center space-x-3 text-xs">
                    <span className="flex items-center space-x-1.5 text-emerald-600 dark:text-emerald-400 font-medium">
                      <CheckCircle2 className="h-4 w-4" />
                      <span>Format &amp; Checksum Validated</span>
                    </span>
                    <span className="text-zinc-300 dark:text-zinc-700">&bull;</span>
                    <span className="text-zinc-500 dark:text-zinc-400">Luhn Mod-36 Algorithm</span>
                  </div>
                </div>
                <div className="md:col-span-5 bg-white dark:bg-[#0f141f] p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 shadow-sm space-y-2 text-xs">
                  <div className="text-[10px] uppercase tracking-wider text-zinc-400 font-medium">Raw Extracted Claim</div>
                  <div className="font-mono text-zinc-900 dark:text-zinc-100 font-semibold">Apex Courier Pvt Ltd</div>
                  <div className="font-mono text-teal-600 dark:text-teal-400 text-[11px]">GSTIN: 07AAAAA0000A1Z4</div>
                  <div className="font-mono text-zinc-700 dark:text-zinc-300 tabular-nums">Amount: ₹4,82,500.00</div>
                </div>
              </div>
            )}

            {activeSequenceStep === 'evidence' && (
              <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
                <div className="md:col-span-7 space-y-3">
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-sky-100 dark:bg-sky-950/40 text-sky-700 dark:text-sky-300">
                    STAGE 02 — INVESTIGATION
                  </span>
                  <h3 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">
                    TinyFish Web Agent Gathers Authoritative Citations
                  </h3>
                  <p className="text-xs sm:text-sm text-zinc-600 dark:text-zinc-400 leading-relaxed">
                    TinyFish autonomously queries public-web registries: the GST portal public search, the Ministry of Corporate Affairs (MCA21), and the vendor&apos;s digital domain footprint. It extracts raw text citations, registration statuses, and source URLs.
                  </p>
                  <div className="pt-2 flex items-center space-x-3 text-xs">
                    <span className="flex items-center space-x-1.5 text-sky-600 dark:text-sky-400 font-medium">
                      <Globe className="h-4 w-4" />
                      <span>Public Sources Only (No CAPTCHA bypass)</span>
                    </span>
                  </div>
                </div>
                <div className="md:col-span-5 bg-white dark:bg-[#0f141f] p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 shadow-sm space-y-2 text-xs">
                  <div className="text-[10px] uppercase tracking-wider text-zinc-400 font-medium">Retrieved Public Citations</div>
                  <div className="p-2 rounded bg-zinc-50 dark:bg-zinc-900 text-[11px] font-mono text-zinc-700 dark:text-zinc-300">
                    GST Status: ACTIVE &bull; Legal: Apex Global Logistics Pvt Ltd
                  </div>
                  <div className="p-2 rounded bg-zinc-50 dark:bg-zinc-900 text-[11px] font-mono text-zinc-700 dark:text-zinc-300">
                    MCA21: CIN U64120DL2018PTC334912 &bull; Inc. 2018
                  </div>
                </div>
              </div>
            )}

            {activeSequenceStep === 'reconciliation' && (
              <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
                <div className="md:col-span-7 space-y-3">
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-teal-100 dark:bg-teal-950/40 text-teal-700 dark:text-teal-300">
                    STAGE 03 — RECONCILIATION
                  </span>
                  <h3 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">
                    Deterministic Cross-Checking Rules
                  </h3>
                  <p className="text-xs sm:text-sm text-zinc-600 dark:text-zinc-400 leading-relaxed">
                    The deterministic rules engine evaluates the invoice claims against the evidence items. It verifies whether the legal name matches the trade alias, checks filing regularity, assesses physical presence, and determines if bank account details have been altered.
                  </p>
                  <div className="pt-2 flex items-center space-x-3 text-xs">
                    <span className="flex items-center space-x-1.5 text-emerald-600 dark:text-emerald-400 font-medium">
                      <CheckCircle2 className="h-4 w-4" />
                      <span>Zero Neural Hallucinations</span>
                    </span>
                    <span className="text-zinc-300 dark:text-zinc-700">&bull;</span>
                    <span className="text-zinc-500 dark:text-zinc-400">Explicit Penalty Logic</span>
                  </div>
                </div>
                <div className="md:col-span-5 bg-white dark:bg-[#0f141f] p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 shadow-sm space-y-2 text-xs">
                  <div className="text-[10px] uppercase tracking-wider text-zinc-400 font-medium">Reconciliation Results</div>
                  <div className="flex items-center justify-between p-2 rounded bg-emerald-50 dark:bg-emerald-950/30 text-emerald-800 dark:text-emerald-300 text-[11px]">
                    <span>GSTIN Active Status</span>
                    <span className="font-semibold">MATCH (0 pts)</span>
                  </div>
                  <div className="flex items-center justify-between p-2 rounded bg-amber-50 dark:bg-amber-950/30 text-amber-800 dark:text-amber-300 text-[11px]">
                    <span>Supplier Legal vs Trade Name</span>
                    <span className="font-semibold">VARIATION (+20 pts)</span>
                  </div>
                </div>
              </div>
            )}

            {activeSequenceStep === 'review' && (
              <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
                <div className="md:col-span-7 space-y-3">
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-100 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300">
                    STAGE 04 — RISK REVIEW
                  </span>
                  <h3 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">
                    Automated Risk Scoring &amp; SHA-256 Digest
                  </h3>
                  <p className="text-xs sm:text-sm text-zinc-600 dark:text-zinc-400 leading-relaxed">
                    Based on total penalty points, VendorShield generates an overall recommendation: <strong>Pass (Green)</strong>, <strong>Manual Review (Amber)</strong>, or <strong>Block (Red)</strong>. An immutable SHA-256 cryptographic digest locks the dossier for regulatory audit compliance.
                  </p>
                  <div className="pt-2 flex items-center space-x-3 text-xs">
                    <span className="flex items-center space-x-1.5 text-zinc-600 dark:text-zinc-400 font-mono">
                      <Lock className="h-4 w-4 text-teal-600" />
                      <span>SHA-256 Tamper-Evident Digest</span>
                    </span>
                  </div>
                </div>
                <div className="md:col-span-5 bg-white dark:bg-[#0f141f] p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 shadow-sm space-y-2 text-xs">
                  <div className="text-[10px] uppercase tracking-wider text-zinc-400 font-medium">Outcome Recommendation</div>
                  <div className="p-3 rounded-lg border border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 flex items-center justify-between">
                    <span className="font-bold">MANUAL REVIEW</span>
                    <span className="font-mono font-bold">Score: 48/100</span>
                  </div>
                  <p className="text-[11px] text-zinc-500">First invoice with altered remittance details. Dual review recommended.</p>
                </div>
              </div>
            )}

            {activeSequenceStep === 'decision' && (
              <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
                <div className="md:col-span-7 space-y-3">
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-100 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300">
                    STAGE 05 — HUMAN DECISION
                  </span>
                  <h3 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">
                    Human-in-the-Loop Governance Sign-Off
                  </h3>
                  <p className="text-xs sm:text-sm text-zinc-600 dark:text-zinc-400 leading-relaxed">
                    VendorShield provides decision support, not autonomous capital release. An accounts payable controller reviews the discrepancy notes, attaches formal rationale, and authorizes or blocks the disbursement before funds move.
                  </p>
                  <div className="pt-2 flex items-center space-x-3 text-xs">
                    <Link
                      href="/queue"
                      className="inline-flex items-center space-x-1 text-teal-600 dark:text-teal-400 font-semibold hover:underline"
                    >
                      <span>Open Cases Queue to inspect real workflow &rarr;</span>
                    </Link>
                  </div>
                </div>
                <div className="md:col-span-5 bg-white dark:bg-[#0f141f] p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 shadow-sm space-y-2 text-xs">
                  <div className="text-[10px] uppercase tracking-wider text-zinc-400 font-medium">Controller Authorization</div>
                  <div className="p-2 rounded bg-emerald-50 dark:bg-emerald-950/30 text-emerald-800 dark:text-emerald-300 text-[11px] flex items-center space-x-2">
                    <Check className="h-4 w-4 shrink-0 text-emerald-600" />
                    <span>Approved with Exception by Controller Prachi</span>
                  </div>
                  <div className="text-[10px] text-zinc-400 font-mono">Timestamp: 2026-10-24T16:45:00Z</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION A — THE PROBLEM: "Invoices Are Digital. Vendor Checks Are Still Manual."
      ========================================================================= */}
      <section className="py-20 sm:py-28 border-b border-zinc-200/80 dark:border-zinc-800/80 bg-zinc-50/40 dark:bg-[#070b12]/40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="max-w-3xl space-y-3 mb-14">
            <span className="text-xs font-semibold uppercase tracking-wider text-teal-700 dark:text-teal-400">
              The Accounts Payable Blindspot
            </span>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
              Invoices Are Digital. Vendor Checks Are Still Manual.
            </h2>
            <p className="text-sm sm:text-base text-zinc-600 dark:text-zinc-400">
              Blind trust in paper claims exposes modern finance teams to circular invoicing schemes, ghost entities, and Input Tax Credit (ITC) clawbacks by tax authorities.
            </p>
          </div>

          {/* Asymmetric 3-Problem Narrative Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Problem 1 */}
            <div className="bg-white dark:bg-[#0f141f] border border-zinc-200/90 dark:border-zinc-800/90 rounded-xl p-6 shadow-subtle flex flex-col justify-between relative group hover:border-zinc-300 dark:hover:border-zinc-700 transition-colors">
              <div className="space-y-4">
                <div className="w-10 h-10 rounded-lg bg-teal-50 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-800/60 text-teal-700 dark:text-teal-400 flex items-center justify-center font-mono font-bold text-sm">
                  01
                </div>
                <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                  Scattered Sources
                </h3>
                <p className="text-xs sm:text-sm text-zinc-600 dark:text-zinc-400 leading-relaxed">
                  GST records, MCA21 corporate filings, and public company websites contain separate, siloed pieces of identity data. No single registry verifies every claim on an invoice document.
                </p>
              </div>
              <div className="mt-6 pt-4 border-t border-zinc-100 dark:border-zinc-800/80 text-[11px] text-zinc-400">
                Requires manual portal switching &amp; query fragmentation
              </div>
            </div>

            {/* Problem 2 */}
            <div className="bg-white dark:bg-[#0f141f] border border-zinc-200/90 dark:border-zinc-800/90 rounded-xl p-6 shadow-subtle flex flex-col justify-between relative group hover:border-zinc-300 dark:hover:border-zinc-700 transition-colors">
              <div className="space-y-4">
                <div className="w-10 h-10 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/60 text-amber-700 dark:text-amber-400 flex items-center justify-center font-mono font-bold text-sm">
                  02
                </div>
                <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                  Manual Cross-Checking
                </h3>
                <p className="text-xs sm:text-sm text-zinc-600 dark:text-zinc-400 leading-relaxed">
                  Finance teams must manually cross-reference supplier trade aliases, legal names, GSTIN checksums, and banking information across tabs under tight payment cycles.
                </p>
              </div>
              <div className="mt-6 pt-4 border-t border-zinc-100 dark:border-zinc-800/80 text-[11px] text-zinc-400">
                Cognitive overload causes subtle trade-alias mismatches to slip through
              </div>
            </div>

            {/* Problem 3 */}
            <div className="bg-white dark:bg-[#0f141f] border border-zinc-200/90 dark:border-zinc-800/90 rounded-xl p-6 shadow-subtle flex flex-col justify-between relative group hover:border-zinc-300 dark:hover:border-zinc-700 transition-colors">
              <div className="space-y-4">
                <div className="w-10 h-10 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800/60 text-rose-700 dark:text-rose-400 flex items-center justify-center font-mono font-bold text-sm">
                  03
                </div>
                <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                  Missing Audit Trails
                </h3>
                <p className="text-xs sm:text-sm text-zinc-600 dark:text-zinc-400 leading-relaxed">
                  Informal Slack approvals or paper printouts fail to reproduce what public evidence was verified before funds moved, leaving statutory auditors with zero cryptographic proof.
                </p>
              </div>
              <div className="mt-6 pt-4 border-t border-zinc-100 dark:border-zinc-800/80 text-[11px] text-zinc-400">
                Zero tamper-evident proof during retrospective tax audits
              </div>
            </div>
          </div>

          {/* High-Risk Scenarios Callout & Assumption Disclaimers */}
          <div className="mt-8 grid grid-cols-1 md:grid-cols-12 gap-6 items-stretch">
            {/* Critical Exposure Callout */}
            <div className="md:col-span-8 bg-zinc-900 dark:bg-[#0c121e] text-white rounded-xl p-6 border border-zinc-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="space-y-1.5">
                <div className="flex items-center space-x-2 text-teal-400 text-xs font-semibold uppercase tracking-wider">
                  <AlertTriangle className="h-4 w-4" />
                  <span>Highest Vulnerability Windows</span>
                </div>
                <p className="text-sm text-zinc-300">
                  The greatest fraud risk occurs in two specific events: <strong>First-Time Vendors</strong> without payment history, and unexpected <strong>Changes to Bank Account Details</strong>.
                </p>
              </div>
              <Link
                href="/upload"
                className="shrink-0 px-4 py-2 rounded-md bg-teal-600 hover:bg-teal-500 text-white text-xs font-medium transition-colors"
              >
                Intake First-Time Vendor
              </Link>
            </div>

            {/* Intellectual Honesty Assumption Box */}
            <div className="md:col-span-4 bg-white dark:bg-[#0f141f] border border-zinc-200/90 dark:border-zinc-800/90 rounded-xl p-5 shadow-subtle flex flex-col justify-center text-xs text-zinc-500 dark:text-zinc-400 space-y-1.5">
              <div className="flex items-center space-x-1.5 font-medium text-zinc-700 dark:text-zinc-300">
                <Info className="h-3.5 w-3.5 text-teal-600 dark:text-teal-400" />
                <span>Presentation Assumption Disclosure</span>
              </div>
              <p className="text-[11px] leading-relaxed">
                Presentation estimates (e.g., 35–45 minutes manual cross-check per vendor, potential ITC liability exposure) represent modeled project baseline assumptions, not audited operational outcomes.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION B — HOW VENDORSHIELD WORKS: 5-STEP WORKFLOW
      ========================================================================= */}
      <section id="workflow" className="py-20 sm:py-28 border-b border-zinc-200/80 dark:border-zinc-800/80 scroll-mt-14">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="max-w-3xl space-y-3 mb-14">
            <span className="text-xs font-semibold uppercase tracking-wider text-teal-700 dark:text-teal-400">
              Governed Verification Pipeline
            </span>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
              From Invoice to Evidence. From Evidence to Review.
            </h2>
            <p className="text-sm sm:text-base text-zinc-600 dark:text-zinc-400">
              A structured, deterministic 5-step pipeline that reconciles invoice claims against external public registries before money moves.
            </p>
          </div>

          {/* 5-Step Connected Pipeline */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 relative">
            {/* Step 1: Ingest */}
            <div
              onClick={() => setActiveStep(1)}
              className={`cursor-pointer rounded-xl p-5 border transition-all text-left space-y-3 ${
                activeStep === 1
                  ? 'bg-white dark:bg-[#0f141f] border-teal-600 dark:border-teal-500 shadow-lg ring-1 ring-teal-500/20'
                  : 'bg-zinc-50/50 dark:bg-zinc-900/30 border-zinc-200/80 dark:border-zinc-800/80 hover:bg-white dark:hover:bg-[#0f141f]'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-teal-700 dark:text-teal-400">01</span>
                <span className="text-[10px] uppercase font-semibold tracking-wider text-zinc-400">INTAKE</span>
              </div>
              <h3 className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">
                INGEST — Invoice PDF
              </h3>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
                Parse PDF invoice claims and validate Indian GSTIN format and Luhn-mod-36 checksum mathematical validity.
              </p>
            </div>

            {/* Step 2: Investigate */}
            <div
              onClick={() => setActiveStep(2)}
              className={`cursor-pointer rounded-xl p-5 border transition-all text-left space-y-3 ${
                activeStep === 2
                  ? 'bg-white dark:bg-[#0f141f] border-teal-600 dark:border-teal-500 shadow-lg ring-1 ring-teal-500/20'
                  : 'bg-zinc-50/50 dark:bg-zinc-900/30 border-zinc-200/80 dark:border-zinc-800/80 hover:bg-white dark:hover:bg-[#0f141f]'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-teal-700 dark:text-teal-400">02</span>
                <span className="text-[10px] uppercase font-semibold tracking-wider text-zinc-400">RESEARCH</span>
              </div>
              <h3 className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">
                INVESTIGATE — Public-Web
              </h3>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
                Deploy TinyFish browser agent to navigate accessible public web sources, corporate registries, and live portals for raw evidence.
              </p>
            </div>

            {/* Step 3: Reconcile */}
            <div
              onClick={() => setActiveStep(3)}
              className={`cursor-pointer rounded-xl p-5 border transition-all text-left space-y-3 ${
                activeStep === 3
                  ? 'bg-white dark:bg-[#0f141f] border-teal-600 dark:border-teal-500 shadow-lg ring-1 ring-teal-500/20'
                  : 'bg-zinc-50/50 dark:bg-zinc-900/30 border-zinc-200/80 dark:border-zinc-800/80 hover:bg-white dark:hover:bg-[#0f141f]'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-teal-700 dark:text-teal-400">03</span>
                <span className="text-[10px] uppercase font-semibold tracking-wider text-zinc-400">RULES</span>
              </div>
              <h3 className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">
                RECONCILE — Rule Checks
              </h3>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
                Compare invoice claims against collected evidence using strict deterministic rules (name match, active status, filing history).
              </p>
            </div>

            {/* Step 4: Brief */}
            <div
              onClick={() => setActiveStep(4)}
              className={`cursor-pointer rounded-xl p-5 border transition-all text-left space-y-3 ${
                activeStep === 4
                  ? 'bg-white dark:bg-[#0f141f] border-teal-600 dark:border-teal-500 shadow-lg ring-1 ring-teal-500/20'
                  : 'bg-zinc-50/50 dark:bg-zinc-900/30 border-zinc-200/80 dark:border-zinc-800/80 hover:bg-white dark:hover:bg-[#0f141f]'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-teal-700 dark:text-teal-400">04</span>
                <span className="text-[10px] uppercase font-semibold tracking-wider text-zinc-400">DOSSIER</span>
              </div>
              <h3 className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">
                BRIEF — Source Summary
              </h3>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
                Produce an evidence-grounded summary with verbatim citations, source URLs, and cryptographic SHA-256 audit fingerprint.
              </p>
            </div>

            {/* Step 5: Decide */}
            <div
              onClick={() => setActiveStep(5)}
              className={`cursor-pointer rounded-xl p-5 border transition-all text-left space-y-3 ${
                activeStep === 5
                  ? 'bg-white dark:bg-[#0f141f] border-teal-600 dark:border-teal-500 shadow-lg ring-1 ring-teal-500/20'
                  : 'bg-zinc-50/50 dark:bg-zinc-900/30 border-zinc-200/80 dark:border-zinc-800/80 hover:bg-white dark:hover:bg-[#0f141f]'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-teal-700 dark:text-teal-400">05</span>
                <span className="text-[10px] uppercase font-semibold tracking-wider text-zinc-400">HUMAN</span>
              </div>
              <h3 className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">
                DECIDE — Human Sign-off
              </h3>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
                Present Pass, Review, or Block recommendation with clear evidence rationales for human finance controller authorization.
              </p>
            </div>
          </div>

          {/* Explicit Honest Scope Disclaimer */}
          <div className="mt-8 p-4 rounded-lg bg-zinc-100/60 dark:bg-zinc-900/40 border border-zinc-200/70 dark:border-zinc-800/70 flex items-start space-x-3 text-xs text-zinc-500 dark:text-zinc-400">
            <Info className="h-4 w-4 text-zinc-400 shrink-0 mt-0.5" />
            <span>
              <strong>Scope Notice:</strong> VendorShield does not claim that every public registry is always accessible, that every third-party website is authentic, or that every supplier can be verified autonomously. Where evidence is incomplete or gated, the pipeline fails closed to <strong>Manual Review</strong>.
            </span>
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION C — PRODUCT PREVIEW: "One Invoice. One Reviewable Dossier."
      ========================================================================= */}
      <section className="py-20 sm:py-28 border-b border-zinc-200/80 dark:border-zinc-800/80 bg-zinc-50/40 dark:bg-[#070b12]/40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 gap-6">
            <div className="max-w-2xl space-y-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-teal-700 dark:text-teal-400">
                Decision Support Interface
              </span>
              <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
                One Invoice. One Reviewable Dossier.
              </h2>
              <p className="text-sm sm:text-base text-zinc-600 dark:text-zinc-400">
                Inspect how invoice claims, public registry findings, and reconciliation checks merge into an auditable pre-payment briefing.
              </p>
            </div>

            <div className="flex items-center space-x-3 shrink-0">
              <Link
                href="/cases/case_inv_2026_8841"
                className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg text-xs font-medium text-teal-700 dark:text-teal-300 bg-teal-50 dark:bg-teal-950/30 border border-teal-200 dark:border-teal-800 hover:bg-teal-100 transition-colors"
              >
                <span>Open Live Dossier</span>
                <ArrowUpRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </div>

          {/* Simulated Benchmark Dossier Card */}
          <div className="bg-white dark:bg-[#0f141f] border border-zinc-200/90 dark:border-zinc-800/90 rounded-2xl shadow-xl overflow-hidden">
            {/* Dossier Header Bar */}
            <div className="p-4 sm:p-6 border-b border-zinc-200/80 dark:border-zinc-800/80 bg-zinc-50/60 dark:bg-zinc-900/40 flex flex-wrap items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="font-mono text-sm font-bold text-zinc-900 dark:text-zinc-100">
                    INV-2026-8841
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-200 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300">
                    ILLUSTRATIVE EXAMPLE (DEMO DATA)
                  </span>
                </div>
                <div className="text-xs text-zinc-500 dark:text-zinc-400">
                  Apex Courier Pvt Ltd &bull; Courier &amp; Freight Logistics
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <div className="text-right">
                  <div className="text-[11px] uppercase tracking-wider text-zinc-400 font-medium">
                    Invoice Amount
                  </div>
                  <div className="font-mono font-bold text-base sm:text-lg text-zinc-900 dark:text-zinc-100 tabular-nums">
                    ₹4,82,500.00
                  </div>
                </div>

                <div className="h-8 w-px bg-zinc-200 dark:bg-zinc-800" />

                <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/60 text-amber-700 dark:text-amber-400 text-xs font-semibold">
                  <AlertTriangle className="h-4 w-4" />
                  <span>MANUAL REVIEW (Score: 48)</span>
                </div>
              </div>
            </div>

            {/* Dossier Interactive Tabs */}
            <div className="flex border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50/30 dark:bg-zinc-900/20 px-6 text-xs font-medium">
              <button
                type="button"
                onClick={() => setSelectedCaseTab('reconciliation')}
                className={`py-3 px-4 border-b-2 transition-colors ${
                  selectedCaseTab === 'reconciliation'
                    ? 'border-teal-600 text-teal-700 dark:text-teal-400 font-semibold'
                    : 'border-transparent text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-300'
                }`}
              >
                Reconciliation Matrix (4 Checks)
              </button>
              <button
                type="button"
                onClick={() => setSelectedCaseTab('claims')}
                className={`py-3 px-4 border-b-2 transition-colors ${
                  selectedCaseTab === 'claims'
                    ? 'border-teal-600 text-teal-700 dark:text-teal-400 font-semibold'
                    : 'border-transparent text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-300'
                }`}
              >
                Extracted Invoice Claims
              </button>
              <button
                type="button"
                onClick={() => setSelectedCaseTab('evidence')}
                className={`py-3 px-4 border-b-2 transition-colors ${
                  selectedCaseTab === 'evidence'
                    ? 'border-teal-600 text-teal-700 dark:text-teal-400 font-semibold'
                    : 'border-transparent text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-300'
                }`}
              >
                Public Evidence Log
              </button>
            </div>

            {/* Dossier Content Area */}
            <div className="p-6">
              {selectedCaseTab === 'reconciliation' && (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Check 1 */}
                    <div className="p-3.5 rounded-lg border border-emerald-200/80 dark:border-emerald-900/50 bg-emerald-50/20 dark:bg-emerald-950/10 flex items-start space-x-3">
                      <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                      <div>
                        <div className="text-xs font-semibold text-zinc-900 dark:text-zinc-100">
                          GSTIN Checksum &amp; Status Validation
                        </div>
                        <div className="text-[11px] text-zinc-600 dark:text-zinc-400 mt-0.5">
                          GSTIN <code className="font-mono">07AAAAA0000A1Z4</code> validated against Luhn checksum algorithm. Status: <strong>ACTIVE</strong>.
                        </div>
                      </div>
                    </div>

                    {/* Check 2 */}
                    <div className="p-3.5 rounded-lg border border-amber-200/80 dark:border-amber-900/50 bg-amber-50/20 dark:bg-amber-950/10 flex items-start space-x-3">
                      <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
                      <div>
                        <div className="text-xs font-semibold text-zinc-900 dark:text-zinc-100">
                          Supplier Entity Name Concordance
                        </div>
                        <div className="text-[11px] text-zinc-600 dark:text-zinc-400 mt-0.5">
                          Invoice displays trade name &ldquo;Apex Courier&rdquo;. Registered MCA legal entity is &ldquo;Apex Global Logistics Pvt Ltd&rdquo;.
                        </div>
                      </div>
                    </div>

                    {/* Check 3 */}
                    <div className="p-3.5 rounded-lg border border-emerald-200/80 dark:border-emerald-900/50 bg-emerald-50/20 dark:bg-emerald-950/10 flex items-start space-x-3">
                      <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                      <div>
                        <div className="text-xs font-semibold text-zinc-900 dark:text-zinc-100">
                          Domain &amp; Web Presence Corroboration
                        </div>
                        <div className="text-[11px] text-zinc-600 dark:text-zinc-400 mt-0.5">
                          Domain age 6.2 years. Contact address matches GST Principal Place of Business in New Delhi.
                        </div>
                      </div>
                    </div>

                    {/* Check 4 */}
                    <div className="p-3.5 rounded-lg border border-amber-200/80 dark:border-amber-900/50 bg-amber-50/20 dark:bg-amber-950/10 flex items-start space-x-3">
                      <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
                      <div>
                        <div className="text-xs font-semibold text-zinc-900 dark:text-zinc-100">
                          Bank Details Verification Requirement
                        </div>
                        <div className="text-[11px] text-zinc-600 dark:text-zinc-400 mt-0.5">
                          First invoice with modified beneficiary account. Penny-drop verification flagged for AP supervisor sign-off.
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="p-3.5 rounded-lg bg-zinc-50 dark:bg-zinc-900/50 border border-zinc-200 dark:border-zinc-800 flex items-center justify-between text-xs">
                    <div className="flex items-center space-x-2 text-zinc-600 dark:text-zinc-400">
                      <Lock className="h-3.5 w-3.5 text-zinc-400" />
                      <span>Audit Fingerprint:</span>
                      <code className="font-mono text-zinc-800 dark:text-zinc-200">
                        e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
                      </code>
                    </div>
                    <span className="text-[11px] text-emerald-600 dark:text-emerald-400 font-medium">
                      Tamper-Evident SHA-256
                    </span>
                  </div>
                </div>
              )}

              {selectedCaseTab === 'claims' && (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
                  <div className="p-3 rounded-lg border border-zinc-200 dark:border-zinc-800">
                    <span className="text-zinc-400 block text-[10px]">SUPPLIER CLAIM</span>
                    <span className="font-medium text-zinc-900 dark:text-zinc-100">Apex Courier</span>
                  </div>
                  <div className="p-3 rounded-lg border border-zinc-200 dark:border-zinc-800">
                    <span className="text-zinc-400 block text-[10px]">GSTIN CLAIM</span>
                    <span className="font-mono text-zinc-900 dark:text-zinc-100">07AAAAA0000A1Z4</span>
                  </div>
                  <div className="p-3 rounded-lg border border-zinc-200 dark:border-zinc-800">
                    <span className="text-zinc-400 block text-[10px]">TOTAL PAYABLE</span>
                    <span className="font-mono text-zinc-900 dark:text-zinc-100">₹4,82,500.00</span>
                  </div>
                  <div className="p-3 rounded-lg border border-zinc-200 dark:border-zinc-800">
                    <span className="text-zinc-400 block text-[10px]">INPUT TAX CREDIT</span>
                    <span className="font-mono text-teal-600 dark:text-teal-400">₹73,602.00 (18% IGST)</span>
                  </div>
                </div>
              )}

              {selectedCaseTab === 'evidence' && (
                <div className="space-y-2 text-xs">
                  <div className="p-3 rounded-lg bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-200 dark:border-zinc-800 flex items-center justify-between">
                    <div>
                      <span className="font-medium text-zinc-900 dark:text-zinc-100">GST Portal Public Search</span>
                      <span className="text-zinc-400 block text-[11px]">https://services.gst.gov.in/services/searchtpbypan</span>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 font-medium">HTTP 200 OK</span>
                  </div>
                  <div className="p-3 rounded-lg bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-200 dark:border-zinc-800 flex items-center justify-between">
                    <div>
                      <span className="font-medium text-zinc-900 dark:text-zinc-100">MCA21 Master Data Verification</span>
                      <span className="text-zinc-400 block text-[11px]">https://www.mca.gov.in/mcafoportal/viewCompanyMasterData.do</span>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 font-medium">CIN Match</span>
                  </div>
                </div>
              )}
            </div>

            {/* Card Footer */}
            <div className="px-6 py-3 border-t border-zinc-200/80 dark:border-zinc-800/80 bg-zinc-50/50 dark:bg-zinc-900/30 flex items-center justify-between text-xs text-zinc-500">
              <span>* Illustrative benchmark case from project presentation (simulated for evaluation).</span>
              <Link href="/queue" className="text-teal-600 dark:text-teal-400 hover:underline font-medium">
                View in Platform Queue &rarr;
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION D — THE INTEGRATION CONCEPT: "TinyFish Browses. VendorShield Decides."
      ========================================================================= */}
      <section id="architecture" className="py-20 sm:py-28 border-b border-zinc-200/80 dark:border-zinc-800/80 scroll-mt-14">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="max-w-3xl space-y-3 mb-14">
            <span className="text-xs font-semibold uppercase tracking-wider text-teal-700 dark:text-teal-400">
              System Architecture &amp; Separation of Concerns
            </span>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
              TinyFish Browses. VendorShield Decides.
            </h2>
            <p className="text-sm sm:text-base text-zinc-600 dark:text-zinc-400">
              Clear technical boundaries ensure autonomous web collection never bypasses deterministic financial rules.
            </p>
          </div>

          {/* Architectural Comparison Diagram */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            {/* Left: TinyFish Web Agent Boundary */}
            <div className="lg:col-span-5 bg-white dark:bg-[#0f141f] border border-sky-200/80 dark:border-sky-900/50 rounded-2xl p-6 shadow-subtle space-y-5">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-sky-50 dark:bg-sky-950/40 text-sky-600 dark:text-sky-400 flex items-center justify-center">
                  <Globe className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="font-bold text-zinc-900 dark:text-zinc-100 text-base">
                    TinyFish Web Agent
                  </h3>
                  <span className="text-xs text-sky-600 dark:text-sky-400 font-medium">
                    Autonomous Public Web Collector
                  </span>
                </div>
              </div>

              <div className="space-y-3 text-xs text-zinc-600 dark:text-zinc-400">
                <div className="flex items-start space-x-2">
                  <Check className="h-3.5 w-3.5 text-sky-600 dark:text-sky-400 shrink-0 mt-0.5" />
                  <span>Navigates accessible public portals, registries, and vendor domains.</span>
                </div>
                <div className="flex items-start space-x-2">
                  <Check className="h-3.5 w-3.5 text-sky-600 dark:text-sky-400 shrink-0 mt-0.5" />
                  <span>Extracts structured text snippets, filing tables, and source URLs.</span>
                </div>
                <div className="flex items-start space-x-2">
                  <Check className="h-3.5 w-3.5 text-sky-600 dark:text-sky-400 shrink-0 mt-0.5" />
                  <span>Operates strictly on public information — <strong>no CAPTCHA or login bypass</strong>.</span>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-sky-50/50 dark:bg-sky-950/20 text-[11px] text-sky-700 dark:text-sky-300 border border-sky-100 dark:border-sky-900/40">
                <strong>Safety Boundary:</strong> Untrusted web content collected by TinyFish is treated as untrusted data, never as executable LLM instructions.
              </div>
            </div>

            {/* Middle: Data Hand-off Conduit */}
            <div className="lg:col-span-2 flex flex-col items-center justify-center space-y-2 text-center">
              <div className="w-10 h-10 rounded-full bg-teal-50 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-800 text-teal-600 dark:text-teal-400 flex items-center justify-center">
                <ArrowRight className="h-5 w-5 hidden lg:block" />
                <ArrowRight className="h-5 w-5 rotate-90 lg:hidden" />
              </div>
              <span className="text-[10px] font-mono font-medium uppercase tracking-wider text-zinc-400">
                Structured Evidence Payload
              </span>
            </div>

            {/* Right: VendorShield Deterministic Sentinel Boundary */}
            <div className="lg:col-span-5 bg-white dark:bg-[#0f141f] border border-teal-200/80 dark:border-teal-900/50 rounded-2xl p-6 shadow-subtle space-y-5">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-teal-50 dark:bg-teal-950/40 text-teal-600 dark:text-teal-400 flex items-center justify-center">
                  <Shield className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="font-bold text-zinc-900 dark:text-zinc-100 text-base">
                    VendorShield Sentinel
                  </h3>
                  <span className="text-xs text-teal-600 dark:text-teal-400 font-medium">
                    Deterministic Risk &amp; Audit Engine
                  </span>
                </div>
              </div>

              <div className="space-y-3 text-xs text-zinc-600 dark:text-zinc-400">
                <div className="flex items-start space-x-2">
                  <Check className="h-3.5 w-3.5 text-teal-600 dark:text-teal-400 shrink-0 mt-0.5" />
                  <span>Validates structured payload against deterministic policy rules.</span>
                </div>
                <div className="flex items-start space-x-2">
                  <Check className="h-3.5 w-3.5 text-teal-600 dark:text-teal-400 shrink-0 mt-0.5" />
                  <span>Applies transparent mathematical scoring (Pass / Review / Block).</span>
                </div>
                <div className="flex items-start space-x-2">
                  <Check className="h-3.5 w-3.5 text-teal-600 dark:text-teal-400 shrink-0 mt-0.5" />
                  <span>Calculates SHA-256 audit digest &amp; prepares dossier for human controller.</span>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-teal-50/50 dark:bg-teal-950/20 text-[11px] text-teal-700 dark:text-teal-300 border border-teal-100 dark:border-teal-900/40">
                <strong>Core Axiom:</strong> TinyFish never determines the final payment decision. VendorShield governs the risk outcome with human dual-custody.
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION E — TRUST AND SAFETY: "Built to Fail Safely. Designed to Explain."
      ========================================================================= */}
      <section className="py-20 sm:py-28 border-b border-zinc-200/80 dark:border-zinc-800/80 bg-zinc-50/40 dark:bg-[#070b12]/40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="max-w-3xl space-y-3 mb-14">
            <span className="text-xs font-semibold uppercase tracking-wider text-teal-700 dark:text-teal-400">
              Safety Architecture &amp; Governance
            </span>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
              Built to Fail Safely. Designed to Explain.
            </h2>
            <p className="text-sm sm:text-base text-zinc-600 dark:text-zinc-400">
              Financial risk intelligence cannot rely on black-box probabilistic guesswork. VendorShield enforces 8 strict safety principles.
            </p>
          </div>

          {/* 8 Safety Principles Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            <div className="bg-white dark:bg-[#0f141f] border border-zinc-200/90 dark:border-zinc-800/90 rounded-xl p-5 shadow-subtle space-y-2.5">
              <div className="w-8 h-8 rounded-lg bg-teal-50 dark:bg-teal-950/40 text-teal-600 dark:text-teal-400 flex items-center justify-center">
                <Cpu className="h-4 w-4" />
              </div>
              <h3 className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">
                Deterministic Validation
              </h3>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
                Rules-based GSTIN checksums, status checks, and threshold formulas. Zero hallucinated approvals.
              </p>
            </div>

            <div className="bg-white dark:bg-[#0f141f] border border-zinc-200/90 dark:border-zinc-800/90 rounded-xl p-5 shadow-subtle space-y-2.5">
              <div className="w-8 h-8 rounded-lg bg-teal-50 dark:bg-teal-950/40 text-teal-600 dark:text-teal-400 flex items-center justify-center">
                <FileCheck className="h-4 w-4" />
              </div>
              <h3 className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">
                Evidence-Linked Claims
              </h3>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
                Every claim on an invoice document must point to a specific, verified citation before it earns trust.
              </p>
            </div>

            <div className="bg-white dark:bg-[#0f141f] border border-zinc-200/90 dark:border-zinc-800/90 rounded-xl p-5 shadow-subtle space-y-2.5">
              <div className="w-8 h-8 rounded-lg bg-teal-50 dark:bg-teal-950/40 text-teal-600 dark:text-teal-400 flex items-center justify-center">
                <Globe className="h-4 w-4" />
              </div>
              <h3 className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">
                Source URLs &amp; Snippets
              </h3>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
                Raw extracted registry excerpts and full source URLs are stored directly in the dossier for human audit.
              </p>
            </div>

            <div className="bg-white dark:bg-[#0f141f] border border-zinc-200/90 dark:border-zinc-800/90 rounded-xl p-5 shadow-subtle space-y-2.5">
              <div className="w-8 h-8 rounded-lg bg-teal-50 dark:bg-teal-950/40 text-teal-600 dark:text-teal-400 flex items-center justify-center">
                <Scale className="h-4 w-4" />
              </div>
              <h3 className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">
                Transparent Rule Scoring
              </h3>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
                Scoring penalties are explicit (e.g. Cancelled GSTIN: +80, Name Variance: +25). No opaque neural weights.
              </p>
            </div>

            <div className="bg-white dark:bg-[#0f141f] border border-zinc-200/90 dark:border-zinc-800/90 rounded-xl p-5 shadow-subtle space-y-2.5">
              <div className="w-8 h-8 rounded-lg bg-teal-50 dark:bg-teal-950/40 text-teal-600 dark:text-teal-400 flex items-center justify-center">
                <Fingerprint className="h-4 w-4" />
              </div>
              <h3 className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">
                SHA-256 Audit Trails
              </h3>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
                A cryptographic digest locks the evidence, claims, and reviewer rationale into an immutable audit record.
              </p>
            </div>

            <div className="bg-white dark:bg-[#0f141f] border border-zinc-200/90 dark:border-zinc-800/90 rounded-xl p-5 shadow-subtle space-y-2.5">
              <div className="w-8 h-8 rounded-lg bg-teal-50 dark:bg-teal-950/40 text-teal-600 dark:text-teal-400 flex items-center justify-center">
                <ShieldAlert className="h-4 w-4" />
              </div>
              <h3 className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">
                Fail-Closed Policy
              </h3>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
                If evidence is missing, conflicting, or inconclusive, the system never assumes safety — it flags for review.
              </p>
            </div>

            <div className="bg-white dark:bg-[#0f141f] border border-zinc-200/90 dark:border-zinc-800/90 rounded-xl p-5 shadow-subtle space-y-2.5">
              <div className="w-8 h-8 rounded-lg bg-teal-50 dark:bg-teal-950/40 text-teal-600 dark:text-teal-400 flex items-center justify-center">
                <Lock className="h-4 w-4" />
              </div>
              <h3 className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">
                Untrusted Web as Data
              </h3>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
                Third-party website text is sanitized and treated purely as passive data to prevent prompt injection attacks.
              </p>
            </div>

            <div className="bg-white dark:bg-[#0f141f] border border-zinc-200/90 dark:border-zinc-800/90 rounded-xl p-5 shadow-subtle space-y-2.5">
              <div className="w-8 h-8 rounded-lg bg-teal-50 dark:bg-teal-950/40 text-teal-600 dark:text-teal-400 flex items-center justify-center">
                <ShieldCheck className="h-4 w-4" />
              </div>
              <h3 className="font-semibold text-sm text-zinc-900 dark:text-zinc-100">
                Human Sign-off Requirement
              </h3>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
                VendorShield is decision support, not autonomous capital release. Consequential payments require human sign-off.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION F — HONEST LIMITATIONS: "Evidence First. Certainty Never Assumed."
      ========================================================================= */}
      <section id="limitations" className="py-20 sm:py-28 border-b border-zinc-200/80 dark:border-zinc-800/80 scroll-mt-14">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="max-w-3xl space-y-3 mb-14">
            <span className="text-xs font-semibold uppercase tracking-wider text-amber-600 dark:text-amber-400">
              System Boundary &amp; Intellectual Honesty
            </span>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
              Evidence First. Certainty Never Assumed.
            </h2>
            <p className="text-sm sm:text-base text-zinc-600 dark:text-zinc-400">
              We build trust by being transparent about what automated public-web investigation can and cannot verify today.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-6 rounded-xl border border-zinc-200/90 dark:border-zinc-800/90 bg-white dark:bg-[#0f141f] shadow-subtle space-y-3">
              <div className="flex items-center space-x-2 text-amber-700 dark:text-amber-400 font-semibold text-sm">
                <AlertCircle className="h-4 w-4" />
                <span>Sophisticated Shell Company Websites</span>
              </div>
              <p className="text-xs sm:text-sm text-zinc-600 dark:text-zinc-400 leading-relaxed">
                A real registered shell company can deploy a convincing corporate website with valid SSL and DNS records. VendorShield cross-checks multiple registries, but cannot independently inspect physical factory operations without field audit.
              </p>
            </div>

            <div className="p-6 rounded-xl border border-zinc-200/90 dark:border-zinc-800/90 bg-white dark:bg-[#0f141f] shadow-subtle space-y-3">
              <div className="flex items-center space-x-2 text-amber-700 dark:text-amber-400 font-semibold text-sm">
                <AlertCircle className="h-4 w-4" />
                <span>Bank Account Ownership Mismatches</span>
              </div>
              <p className="text-xs sm:text-sm text-zinc-600 dark:text-zinc-400 leading-relaxed">
                Public web scraping cannot verify bank beneficiary ownership without direct banking API access. Until penny-drop verification is connected, modified bank details remain a mandatory human review trigger.
              </p>
            </div>

            <div className="p-6 rounded-xl border border-zinc-200/90 dark:border-zinc-800/90 bg-white dark:bg-[#0f141f] shadow-subtle space-y-3">
              <div className="flex items-center space-x-2 text-amber-700 dark:text-amber-400 font-semibold text-sm">
                <AlertCircle className="h-4 w-4" />
                <span>Gated Registries &amp; CAPTCHAs</span>
              </div>
              <p className="text-xs sm:text-sm text-zinc-600 dark:text-zinc-400 leading-relaxed">
                TinyFish respects legal website terms and does not attempt CAPTCHA circumvention or unauthorized authentication bypass. Where a portal blocks access, evidence is marked unavailable.
              </p>
            </div>

            <div className="p-6 rounded-xl border border-zinc-200/90 dark:border-zinc-800/90 bg-white dark:bg-[#0f141f] shadow-subtle space-y-3">
              <div className="flex items-center space-x-2 text-amber-700 dark:text-amber-400 font-semibold text-sm">
                <AlertCircle className="h-4 w-4" />
                <span>Internal Collusion &amp; Unauthorized Creation</span>
              </div>
              <p className="text-xs sm:text-sm text-zinc-600 dark:text-zinc-400 leading-relaxed">
                If an internal employee colludes with an external vendor inside the enterprise ERP, external due diligence alone cannot replace dual-custody authorization and separation-of-duties internal controls.
              </p>
            </div>
          </div>

          <div className="mt-8 p-4 rounded-xl bg-amber-50/40 dark:bg-amber-950/20 border border-amber-200/80 dark:border-amber-900/60 text-xs text-amber-800 dark:text-amber-300">
            <strong>Key Principle:</strong> In VendorShield, a missing source or an uncorroborated claim is treated as a <em>reason for human review</em>, never as definitive proof of malicious fraud.
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION G — ROADMAP: "From Prototype to Pilot."
      ========================================================================= */}
      <section className="py-20 sm:py-28 border-b border-zinc-200/80 dark:border-zinc-800/80 bg-zinc-50/40 dark:bg-[#070b12]/40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="max-w-3xl space-y-3 mb-14">
            <span className="text-xs font-semibold uppercase tracking-wider text-teal-700 dark:text-teal-400">
              Maturity &amp; Progression
            </span>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
              From Prototype to Pilot.
            </h2>
            <p className="text-sm sm:text-base text-zinc-600 dark:text-zinc-400">
              Clear demarcation between operational MVP functionality developed for HackIIITD and enterprise pilot capabilities on the roadmap.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* MVP Scope (Current Development) */}
            <div className="bg-white dark:bg-[#0f141f] border border-teal-200/80 dark:border-teal-900/60 rounded-2xl p-6 shadow-subtle space-y-5">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-1 rounded text-xs font-semibold bg-teal-50 dark:bg-teal-950/40 text-teal-700 dark:text-teal-400 border border-teal-200 dark:border-teal-800">
                  CURRENT MVP SCOPE
                </span>
                <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">
                  Operational in Codebase
                </span>
              </div>

              <div className="space-y-3 text-xs text-zinc-700 dark:text-zinc-300">
                <div className="flex items-start space-x-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                  <span><strong>PDF Invoice Parsing:</strong> Rule-based and text extraction of supplier identity, invoice amount, and GSTIN claims.</span>
                </div>
                <div className="flex items-start space-x-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                  <span><strong>GSTIN Format &amp; Checksum:</strong> Exact Python implementation of Luhn-mod-36 checksum mathematical verification.</span>
                </div>
                <div className="flex items-start space-x-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                  <span><strong>TinyFish Web Agent:</strong> Autonomous navigation of public registry portals and vendor web domains for evidence collection.</span>
                </div>
                <div className="flex items-start space-x-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                  <span><strong>Deterministic Scoring:</strong> Transparent Pass / Review / Block policy engine with explicit rule weightings.</span>
                </div>
                <div className="flex items-start space-x-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                  <span><strong>Dossier &amp; Audit Logs:</strong> Full review interface, human sign-off notes, and SHA-256 tamper-evident audit report generation.</span>
                </div>
              </div>
            </div>

            {/* Pilot Roadmap */}
            <div className="bg-white dark:bg-[#0f141f] border border-zinc-200/90 dark:border-zinc-800/90 rounded-2xl p-6 shadow-subtle space-y-5">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-1 rounded text-xs font-semibold bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-700">
                  PLANNED PILOT WORK
                </span>
                <span className="text-xs text-zinc-400 font-medium">
                  Next Milestone
                </span>
              </div>

              <div className="space-y-3 text-xs text-zinc-600 dark:text-zinc-400">
                <div className="flex items-start space-x-2">
                  <Clock className="h-4 w-4 text-teal-600 dark:text-teal-400 shrink-0 mt-0.5" />
                  <span><strong>Enterprise ERP Connectors:</strong> Native webhooks and batch intake adapters for SAP S/4HANA, Oracle NetSuite, and Tally Prime.</span>
                </div>
                <div className="flex items-start space-x-2">
                  <Clock className="h-4 w-4 text-teal-600 dark:text-teal-400 shrink-0 mt-0.5" />
                  <span><strong>Asynchronous Workers &amp; Caching:</strong> Celery/Redis background worker queue with encrypted registry cache to handle high-volume invoice bursts.</span>
                </div>
                <div className="flex items-start space-x-2">
                  <Clock className="h-4 w-4 text-teal-600 dark:text-teal-400 shrink-0 mt-0.5" />
                  <span><strong>Penny-Drop Banking Verification:</strong> Integrated NPCI/bank API validation to verify beneficiary name match before disbursements.</span>
                </div>
                <div className="flex items-start space-x-2">
                  <Clock className="h-4 w-4 text-teal-600 dark:text-teal-400 shrink-0 mt-0.5" />
                  <span><strong>Role-Based Dual Custody:</strong> Multi-tiered approval policies (e.g. invoices &gt; ₹5,00,000 require dual finance manager sign-off).</span>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-zinc-50 dark:bg-zinc-900/40 text-[11px] text-zinc-500 border border-zinc-200/70 dark:border-zinc-800/70">
                <strong>Measurement Target:</strong> Target verification runtime of &lt;60 seconds per vendor and a 5-team AP pilot are forward-looking design goals to evaluate, not claimed production metrics.
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          FINAL CALL TO ACTION & PLATFORM LAUNCH
      ========================================================================= */}
      <section className="py-20 sm:py-28 relative">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 text-center space-y-6">
          <div className="w-12 h-12 rounded-2xl bg-teal-600/10 text-teal-600 dark:text-teal-400 mx-auto flex items-center justify-center border border-teal-500/20">
            <Shield className="h-6 w-6 stroke-[2.2]" />
          </div>

          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
            Secure Your Accounts Payable Pipeline
          </h2>

          <p className="text-sm sm:text-base text-zinc-600 dark:text-zinc-400 max-w-xl mx-auto leading-relaxed">
            Protect your organization from circular fake invoices and lost input tax credit. Test the live due-diligence platform now.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <Link
              href="/queue"
              className="inline-flex items-center space-x-2 px-6 py-3 rounded-lg text-sm font-semibold text-white bg-teal-700 hover:bg-teal-600 dark:bg-teal-600 dark:hover:bg-teal-500 transition-all shadow-md hover:shadow-teal-500/20 active:scale-95"
            >
              <span>Explore Platform Queue</span>
              <ArrowRight className="h-4 w-4" />
            </Link>

            <Link
              href="/upload"
              className="inline-flex items-center space-x-2 px-6 py-3 rounded-lg text-sm font-medium text-zinc-700 dark:text-zinc-300 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800/60 transition-colors shadow-subtle active:scale-95"
            >
              <span>Intake Benchmark Invoice</span>
              <ChevronRight className="h-4 w-4 text-zinc-400" />
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
