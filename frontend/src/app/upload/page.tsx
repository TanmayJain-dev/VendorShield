'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '../../lib/api';
import { UploadCloud, FileText, ArrowRight, ShieldCheck, Check } from 'lucide-react';

export default function IntakePage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [supplierName, setSupplierName] = useState('Apex Courier');
  const [gstin, setGstin] = useState('07AAAAA0000A1Z5');
  const [invoiceNumber, setInvoiceNumber] = useState('INV-2026-8841');
  const [totalAmount, setTotalAmount] = useState('482500.00');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadBenchmarkPreset = () => {
    setSupplierName('Apex Courier');
    setGstin('07AAAAA0000A1Z5');
    setInvoiceNumber('INV-2026-8841');
    setTotalAmount('482500.00');
  };

  const loadGhostVendorPreset = () => {
    setSupplierName('Specter Cloud Technologies');
    setGstin('07AAAAA0000A1Z5');
    setInvoiceNumber('INV-2026-8842');
    setTotalAmount('295000.00');
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
      setError(err.message || 'Failed to submit invoice intake');
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="border-b border-slate-800 pb-4">
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <UploadCloud className="h-5 w-5 text-cyan-400" />
          <span>Supplier Invoice Intake &amp; Claim Extraction</span>
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Upload an invoice PDF or populate claims. Claims will be reconciled against public registries via TinyFish.
        </p>
      </div>

      {/* Preset Quick Load */}
      <div className="bg-[#0f172a]/60 border border-slate-800/80 rounded-lg p-3.5 flex flex-wrap items-center justify-between gap-3 text-xs">
        <span className="text-slate-400 font-mono text-[11px] uppercase tracking-wider">
          Quick Demo Presets:
        </span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={loadBenchmarkPreset}
            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 rounded font-mono text-[11px] transition"
          >
            INV-2026-8841 (Apex Courier)
          </button>
          <button
            type="button"
            onClick={loadGhostVendorPreset}
            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-amber-300 border border-slate-700 rounded font-mono text-[11px] transition"
          >
            INV-2026-8842 (Ghost Vendor)
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Upload Dropzone */}
        <div className="border-2 border-dashed border-slate-700/80 hover:border-cyan-500/60 rounded-xl p-8 text-center bg-[#0d1322]/40 transition">
          <FileText className="h-10 w-10 text-cyan-400/80 mx-auto mb-3" />
          <p className="text-xs font-semibold text-slate-200">
            {file ? file.name : 'Drag and drop supplier invoice PDF here'}
          </p>
          <p className="text-[11px] text-slate-400 mt-1">
            Supports digital PDF text and scanned receipts (PyMuPDF / OCR)
          </p>
          <input
            type="file"
            accept=".pdf,.png,.jpg,.jpeg"
            onChange={(e) => e.target.files && setFile(e.target.files[0])}
            className="mt-4 text-xs text-slate-400 file:mr-4 file:py-1.5 file:px-3 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-cyan-950 file:text-cyan-400 hover:file:bg-cyan-900 cursor-pointer"
          />
        </div>

        {/* Claim Fields Editor */}
        <div className="bg-[#0f172a]/70 border border-slate-800 rounded-lg p-5 space-y-4">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-300 font-mono">
            Extracted Invoice Claims (Reviewer Correctable)
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block text-slate-400 mb-1 font-mono text-[11px]">
                Supplier Trade Name *
              </label>
              <input
                type="text"
                required
                value={supplierName}
                onChange={(e) => setSupplierName(e.target.value)}
                className="w-full bg-[#0b0f19] border border-slate-700 rounded px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1 font-mono text-[11px]">
                Supplier GSTIN (15-char)
              </label>
              <input
                type="text"
                value={gstin}
                onChange={(e) => setGstin(e.target.value.toUpperCase())}
                placeholder="07AAAAA0000A1Z5"
                className="w-full bg-[#0b0f19] border border-slate-700 rounded px-3 py-2 text-white font-mono focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1 font-mono text-[11px]">
                Invoice Number *
              </label>
              <input
                type="text"
                required
                value={invoiceNumber}
                onChange={(e) => setInvoiceNumber(e.target.value)}
                className="w-full bg-[#0b0f19] border border-slate-700 rounded px-3 py-2 text-white font-mono focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1 font-mono text-[11px]">
                Invoice Total Amount (₹) *
              </label>
              <input
                type="number"
                step="0.01"
                required
                value={totalAmount}
                onChange={(e) => setTotalAmount(e.target.value)}
                className="w-full bg-[#0b0f19] border border-slate-700 rounded px-3 py-2 text-white font-mono focus:outline-none focus:border-cyan-500"
              />
            </div>
          </div>
        </div>

        {error && (
          <div className="p-3 bg-rose-950/60 border border-rose-800 rounded text-rose-300 text-xs">
            {error}
          </div>
        )}

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={loading}
            className="flex items-center gap-2 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold px-5 py-2.5 rounded-lg text-xs transition disabled:opacity-50"
          >
            <span>{loading ? 'Processing Intake...' : 'Proceed to Research Dossier'}</span>
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </form>
    </div>
  );
}
