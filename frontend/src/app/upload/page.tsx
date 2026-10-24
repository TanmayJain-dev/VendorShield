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
  ShieldAlert,
  Sparkles,
  Info
} from 'lucide-react';

export default function IntakePage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [supplierName, setSupplierName] = useState('Apex Courier');
  const [gstin, setGstin] = useState('07AAAAA0000A1Z5');
  const [invoiceNumber, setInvoiceNumber] = useState('INV-2026-8841');
  const [totalAmount, setTotalAmount] = useState('482500.00');
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

  const isGstinFormatValid = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/.test(gstin);

  return (
    <div className="max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 sm:py-8 animate-reveal-up">
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <Link
            href="/queue"
            className="inline-flex items-center space-x-1 text-xs text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200 transition-colors mb-2"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Back to Cases Queue</span>
          </Link>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
            Supplier Invoice Intake & Pre-Disbursal Gate
          </h1>
          <p className="text-xs sm:text-sm text-zinc-500 dark:text-zinc-400 mt-1 max-w-xl leading-relaxed">
            Autonomous 4-hop forensic audit powered by TinyFish Live Web Agents. Reconciles GSTR-3B filings, NCLT dockets, DGGI enforcement radar, and IndiaMART wholesale prices.
          </p>
        </div>

        {/* Preset Scenarios Card */}
        <div className="bg-white dark:bg-[#0e1420] border border-zinc-200/90 dark:border-zinc-800/90 rounded-xl p-4 sm:p-5 space-y-3 shadow-subtle">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-zinc-800 dark:text-zinc-200">
              1-Click Enterprise Audit Scenarios
            </span>
            <span className="text-[11px] text-zinc-400 font-mono">Live TinyFish SSE Ready</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {/* Scenario 0: Havells Live Enterprise Preset */}
            <button
              type="button"
              onClick={loadHavellsLivePreset}
              className={`p-3 text-left rounded-xl border text-xs transition-all ${
                selectedScenario === 'havells'
                  ? 'border-indigo-600 dark:border-indigo-500 bg-indigo-50/50 dark:bg-indigo-950/30 ring-1 ring-indigo-500/30'
                  : 'border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800/40'
              }`}
            >
              <div className="flex items-center justify-between font-bold text-zinc-900 dark:text-zinc-100">
                <span className="font-mono text-[10px]">INV-2026-9901</span>
                <span className="text-[10px] font-mono font-bold text-indigo-700 dark:text-indigo-400">₹4,98,550</span>
              </div>
              <div className="text-[11px] font-semibold text-zinc-800 dark:text-zinc-200 mt-1 truncate">
                Havells India Ltd
              </div>
              <div className="text-[10px] text-zinc-500 dark:text-zinc-400 mt-0.5 leading-snug">
                Real GSTIN (07AAACH0828A1ZE) + IndiaMART copper cable benchmark.
              </div>
            </button>

            {/* Scenario 1: Apex Courier Benchmark */}
            <button
              type="button"
              onClick={loadBenchmarkPreset}
              className={`p-3 text-left rounded-xl border text-xs transition-all ${
                selectedScenario === 'benchmark'
                  ? 'border-teal-600 dark:border-teal-500 bg-teal-50/50 dark:bg-teal-950/30 ring-1 ring-teal-500/30'
                  : 'border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800/40'
              }`}
            >
              <div className="flex items-center justify-between font-bold text-zinc-900 dark:text-zinc-100">
                <span className="font-mono text-[10px]">INV-2026-8841</span>
                <span className="text-[10px] font-mono font-bold text-teal-700 dark:text-teal-400">₹4,82,500</span>
              </div>
              <div className="text-[11px] font-semibold text-zinc-800 dark:text-zinc-200 mt-1 truncate">
                Apex Courier Pvt Ltd
              </div>
              <div className="text-[10px] text-zinc-500 dark:text-zinc-400 mt-0.5 leading-snug">
                Trade alias discrepancy & MSME 43B(h) Split Escrow hold.
              </div>
            </button>

            {/* Scenario 2: Specter Cloud Ghost Vendor */}
            <button
              type="button"
              onClick={loadGhostVendorPreset}
              className={`p-3 text-left rounded-xl border text-xs transition-all ${
                selectedScenario === 'ghost'
                  ? 'border-rose-600 dark:border-rose-500 bg-rose-50/50 dark:bg-rose-950/30 ring-1 ring-rose-500/30'
                  : 'border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800/40'
              }`}
            >
              <div className="flex items-center justify-between font-bold text-zinc-900 dark:text-zinc-100">
                <span className="font-mono text-[10px]">INV-2026-8842</span>
                <span className="text-[10px] font-mono font-bold text-rose-700 dark:text-rose-400">₹2,95,000</span>
              </div>
              <div className="text-[11px] font-semibold text-zinc-800 dark:text-zinc-200 mt-1 truncate">
                Specter Cloud Shell
              </div>
              <div className="text-[10px] text-zinc-500 dark:text-zinc-400 mt-0.5 leading-snug">
                NCLT petition & 38-firm ghost hub (Forensic Freeze).
              </div>
            </button>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-3.5 rounded-lg bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/60 text-xs text-rose-800 dark:text-rose-300 flex items-center space-x-2">
            <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" />
            <span>{error}</span>
          </div>
        )}

        {/* Main Intake Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Dropzone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-xl p-8 text-center transition-all ${
              isDragging
                ? 'border-teal-500 bg-teal-50/30 dark:bg-teal-950/30 scale-[1.01]'
                : 'border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#0e1420] shadow-subtle'
            }`}
          >
            {file ? (
              <div className="flex items-center justify-center space-x-3">
                <div className="w-10 h-10 rounded-lg bg-teal-50 dark:bg-teal-950/40 text-teal-600 dark:text-teal-400 flex items-center justify-center">
                  <FileText className="h-5 w-5" />
                </div>
                <div className="text-left text-xs">
                  <div className="font-semibold text-zinc-900 dark:text-zinc-100">{file.name}</div>
                  <div className="text-[11px] text-zinc-400 font-mono">{(file.size / 1024).toFixed(1)} KB &bull; Attached</div>
                </div>
                <button
                  type="button"
                  onClick={() => setFile(null)}
                  className="p-1.5 rounded-md text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors ml-3"
                  aria-label="Remove attached file"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="w-12 h-12 rounded-xl bg-zinc-100 dark:bg-zinc-800/80 text-zinc-500 dark:text-zinc-400 mx-auto flex items-center justify-center">
                  <UploadCloud className="h-6 w-6 stroke-[1.8]" />
                </div>
                <div className="text-xs font-semibold text-zinc-800 dark:text-zinc-200">
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
                <div className="text-[11px] text-zinc-400">
                  Supports PDF documents, TIFF, or image scans up to 10MB
                </div>
              </div>
            )}
          </div>

          {/* Claim Input Fields Card */}
          <div className="bg-white dark:bg-[#0e1420] border border-zinc-200/90 dark:border-zinc-800/90 rounded-xl p-5 sm:p-6 space-y-4 shadow-subtle">
            <div className="flex items-center justify-between pb-3 border-b border-zinc-100 dark:border-zinc-800/80 text-xs">
              <span className="font-semibold text-zinc-900 dark:text-zinc-100">
                Invoice Claim Parameters
              </span>
              <span className="text-[11px] text-zinc-400">Extracted or declared values</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              {/* Supplier Name */}
              <div className="space-y-1">
                <label className="block text-zinc-700 dark:text-zinc-300 font-medium">
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
                  className="w-full px-3 py-2 bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-1 focus:ring-teal-500 font-medium text-xs transition-colors"
                  placeholder="e.g. Apex Courier"
                />
              </div>

              {/* GSTIN */}
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <label className="block text-zinc-700 dark:text-zinc-300 font-medium">
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
                    className="w-full px-3 py-2 font-mono uppercase bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-1 focus:ring-teal-500 font-semibold text-xs transition-colors"
                    placeholder="07AAAAA0000A1Z5"
                  />
                  {gstin.length === 15 && (
                    <div className="absolute right-2.5 top-1/2 -translate-y-1/2">
                      {isGstinFormatValid ? (
                        <span className="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400">Valid Format</span>
                      ) : (
                        <span className="text-[10px] font-semibold text-rose-600 dark:text-rose-400">Invalid Format</span>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Invoice Number */}
              <div className="space-y-1">
                <label className="block text-zinc-700 dark:text-zinc-300 font-medium">
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
                  className="w-full px-3 py-2 font-mono bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-1 focus:ring-teal-500 font-medium text-xs transition-colors"
                  placeholder="INV-2026-8841"
                />
              </div>

              {/* Total Amount */}
              <div className="space-y-1">
                <label className="block text-zinc-700 dark:text-zinc-300 font-medium">
                  Total Payable Amount (INR) <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 font-mono text-zinc-400 text-xs">
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
                    className="w-full pl-7 pr-3 py-2 font-mono bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-1 focus:ring-teal-500 font-semibold text-xs tabular-nums transition-colors"
                    placeholder="482500.00"
                  />
                </div>
                <div className="text-[10.5px] text-zinc-400 text-right tabular-nums">
                  Formatted: <strong className="text-zinc-700 dark:text-zinc-300">{formattedAmount}</strong>
                </div>
              </div>
            </div>
          </div>

          {/* Form Actions */}
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
              className="group inline-flex items-center space-x-2 px-5 py-2.5 rounded-lg text-xs font-semibold text-white bg-teal-700 hover:bg-teal-600 dark:bg-teal-600 dark:hover:bg-teal-500 transition-all duration-200 shadow-sm hover:shadow-teal-500/20 active:scale-95 disabled:opacity-50"
            >
              <span>{loading ? 'Ingesting Claims...' : 'Proceed to Dossier'}</span>
              <ArrowRight className="h-3.5 w-3.5 group-hover:translate-x-0.5 transition-transform" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
