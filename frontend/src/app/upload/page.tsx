'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '../../lib/api';
import {
  UploadCloud,
  FileText,
  ArrowRight,
  Check,
  AlertCircle,
  X,
  ArrowLeft,
  ShieldCheck,
  Sparkles,
  Zap
} from 'lucide-react';

export default function IntakePage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [supplierName, setSupplierName] = useState('Havells Industrial Electricals');
  const [gstin, setGstin] = useState('07AAACH0828A1ZE');
  const [invoiceNumber, setInvoiceNumber] = useState('INV-2026-9901');
  const [totalAmount, setTotalAmount] = useState('498550.00');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedScenario, setSelectedScenario] = useState<'havells' | 'benchmark' | 'ghost' | null>('havells');

  const loadHavellsLivePreset = () => {
    setSupplierName('Havells Industrial Electricals');
    setGstin('07AAACH0828A1ZE');
    setInvoiceNumber('INV-2026-9901');
    setTotalAmount('498550.00');
    setSelectedScenario('havells');
  };

  const loadBenchmarkPreset = () => {
    setSupplierName('Apex Courier');
    setGstin('07AAAAA0000A1Z5');
    setInvoiceNumber('INV-2026-8841');
    setTotalAmount('482500.00');
    setSelectedScenario('benchmark');
  };

  const loadGhostVendorPreset = () => {
    setSupplierName('Specter Cloud Technologies');
    setGstin('07AAAAA0000A1Z5');
    setInvoiceNumber('INV-2026-8842');
    setTotalAmount('295000.00');
    setSelectedScenario('ghost');
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
  
    try {
      const formData = new FormData();
      if (file) formData.append('file', file);
      formData.append('supplier_name', supplierName);
      formData.append('gstin', gstin);
      formData.append('invoice_number', invoiceNumber);
      formData.append('total_amount', totalAmount);

      const createdCase = await api.createCase(formData);
      router.push(`/cases/${createdCase.case_id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to submit invoice intake.');
      setLoading(false);
    }
  };

  const formattedAmount = (() => {
    const num = parseFloat(totalAmount);
    if (isNaN(num)) return '₹0.00';
    return `₹${num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  })();

  const parsedTotal = parseFloat(totalAmount) || 0;
  const isGstinFormatValid = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/.test(gstin);

  return (
    <div className="max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 sm:py-8 animate-reveal-up text-zinc-900 dark:text-zinc-100">
      {/* Top Header */}
      <div className="mb-6">
        <Link
          href="/queue"
          className="inline-flex items-center space-x-1.5 text-xs text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200 transition-colors mb-2.5"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to Cases Queue</span>
        </Link>
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
              Supplier Invoice Intake & Pre-Disbursal Gate
            </h1>
            <p className="text-xs sm:text-sm text-zinc-500 dark:text-zinc-400 mt-1 max-w-2xl leading-relaxed">
              Autonomous 4-hop forensic audit powered by TinyFish Live Web Agents. Reconciles GSTR-3B filings, NCLT dockets, DGGI enforcement radar, and IndiaMART wholesale prices.
            </p>
          </div>
          <div className="inline-flex items-center gap-2 self-start md:self-auto px-3 py-1.5 rounded-full bg-teal-50 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-800 text-[11px] font-medium text-teal-800 dark:text-teal-300 shrink-0">
            <span className="w-2 h-2 rounded-full bg-teal-500 animate-pulse"></span>
            <span>TinyFish Live Agent Engine Active</span>
          </div>
        </div>
      </div>

      {/* Main Responsive Grid Layout (5:7 ratio on desktop) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column (5 cols): File Upload & 1-Click Test Scenarios */}
        <div className="lg:col-span-5 space-y-5">
          {/* Source Document Dropzone Card */}
          <div className="bg-white dark:bg-[#0e1420] border border-zinc-200/90 dark:border-zinc-800/90 rounded-2xl p-5 shadow-subtle space-y-3.5">
            <div className="flex items-center justify-between pb-2.5 border-b border-zinc-100 dark:border-zinc-800/80">
              <span className="text-xs font-semibold text-zinc-900 dark:text-zinc-100">
                Source Invoice Document
              </span>
              <span className="text-[11px] text-zinc-400 font-mono">Optional PDF / Scan</span>
            </div>

            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-xl p-5 text-center transition-all ${
                isDragging
                  ? 'border-teal-500 bg-teal-50/40 dark:bg-teal-950/40 scale-[1.01]'
                  : 'border-zinc-200 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-900/30 hover:border-zinc-300 dark:hover:border-zinc-700'
              }`}
            >
              {file ? (
                <div className="flex items-center justify-between p-3 rounded-lg bg-teal-50/80 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-800/60">
                  <div className="flex items-center space-x-3 text-left">
                    <div className="w-9 h-9 rounded-lg bg-teal-600 text-white flex items-center justify-center shrink-0">
                      <FileText className="h-5 w-5" />
                    </div>
                    <div className="truncate max-w-[180px] sm:max-w-[220px]">
                      <div className="text-xs font-semibold text-zinc-900 dark:text-zinc-100 truncate">{file.name}</div>
                      <div className="text-[10px] text-zinc-500 dark:text-zinc-400 font-mono">{(file.size / 1024).toFixed(1)} KB &bull; Attached</div>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setFile(null)}
                    className="p-1 rounded-md text-zinc-400 hover:text-rose-600 dark:hover:text-rose-400 transition-colors"
                    title="Remove file"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ) : (
                <div className="space-y-2 py-2">
                  <div className="w-10 h-10 rounded-xl bg-teal-50 dark:bg-teal-950/50 text-teal-600 dark:text-teal-400 mx-auto flex items-center justify-center">
                    <UploadCloud className="h-5 w-5 stroke-[1.8]" />
                  </div>
                  <div className="text-xs font-medium text-zinc-700 dark:text-zinc-300">
                    Drop vendor invoice PDF here, or{' '}
                    <label className="text-teal-600 dark:text-teal-400 hover:underline cursor-pointer font-bold">
                      browse files
                      <input
                        type="file"
                        accept=".pdf,.png,.jpg,.jpeg"
                        onChange={(e) => e.target.files && setFile(e.target.files[0])}
                        className="hidden"
                      />
                    </label>
                  </div>
                  <div className="text-[10px] text-zinc-400">
                    Supports PDF documents, TIFF, or image scans up to 10MB
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 1-Click Enterprise Audit Scenarios */}
          <div className="bg-white dark:bg-[#0e1420] border border-zinc-200/90 dark:border-zinc-800/90 rounded-2xl p-5 shadow-subtle space-y-3">
            <div className="flex items-center justify-between pb-2.5 border-b border-zinc-100 dark:border-zinc-800/80">
              <div>
                <span className="text-xs font-semibold text-zinc-900 dark:text-zinc-100 block">
                  1-Click Enterprise Audit Scenarios
                </span>
                <span className="text-[10.5px] text-zinc-400">Preload verified forensic benchmark cases</span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300">
                Live SSE
              </span>
            </div>

            <div className="space-y-2.5">
              {/* Scenario 0: Havells Live Enterprise Preset */}
              <button
                type="button"
                onClick={loadHavellsLivePreset}
                className={`w-full p-3 text-left rounded-xl border text-xs transition-all relative ${
                  selectedScenario === 'havells'
                    ? 'border-indigo-600 dark:border-indigo-500 bg-indigo-50/60 dark:bg-indigo-950/30 ring-1 ring-indigo-500/40 shadow-sm'
                    : 'border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800/40'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[10px] font-bold text-zinc-900 dark:text-zinc-100">INV-2026-9901</span>
                  <span className="text-[11px] font-mono font-bold text-indigo-700 dark:text-indigo-400">₹4,98,550</span>
                </div>
                <div className="text-xs font-bold text-zinc-900 dark:text-zinc-100 mt-1">Havells India Ltd</div>
                <div className="text-[10.5px] text-zinc-500 dark:text-zinc-400 mt-0.5 leading-snug">
                  Real GSTIN (07AAACH0828A1ZE) + IndiaMART copper cable benchmark.
                </div>
              </button>

              {/* Scenario 1: Apex Courier Benchmark */}
              <button
                type="button"
                onClick={loadBenchmarkPreset}
                className={`w-full p-3 text-left rounded-xl border text-xs transition-all relative ${
                  selectedScenario === 'benchmark'
                    ? 'border-teal-600 dark:border-teal-500 bg-teal-50/60 dark:bg-teal-950/30 ring-1 ring-teal-500/40 shadow-sm'
                    : 'border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800/40'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[10px] font-bold text-zinc-900 dark:text-zinc-100">INV-2026-8841</span>
                  <span className="text-[11px] font-mono font-bold text-teal-700 dark:text-teal-400">₹4,82,500</span>
                </div>
                <div className="text-xs font-bold text-zinc-900 dark:text-zinc-100 mt-1">Apex Courier Pvt Ltd</div>
                <div className="text-[10.5px] text-zinc-500 dark:text-zinc-400 mt-0.5 leading-snug">
                  Trade alias discrepancy & MSME 43B(h) Split Escrow hold.
                </div>
              </button>

              {/* Scenario 2: Specter Cloud Ghost Vendor */}
              <button
                type="button"
                onClick={loadGhostVendorPreset}
                className={`w-full p-3 text-left rounded-xl border text-xs transition-all relative ${
                  selectedScenario === 'ghost'
                    ? 'border-rose-600 dark:border-rose-500 bg-rose-50/60 dark:bg-rose-950/30 ring-1 ring-rose-500/40 shadow-sm'
                    : 'border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800/40'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[10px] font-bold text-zinc-900 dark:text-zinc-100">INV-2026-8842</span>
                  <span className="text-[11px] font-mono font-bold text-rose-700 dark:text-rose-400">₹2,95,000</span>
                </div>
                <div className="text-xs font-bold text-zinc-900 dark:text-zinc-100 mt-1">Specter Cloud Shell</div>
                <div className="text-[10.5px] text-zinc-500 dark:text-zinc-400 mt-0.5 leading-snug">
                  NCLT petition & 38-firm ghost hub (Forensic Freeze).
                </div>
              </button>
            </div>
          </div>

          {/* Autonomous Telemetry Pipeline Guide */}
          <div className="bg-zinc-50/80 dark:bg-zinc-900/40 border border-zinc-200/80 dark:border-zinc-800/80 rounded-2xl p-4 text-[11px] space-y-2 text-zinc-600 dark:text-zinc-400">
            <div className="font-semibold text-zinc-800 dark:text-zinc-200 flex items-center space-x-1.5">
              <Sparkles className="h-3.5 w-3.5 text-teal-600 dark:text-teal-400" />
              <span>TinyFish 4-Hop Autonomous Pipeline</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-[10px] pt-1 font-mono">
              <div className="flex items-center space-x-1 text-zinc-600 dark:text-zinc-300">
                <span className="w-1.5 h-1.5 rounded-full bg-teal-500"></span>
                <span>1. GSTN Velocity</span>
              </div>
              <div className="flex items-center space-x-1 text-zinc-600 dark:text-zinc-300">
                <span className="w-1.5 h-1.5 rounded-full bg-teal-500"></span>
                <span>2. MCA Shell Network</span>
              </div>
              <div className="flex items-center space-x-1 text-zinc-600 dark:text-zinc-300">
                <span className="w-1.5 h-1.5 rounded-full bg-teal-500"></span>
                <span>3. DGGI Radar</span>
              </div>
              <div className="flex items-center space-x-1 text-zinc-600 dark:text-zinc-300">
                <span className="w-1.5 h-1.5 rounded-full bg-teal-500"></span>
                <span>4. IndiaMART Benchmarks</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column (7 cols): Invoice Claim Parameters & Pre-Disbursal Projection */}
        <div className="lg:col-span-7 space-y-5">
          <div className="bg-white dark:bg-[#0e1420] border border-zinc-200/90 dark:border-zinc-800/90 rounded-2xl p-6 shadow-subtle space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-zinc-100 dark:border-zinc-800/80">
              <div>
                <h2 className="text-sm font-bold text-zinc-900 dark:text-zinc-100">
                  Invoice Claim Parameters
                </h2>
                <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
                  Declared supplier details & statutory billing credentials
                </p>
              </div>
              <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/60 text-[10px] font-medium text-emerald-700 dark:text-emerald-400">
                <ShieldCheck className="h-3.5 w-3.5" />
                <span>Pre-Disbursal Gated</span>
              </div>
            </div>

            {/* Error Alert */}
            {error && (
              <div className="p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/60 text-xs text-rose-800 dark:text-rose-300 flex items-center space-x-2">
                <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" />
                <span>{error}</span>
              </div>
            )}

            {/* Form Fields */}
            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                {/* Supplier Name */}
                <div className="space-y-1.5">
                  <label className="block text-zinc-700 dark:text-zinc-300 font-semibold">
                    Supplier Trade Name <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={supplierName}
                    onChange={(e) => {
                      setSupplierName(e.target.value);
                      setSelectedScenario(null);
                    }}
                    className="w-full px-3.5 py-2.5 bg-zinc-50/80 dark:bg-zinc-900/80 border border-zinc-200 dark:border-zinc-800 rounded-xl text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 font-medium text-xs transition-colors"
                    placeholder="e.g. Havells India Ltd"
                  />
                </div>

                {/* Supplier GSTIN */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="block text-zinc-700 dark:text-zinc-300 font-semibold">
                      Supplier GSTIN <span className="text-rose-500">*</span>
                    </label>
                    <span className="text-[10px] text-zinc-400 font-mono">
                      {gstin.length}/15
                    </span>
                  </div>
                  <div className="relative">
                    <input
                      type="text"
                      maxLength={15}
                      value={gstin}
                      onChange={(e) => {
                        setGstin(e.target.value.toUpperCase());
                        setSelectedScenario(null);
                      }}
                      className="w-full px-3.5 py-2.5 font-mono uppercase bg-zinc-50/80 dark:bg-zinc-900/80 border border-zinc-200 dark:border-zinc-800 rounded-xl text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 font-semibold text-xs transition-colors"
                      placeholder="07AAACH0828A1ZE"
                    />
                    {gstin.length === 15 && (
                      <div className="absolute right-2.5 top-1/2 -translate-y-1/2">
                        {isGstinFormatValid ? (
                          <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/60">
                            Valid Modulo-36
                          </span>
                        ) : (
                          <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-rose-50 dark:bg-rose-950/60 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-800/60">
                            Invalid Format
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {/* Invoice Number */}
                <div className="space-y-1.5">
                  <label className="block text-zinc-700 dark:text-zinc-300 font-semibold">
                    Invoice Number <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={invoiceNumber}
                    onChange={(e) => {
                      setInvoiceNumber(e.target.value);
                      setSelectedScenario(null);
                    }}
                    className="w-full px-3.5 py-2.5 font-mono bg-zinc-50/80 dark:bg-zinc-900/80 border border-zinc-200 dark:border-zinc-800 rounded-xl text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 font-medium text-xs transition-colors"
                    placeholder="INV-2026-9901"
                  />
                </div>

                {/* Total Amount */}
                <div className="space-y-1.5">
                  <label className="block text-zinc-700 dark:text-zinc-300 font-semibold">
                    Total Payable Amount (INR) <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <span className="absolute left-3.5 top-1/2 -translate-y-1/2 font-mono text-zinc-400 text-xs">
                      ₹
                    </span>
                    <input
                      type="number"
                      step="0.01"
                      required
                      value={totalAmount}
                      onChange={(e) => {
                        setTotalAmount(e.target.value);
                        setSelectedScenario(null);
                      }}
                      className="w-full pl-8 pr-3.5 py-2.5 font-mono bg-zinc-50/80 dark:bg-zinc-900/80 border border-zinc-200 dark:border-zinc-800 rounded-xl text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 font-semibold text-xs tabular-nums transition-colors"
                      placeholder="498550.00"
                    />
                  </div>
                  <div className="text-[10px] text-zinc-400 text-right tabular-nums">
                    Formatted: <strong className="text-zinc-700 dark:text-zinc-300">{formattedAmount}</strong>
                  </div>
                </div>
              </div>

              {/* Real-time Dynamic Split-Settlement Routing Preview */}
              <div className="p-4 rounded-xl bg-zinc-50 dark:bg-[#090d16] border border-zinc-200/80 dark:border-zinc-800/80 space-y-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-zinc-800 dark:text-zinc-200 flex items-center gap-1.5">
                    <Zap className="h-3.5 w-3.5 text-amber-500" />
                    <span>Projected Pre-Disbursal Settlement Routing</span>
                  </span>
                  <span className="text-[10px] font-mono text-zinc-500 dark:text-zinc-400">
                    2026 GSTN IMS Model
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3 pt-1">
                  <div className="p-2.5 rounded-lg bg-white dark:bg-zinc-900/80 border border-zinc-200/80 dark:border-zinc-800/80">
                    <div className="text-[10px] text-zinc-500 dark:text-zinc-400 font-medium">Safe Base Disbursal (82%)</div>
                    <div className="text-sm font-bold font-mono text-emerald-600 dark:text-emerald-400 mt-0.5">
                      ₹{(parsedTotal * 0.82).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                    <div className="text-[9.5px] text-zinc-400 mt-0.5">Immediate wire disbursal</div>
                  </div>

                  <div className="p-2.5 rounded-lg bg-white dark:bg-zinc-900/80 border border-zinc-200/80 dark:border-zinc-800/80">
                    <div className="text-[10px] text-zinc-500 dark:text-zinc-400 font-medium">Contingent GST Escrow (18%)</div>
                    <div className="text-sm font-bold font-mono text-amber-600 dark:text-amber-400 mt-0.5">
                      ₹{(parsedTotal * 0.18).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                    <div className="text-[9.5px] text-zinc-400 mt-0.5">Auto-released on GSTR-2B reflection</div>
                  </div>
                </div>
              </div>

              {/* Submit & Cancel Actions */}
              <div className="flex items-center justify-between pt-2">
                <Link
                  href="/queue"
                  className="text-xs text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200 transition-colors"
                >
                  Cancel and Return
                </Link>

                <button
                  type="submit"
                  disabled={loading}
                  className="group inline-flex items-center space-x-2 px-6 py-2.5 rounded-xl text-xs font-semibold text-white bg-teal-700 hover:bg-teal-600 dark:bg-teal-600 dark:hover:bg-teal-500 transition-all duration-200 shadow-sm hover:shadow-teal-500/20 active:scale-95 disabled:opacity-50 cursor-pointer"
                >
                  <span>{loading ? 'Ingesting Claims...' : 'Initiate Forensic Pre-Disbursal Gate'}</span>
                  <ArrowRight className="h-4 w-4 group-hover:translate-x-0.5 transition-transform" />
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
