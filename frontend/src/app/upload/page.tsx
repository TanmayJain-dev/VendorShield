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
  ShieldAlert,
  ChevronDown,
  Info,
  Files
} from 'lucide-react';

export default function IntakePage() {
  const router = useRouter();
  const [files, setFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [supplierName, setSupplierName] = useState('');
  const [gstin, setGstin] = useState('');
  const [invoiceNumber, setInvoiceNumber] = useState('');
  const [totalAmount, setTotalAmount] = useState('');
  const [isDemo, setIsDemo] = useState(false);
  const [loading, setLoading] = useState(false);
  const [progressMsg, setProgressMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [presetsOpen, setPresetsOpen] = useState(false);

  const loadBenchmarkPreset = () => {
    setSupplierName('Apex Courier');
    setGstin('07AAAAA0000A1Z4');
    setInvoiceNumber('INV-2026-8841');
    setTotalAmount('482500.00');
    setIsDemo(true);
    setFiles([]);
  };

  const loadGhostVendorPreset = () => {
    setSupplierName('Specter Cloud Technologies');
    setGstin('07AAAAA0000A1Z4');
    setInvoiceNumber('INV-2026-8842');
    setTotalAmount('295000.00');
    setIsDemo(true);
    setFiles([]);
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
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFiles = Array.from(e.dataTransfer.files).filter(f =>
        f.name.match(/\.(pdf|png|jpe?g)$/i)
      );
      if (droppedFiles.length === 0) {
        setError('Only PDF, PNG, or JPEG files are accepted.');
        return;
      }
      setFiles(prev => [...prev, ...droppedFiles]);
      setIsDemo(false);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const selected = Array.from(e.target.files).filter(f =>
        f.name.match(/\.(pdf|png|jpe?g)$/i)
      );
      setFiles(prev => [...prev, ...selected]);
      setIsDemo(false);
    }
  };

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setProgressMsg(null);

    try {
      if (files.length > 0) {
        // Multi-file or single file upload flow
        const createdCaseIds: string[] = [];
        for (let i = 0; i < files.length; i++) {
          const currentFile = files[i];
          setProgressMsg(`Processing file ${i + 1} of ${files.length}: ${currentFile.name}...`);
          
          const meta = files.length === 1 ? {
            supplier_name: supplierName.trim() || undefined,
            gstin: gstin.trim() ? gstin.trim().toUpperCase() : undefined,
            invoice_number: invoiceNumber.trim() || undefined,
            total_amount: totalAmount ? parseFloat(totalAmount) : undefined,
            is_demo: isDemo
          } : {
            is_demo: isDemo
          };

          const created = await api.uploadInvoice(currentFile, meta);
          createdCaseIds.push(created.case_id);
        }

        if (createdCaseIds.length === 1) {
          router.push(`/cases/${createdCaseIds[0]}`);
        } else {
          router.push('/queue');
        }
      } else {
        // Manual entry intake (no file attached)
        if (!supplierName.trim()) {
          throw new Error('Please attach an invoice file or provide at least a Supplier Name.');
        }

        const formData = new FormData();
        formData.append('supplier_name', supplierName.trim());
        if (gstin.trim()) formData.append('gstin', gstin.trim().toUpperCase());
        if (invoiceNumber.trim()) formData.append('invoice_number', invoiceNumber.trim());
        if (totalAmount) formData.append('total_amount', totalAmount);
        formData.append('is_demo', String(isDemo));

        const createdCase = await api.createCase(formData);
        router.push(`/cases/${createdCase.case_id}`);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to submit invoice intake.');
      setLoading(false);
      setProgressMsg(null);
    }
  };

  const formattedAmount = (() => {
    const num = parseFloat(totalAmount);
    if (isNaN(num)) return '₹0.00';
    return `₹${num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  })();

  const isGstinFormatValid = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/.test(gstin.trim());

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
          <div className="flex items-center justify-between">
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
              Supplier Invoice Intake
            </h1>
            {isDemo && (
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-500 border border-amber-500/30 font-semibold">
                DEMO DATA
              </span>
            )}
          </div>
          <p className="text-xs sm:text-sm text-zinc-500 dark:text-zinc-400 mt-1 max-w-xl leading-relaxed">
            Upload accounts payable invoices (PDF, PNG, JPEG) for multi-layer extraction (QR, Text, LLM) or populate claims for autonomous due-diligence verification.
          </p>
        </div>

        {/* Collapsible Demo Presets Section */}
        <div className="border border-zinc-200 dark:border-zinc-800 rounded-xl overflow-hidden bg-zinc-50/50 dark:bg-zinc-900/20">
          <button
            type="button"
            onClick={() => setPresetsOpen(!presetsOpen)}
            className="w-full px-4 py-3 flex items-center justify-between text-left text-xs font-semibold text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100/60 dark:hover:bg-zinc-800/40 transition"
          >
            <div className="flex items-center space-x-2">
              <span className="px-1.5 py-0.5 text-[10px] font-mono font-bold rounded bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-400 border border-amber-300 dark:border-amber-800">
                DEMO DATA
              </span>
              <span>Demo Scenarios (Synthetic Benchmark Fixtures)</span>
            </div>
            <ChevronDown className={`h-4 w-4 text-zinc-400 transition-transform ${presetsOpen ? 'rotate-180' : ''}`} />
          </button>

          {presetsOpen && (
            <div className="p-4 pt-1 border-t border-zinc-200 dark:border-zinc-800 space-y-3 bg-white dark:bg-[#0e1420]">
              <p className="text-[11px] text-zinc-500 dark:text-zinc-400">
                Select a preset synthetic scenario for offline evaluation without uploading a real PDF invoice.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={loadBenchmarkPreset}
                  className="p-3 text-left rounded-lg border border-zinc-200 dark:border-zinc-800 hover:border-teal-500 dark:hover:border-teal-500 hover:bg-teal-50/30 dark:hover:bg-teal-950/20 transition-all text-xs"
                >
                  <div className="flex items-center justify-between font-bold text-zinc-900 dark:text-zinc-100">
                    <span className="font-mono">INV-2026-8841</span>
                    <span className="text-[11px] font-mono text-teal-600 dark:text-teal-400">₹4,82,500</span>
                  </div>
                  <div className="text-[11px] font-medium text-zinc-700 dark:text-zinc-300 mt-1">
                    Apex Courier Pvt Ltd
                  </div>
                  <div className="text-[10px] text-zinc-500 dark:text-zinc-400 mt-0.5">
                    Active GSTIN with trade alias discrepancy (Manual Review).
                  </div>
                </button>

                <button
                  type="button"
                  onClick={loadGhostVendorPreset}
                  className="p-3 text-left rounded-lg border border-zinc-200 dark:border-zinc-800 hover:border-rose-500 dark:hover:border-rose-500 hover:bg-rose-50/30 dark:hover:bg-rose-950/20 transition-all text-xs"
                >
                  <div className="flex items-center justify-between font-bold text-zinc-900 dark:text-zinc-100">
                    <span className="font-mono">INV-2026-8842</span>
                    <span className="text-[11px] font-mono text-rose-600 dark:text-rose-400">₹2,95,000</span>
                  </div>
                  <div className="text-[11px] font-medium text-zinc-700 dark:text-zinc-300 mt-1">
                    Specter Cloud Technologies
                  </div>
                  <div className="text-[10px] text-zinc-500 dark:text-zinc-400 mt-0.5">
                    Ghost vendor with zero public registry footprint (Critical Block).
                  </div>
                </button>
              </div>
            </div>
          )}
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
          {/* Multi-file Dropzone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-xl p-6 sm:p-8 text-center transition-all ${
              isDragging
                ? 'border-teal-500 bg-teal-50/30 dark:bg-teal-950/30 scale-[1.01]'
                : 'border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#0e1420] shadow-subtle'
            }`}
          >
            <div className="flex flex-col items-center justify-center space-y-2">
              <div className="w-12 h-12 rounded-full bg-teal-50 dark:bg-teal-950/50 text-teal-600 dark:text-teal-400 flex items-center justify-center mb-1">
                <UploadCloud className="h-6 w-6" />
              </div>
              <div className="text-xs font-semibold text-zinc-900 dark:text-zinc-100">
                Drag and drop vendor invoice files here
              </div>
              <p className="text-[11px] text-zinc-500 dark:text-zinc-400">
                Supports PDF (native e-invoice QR or scanned), PNG, JPG, or JPEG. Multi-file batch intake enabled.
              </p>
              <label className="mt-2 inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium text-teal-700 dark:text-teal-300 bg-teal-50 dark:bg-teal-950/60 border border-teal-200 dark:border-teal-800 cursor-pointer hover:bg-teal-100/50 transition">
                <Files className="h-3.5 w-3.5" />
                <span>Browse Files</span>
                <input
                  type="file"
                  multiple
                  accept=".pdf,.png,.jpg,.jpeg"
                  onChange={handleFileInput}
                  className="hidden"
                />
              </label>
            </div>

            {/* Selected Files List */}
            {files.length > 0 && (
              <div className="mt-5 border-t border-zinc-200 dark:border-zinc-800 pt-4 space-y-2 text-left">
                <div className="text-[11px] font-semibold text-zinc-700 dark:text-zinc-300 flex items-center justify-between">
                  <span>Attached Invoices ({files.length})</span>
                  <button
                    type="button"
                    onClick={() => setFiles([])}
                    className="text-[10px] text-rose-500 hover:underline"
                  >
                    Clear All
                  </button>
                </div>
                <div className="max-h-40 overflow-y-auto space-y-1.5 pr-1">
                  {files.map((f, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between p-2 rounded-lg bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-200 dark:border-zinc-800 text-xs"
                    >
                      <div className="flex items-center space-x-2 truncate">
                        <FileText className="h-4 w-4 text-teal-600 shrink-0" />
                        <span className="font-mono text-zinc-800 dark:text-zinc-200 truncate">{f.name}</span>
                        <span className="text-[10px] text-zinc-400 font-mono">({(f.size / 1024).toFixed(1)} KB)</span>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeFile(i)}
                        className="p-1 text-zinc-400 hover:text-rose-500 transition"
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Optional Claims Metadata / Manual Intake Section */}
          <div className="bg-white dark:bg-[#0e1420] border border-zinc-200/90 dark:border-zinc-800/90 rounded-xl p-5 space-y-4 shadow-subtle">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xs font-semibold text-zinc-900 dark:text-zinc-100">
                  {files.length > 0 ? 'Pre-extraction Overrides (Optional)' : 'Manual Invoice Claims Intake'}
                </h3>
                <p className="text-[11px] text-zinc-500 dark:text-zinc-400">
                  {files.length > 0
                    ? 'Leave blank to let the pipeline extract fields automatically from the uploaded file.'
                    : 'Enter invoice claims manually for evaluation when no physical file is available.'}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                  Supplier / Vendor Name {files.length === 0 && <span className="text-rose-500">*</span>}
                </label>
                <input
                  type="text"
                  value={supplierName}
                  onChange={(e) => setSupplierName(e.target.value)}
                  placeholder="e.g. Apex Courier Pvt Ltd"
                  className="w-full px-3 py-2 text-xs rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none focus:ring-1 focus:ring-teal-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                  Supplier GSTIN (15 characters)
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={gstin}
                    onChange={(e) => setGstin(e.target.value.toUpperCase())}
                    placeholder="e.g. 07AAAAA0000A1Z4"
                    maxLength={15}
                    className="w-full px-3 py-2 text-xs font-mono uppercase rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none focus:ring-1 focus:ring-teal-500"
                  />
                  {gstin && (
                    <div className="absolute right-2.5 top-2.5">
                      {isGstinFormatValid ? (
                        <Check className="h-3.5 w-3.5 text-emerald-500" />
                      ) : (
                        <span className="text-[10px] text-amber-500 font-mono">Format Invalid</span>
                      )}
                    </div>
                  )}
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                  Invoice Number
                </label>
                <input
                  type="text"
                  value={invoiceNumber}
                  onChange={(e) => setInvoiceNumber(e.target.value)}
                  placeholder="e.g. INV-2026-8841"
                  className="w-full px-3 py-2 text-xs font-mono rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none focus:ring-1 focus:ring-teal-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                  Gross Invoice Amount (INR)
                </label>
                <div className="relative">
                  <input
                    type="number"
                    step="0.01"
                    value={totalAmount}
                    onChange={(e) => setTotalAmount(e.target.value)}
                    placeholder="e.g. 482500.00"
                    className="w-full px-3 py-2 text-xs font-mono rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none focus:ring-1 focus:ring-teal-500"
                  />
                  {totalAmount && (
                    <span className="absolute right-3 top-2 text-[11px] font-mono text-zinc-400">
                      {formattedAmount}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Progress message during batch upload */}
          {progressMsg && (
            <div className="p-3 rounded-lg bg-teal-50 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-800 text-xs text-teal-800 dark:text-teal-300 font-mono flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-teal-500 animate-pulse" />
              <span>{progressMsg}</span>
            </div>
          )}

          {/* Submit Action */}
          <div className="flex items-center justify-end space-x-3 pt-2">
            <Link
              href="/queue"
              className="px-4 py-2 text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={loading || (files.length === 0 && !supplierName.trim())}
              className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-lg text-xs font-semibold text-white bg-teal-700 hover:bg-teal-600 dark:bg-teal-600 dark:hover:bg-teal-500 transition shadow-sm hover:shadow-teal-500/20 disabled:opacity-50 active:scale-95"
            >
              <span>
                {loading
                  ? 'Processing Intake...'
                  : files.length > 1
                  ? `Upload & Ingest ${files.length} Invoices`
                  : files.length === 1
                  ? 'Upload & Ingest Invoice'
                  : 'Create Verification Case'}
              </span>
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
