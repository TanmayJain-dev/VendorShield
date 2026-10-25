'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '../../lib/api';
import { validateGstinModulo36 } from '../../lib/gstin';
import { DocumentParseResponse } from '../../types/api';
import {
  UploadCloud,
  FileText,
  ArrowRight,
  AlertCircle,
  X,
  ArrowLeft,
  ShieldCheck,
  Sparkles,
  Zap,
  RefreshCw,
  Eye,
  ChevronDown,
  ChevronUp,
  Check,
  Copy,
  Landmark,
  Truck,
  AlertTriangle
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

  // Real-time Extraction States
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractionTelemetry, setExtractionTelemetry] = useState<DocumentParseResponse | null>(null);
  const [showRawText, setShowRawText] = useState(false);
  const [copiedRawText, setCopiedRawText] = useState(false);
  const [missingFields, setMissingFields] = useState<string[]>([]);
  const [isEditing, setIsEditing] = useState(false);
  const [scanStep, setScanStep] = useState<string>('');

  const loadHavellsLivePreset = () => {
    setFile(null);
    setExtractionTelemetry(null);
    setMissingFields([]);
    setSupplierName('Havells Industrial Electricals');
    setGstin('07AAACH0828A1ZE');
    setInvoiceNumber('INV-2026-9901');
    setTotalAmount('498550.00');
    setSelectedScenario('havells');
    setError(null);
  };

  const loadBenchmarkPreset = () => {
    setFile(null);
    setExtractionTelemetry(null);
    setMissingFields([]);
    setSupplierName('Apex Courier');
    setGstin('07AAAAA0000A1Z5');
    setInvoiceNumber('INV-2026-8841');
    setTotalAmount('482500.00');
    setSelectedScenario('benchmark');
    setError(null);
  };

  const loadGhostVendorPreset = () => {
    setFile(null);
    setExtractionTelemetry(null);
    setMissingFields([]);
    setSupplierName('Specter Cloud Technologies');
    setGstin('07AAAAA0000A1Z5');
    setInvoiceNumber('INV-2026-8842');
    setTotalAmount('295000.00');
    setSelectedScenario('ghost');
    setError(null);
  };

  const handleFileProcess = async (selectedFile: File) => {
    // 1. Immediately reset all fields the exact millisecond a file is selected/dropped
    setFile(selectedFile);
    setSelectedScenario(null);
    setError(null);
    setIsExtracting(true);
    setScanStep('Reading document pixels & initializing 300 DPI RapidOCR...');
    setExtractionTelemetry(null);
    setMissingFields([]);
    setSupplierName('');
    setGstin('');
    setInvoiceNumber('');
    setTotalAmount('');

    const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

    try {
      const apiPromise = api.parseDocument(selectedFile);

      await sleep(500);
      setScanStep('Segmenting multi-column vendor & buyer zones...');
      await sleep(500);
      setScanStep('Reconciling statutory GSTN Luhn Modulo-36 & claims...');
      await sleep(350);

      const data = await apiPromise;
      setExtractionTelemetry(data);

      if (data.supplier_name && data.supplier_name !== 'Unknown Supplier') {
        setSupplierName(data.supplier_name);
      }
      if (data.gstin) {
        setGstin(data.gstin);
      }
      if (data.invoice_number) {
        setInvoiceNumber(data.invoice_number);
      }
      if (data.total_amount != null && data.total_amount > 0) {
        setTotalAmount(data.total_amount.toFixed(2));
      } else {
        setTotalAmount('');
      }
      setMissingFields(data.missing_fields || []);
    } catch (err: any) {
      console.error('Document extraction error:', err);
      setError(`Automatic OCR notice: ${err.message || 'Could not parse document'}. You may still verify or manually enter values below.`);
    } finally {
      setIsExtracting(false);
      setScanStep('');
    }
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
      handleFileProcess(e.dataTransfer.files[0]);
    }
  };

  const handleCopyRawText = () => {
    if (!extractionTelemetry?.raw_text_preview) return;
    navigator.clipboard.writeText(extractionTelemetry.raw_text_preview);
    setCopiedRawText(true);
    setTimeout(() => setCopiedRawText(false), 2000);
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
      router.push(`/cases/${createdCase.case_id}?auto=true`);
    } catch (err: any) {
      setError(err.message || 'Failed to submit invoice intake.');
      setLoading(false);
    }
  };

  const parsedTotal = parseFloat(totalAmount) || 0;
  const formattedAmount = parsedTotal > 0
    ? `₹${parsedTotal.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    : '₹0.00';

  const gstinValidation = validateGstinModulo36(gstin);

  return (
    <div className="max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 sm:py-8 animate-reveal-up text-zinc-900 dark:text-zinc-100">
      {/* Top Header */}
      <div className="mb-6">
        <Link
          href="/queue"
          className="inline-flex items-center space-x-1.5 text-xs sm:text-sm text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200 transition-colors mb-2.5 font-medium"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Cases Queue</span>
        </Link>
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-zinc-900 dark:text-zinc-50">
              Supplier Invoice Intake &amp; Pre-Disbursal Gate
            </h1>
            <p className="text-sm sm:text-base text-zinc-500 dark:text-zinc-400 mt-1 max-w-2xl leading-relaxed">
              Autonomous 4-hop forensic audit powered by TinyFish Live Web Agents. Reconciles GSTR-3B filings, NCLT dockets, DGGI enforcement radar, and IndiaMART wholesale prices.
            </p>
          </div>
          <div className="inline-flex items-center gap-2 self-start md:self-auto px-3.5 py-1.5 rounded-full bg-teal-50 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-800 text-xs font-bold text-teal-800 dark:text-teal-300 shrink-0">
            <span className="w-2.5 h-2.5 rounded-full bg-teal-500 animate-pulse"></span>
            <span>TinyFish Live Agent Engine Active</span>
          </div>
        </div>
      </div>

      {/* Main Responsive Grid Layout (5:7 ratio on desktop) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column (5 cols): File Upload & 1-Click Test Scenarios */}
        <div className="lg:col-span-5 space-y-5">
          {/* Source Document Dropzone Card */}
          <div className="bg-white dark:bg-[#0e1420] border border-zinc-200/90 dark:border-zinc-800/90 rounded-2xl p-5 sm:p-6 shadow-subtle space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-zinc-100 dark:border-zinc-800/80">
              <span className="text-sm font-bold text-zinc-900 dark:text-zinc-100">
                Source Invoice Document
              </span>
              <span className="text-xs text-zinc-400 font-mono">PDF, PNG, JPG, WEBP (10MB)</span>
            </div>

            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-xl p-5 sm:p-6 text-center transition-all ${
                isDragging
                  ? 'border-teal-500 bg-teal-50/40 dark:bg-teal-950/40 scale-[1.01]'
                  : 'border-zinc-200 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-900/30 hover:border-zinc-300 dark:hover:border-zinc-700'
              }`}
            >
              {isExtracting ? (
                <div className="py-6 flex flex-col items-center justify-center space-y-3">
                  <div className="w-12 h-12 rounded-xl bg-teal-50 dark:bg-teal-950/50 text-teal-600 dark:text-teal-400 flex items-center justify-center animate-pulse">
                    <RefreshCw className="h-6 w-6 animate-spin" />
                  </div>
                  <div className="space-y-1">
                    <div className="text-sm font-bold text-teal-700 dark:text-teal-300">
                      🔄 {scanStep || 'Extracting invoice telemetry & running Modulo-36 / OCR checks...'}
                    </div>
                    <div className="text-xs text-zinc-500 dark:text-zinc-400 font-mono">
                      RapidOCR ONNX (300 DPI) &bull; Vector Layer Analysis
                    </div>
                  </div>
                </div>
              ) : file ? (
                <div className="flex items-center justify-between p-3.5 rounded-xl bg-teal-50/80 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-800/60">
                  <div className="flex items-center space-x-3 text-left">
                    <div className="w-10 h-10 rounded-lg bg-teal-600 text-white flex items-center justify-center shrink-0">
                      <FileText className="h-5 w-5" />
                    </div>
                    <div className="truncate max-w-[180px] sm:max-w-[220px]">
                      <div className="text-sm font-bold text-zinc-900 dark:text-zinc-100 truncate">{file.name}</div>
                      <div className="text-xs text-zinc-500 dark:text-zinc-400 font-mono">
                        {(file.size / 1024).toFixed(1)} KB &bull; Parsed &amp; Attached
                      </div>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setFile(null);
                      setExtractionTelemetry(null);
                      setMissingFields([]);
                    }}
                    className="p-1.5 rounded-lg text-zinc-400 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
                    title="Remove file"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ) : (
                <div className="space-y-2.5 py-3">
                  <div className="w-12 h-12 rounded-xl bg-teal-50 dark:bg-teal-950/50 text-teal-600 dark:text-teal-400 mx-auto flex items-center justify-center">
                    <UploadCloud className="h-6 w-6 stroke-[1.8]" />
                  </div>
                  <div className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
                    Drop vendor invoice (PDF, JPG, PNG) here, or{' '}
                    <label className="text-teal-600 dark:text-teal-400 hover:underline cursor-pointer font-bold">
                      browse files
                      <input
                        type="file"
                        accept=".pdf,.png,.jpg,.jpeg,.webp"
                        onChange={(e) => e.target.files && e.target.files[0] && handleFileProcess(e.target.files[0])}
                        className="hidden"
                      />
                    </label>
                  </div>
                  <div className="text-xs text-zinc-400 font-sans">
                    Supports PDFs, high-res scans, or smartphone invoice photos up to 10MB
                  </div>
                </div>
              )}
            </div>

            {/* Extracted Document Telemetry Drawer */}
            {extractionTelemetry && (
              <div className="p-4 rounded-xl bg-teal-50/60 dark:bg-teal-950/20 border border-teal-200/80 dark:border-teal-800/60 space-y-3 animate-reveal-up text-xs">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-teal-500 animate-pulse" />
                    <span className="font-bold text-teal-900 dark:text-teal-200 text-sm">
                      Extracted Document Telemetry
                    </span>
                  </div>
                  <span className="px-2.5 py-0.5 rounded-md font-mono text-[11px] font-bold bg-teal-100 dark:bg-teal-900/60 text-teal-800 dark:text-teal-300">
                    {extractionTelemetry.extraction_method === 'PYMUPDF_TEXT'
                      ? 'PyMuPDF Text Engine'
                      : 'RapidOCR ONNX (300 DPI)'}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-zinc-700 dark:text-zinc-300">
                  <div className="bg-white/80 dark:bg-zinc-900/80 p-2.5 rounded-lg border border-teal-100 dark:border-teal-900/40">
                    <div className="text-[10px] uppercase font-bold text-zinc-400">Extraction Quality</div>
                    <div className="font-bold text-emerald-600 dark:text-emerald-400 font-mono mt-0.5">
                      {(extractionTelemetry.extraction_confidence * 100).toFixed(0)}% Certified
                    </div>
                  </div>
                  <div className="bg-white/80 dark:bg-zinc-900/80 p-2.5 rounded-lg border border-teal-100 dark:border-teal-900/40">
                    <div className="text-[10px] uppercase font-bold text-zinc-400">Modulo-36 Checksum</div>
                    <div className="font-bold font-mono mt-0.5 truncate">
                      {gstinValidation.valid ? (
                        <span className="text-emerald-600 dark:text-emerald-400">Verified Valid</span>
                      ) : (
                        <span className="text-rose-600 dark:text-rose-400" title={gstinValidation.reason}>
                          Invalid / Checksum Failed
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Forensic Document Anomaly Callout */}
                {(extractionTelemetry.forensic_anomaly ||
                  extractionTelemetry.buyer_gstin ||
                  extractionTelemetry.gstin_format_valid === false ||
                  !gstinValidation.valid ||
                  extractionTelemetry.total_amount == null ||
                  extractionTelemetry.total_amount === 0) && (
                  <div className="p-3 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/80 text-amber-900 dark:text-amber-200 space-y-1.5">
                    <div className="flex items-center gap-1.5 font-bold text-xs text-amber-800 dark:text-amber-300">
                      <AlertTriangle className="h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />
                      <span>Forensic Document Anomaly</span>
                    </div>
                    <div className="text-[11px] leading-relaxed text-amber-800/90 dark:text-amber-300/90 space-y-1">
                      {extractionTelemetry.forensic_anomaly ? (
                        <p>{extractionTelemetry.forensic_anomaly}</p>
                      ) : (
                        <>
                          {!gstinValidation.valid && (
                            <p>&bull; Supplier GSTIN &lsquo;{gstin || 'None'}&rsquo; is structurally invalid ({gstinValidation.reason}).</p>
                          )}
                          {extractionTelemetry.buyer_gstin && (
                            <p>&bull; Client/Buyer distinguished: {extractionTelemetry.buyer_name || 'Client'} (GSTIN: {extractionTelemetry.buyer_gstin}).</p>
                          )}
                          {(extractionTelemetry.total_amount == null || extractionTelemetry.total_amount === 0) && (
                            <p>&bull; Invoice Total / Grand Total is blank on document &mdash; manual amount required.</p>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                )}

                {/* Extracted Metadata Fields */}
                <div className="bg-white/80 dark:bg-zinc-900/80 p-2.5 rounded-lg border border-teal-100 dark:border-teal-900/40 space-y-1.5">
                  {extractionTelemetry.line_items && extractionTelemetry.line_items.length > 0 && (
                    <div className="text-zinc-800 dark:text-zinc-200 font-medium truncate">
                      <span className="text-zinc-400 font-bold">Item: </span>
                      {extractionTelemetry.line_items[0].description} ({extractionTelemetry.line_items[0].quantity} @ ₹{extractionTelemetry.line_items[0].unit_price.toLocaleString('en-IN')})
                    </div>
                  )}
                  {extractionTelemetry.ifsc_code && (
                    <div className="text-zinc-800 dark:text-zinc-200 font-mono text-[11px] flex items-center gap-1.5">
                      <Landmark className="h-3.5 w-3.5 text-teal-600 dark:text-teal-400 shrink-0" />
                      <span>{extractionTelemetry.ifsc_code} {extractionTelemetry.bank_account_masked ? `• ${extractionTelemetry.bank_account_masked}` : ''}</span>
                    </div>
                  )}
                  {extractionTelemetry.eway_bill_no && (
                    <div className="text-zinc-800 dark:text-zinc-200 font-mono text-[11px] flex items-center gap-1.5">
                      <Truck className="h-3.5 w-3.5 text-teal-600 dark:text-teal-400 shrink-0" />
                      <span>e-Way Bill: {extractionTelemetry.eway_bill_no}</span>
                    </div>
                  )}
                </div>

                {/* Collapsible Raw Text / OCR Preview */}
                {extractionTelemetry.raw_text_preview && (
                  <div className="pt-1">
                    <div className="flex items-center justify-between">
                      <button
                        type="button"
                        onClick={() => setShowRawText(!showRawText)}
                        className="flex items-center gap-1.5 text-xs font-semibold text-teal-800 dark:text-teal-300 hover:underline cursor-pointer"
                      >
                        <Eye className="h-3.5 w-3.5" />
                        <span>{showRawText ? 'Hide Raw Text / OCR Snippet' : 'View Extracted Raw Text / OCR Preview'}</span>
                        {showRawText ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                      </button>

                      {showRawText && (
                        <button
                          type="button"
                          onClick={handleCopyRawText}
                          className="flex items-center gap-1 text-[11px] font-semibold text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200"
                        >
                          {copiedRawText ? <Check className="h-3 w-3 text-emerald-500" /> : <Copy className="h-3 w-3" />}
                          <span>{copiedRawText ? 'Copied' : 'Copy'}</span>
                        </button>
                      )}
                    </div>

                    {showRawText && (
                      <div className="mt-2 p-3 bg-zinc-900 text-zinc-200 rounded-lg font-mono text-[11px] leading-relaxed max-h-40 overflow-y-auto">
                        <pre className="whitespace-pre-wrap font-mono">{extractionTelemetry.raw_text_preview}</pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* 1-Click Enterprise Audit Scenarios */}
          <div className="bg-white dark:bg-[#0e1420] border border-zinc-200/90 dark:border-zinc-800/90 rounded-2xl p-5 sm:p-6 shadow-subtle space-y-3.5">
            <div className="flex items-center justify-between pb-3 border-b border-zinc-100 dark:border-zinc-800/80">
              <div>
                <span className="text-sm font-bold text-zinc-900 dark:text-zinc-100 block">
                  1-Click Enterprise Scenarios
                </span>
                <span className="text-xs text-zinc-400">Preload verified forensic benchmark cases</span>
              </div>
              <span className="text-xs font-mono font-semibold px-2.5 py-0.5 rounded-md bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300">
                Live SSE
              </span>
            </div>

            <div className="space-y-3">
              {/* Scenario 0: Havells Live Enterprise Preset */}
              <button
                type="button"
                onClick={loadHavellsLivePreset}
                className={`w-full p-3.5 text-left rounded-xl border transition-all relative ${
                  selectedScenario === 'havells'
                    ? 'border-indigo-600 dark:border-indigo-500 bg-indigo-50/60 dark:bg-indigo-950/30 ring-2 ring-indigo-500/30 shadow-sm'
                    : 'border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800/40'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-zinc-900 dark:text-zinc-100">INV-2026-9901</span>
                  <span className="text-sm font-mono font-extrabold text-indigo-700 dark:text-indigo-400">₹4,98,550</span>
                </div>
                <div className="text-sm font-bold text-zinc-900 dark:text-zinc-100 mt-1">Havells India Ltd</div>
                <div className="text-xs text-zinc-500 dark:text-zinc-400 mt-1 leading-snug">
                  Real GSTIN (07AAACH0828A1ZE) + IndiaMART copper cable benchmark.
                </div>
              </button>

              {/* Scenario 1: Apex Courier Benchmark */}
              <button
                type="button"
                onClick={loadBenchmarkPreset}
                className={`w-full p-3.5 text-left rounded-xl border transition-all relative ${
                  selectedScenario === 'benchmark'
                    ? 'border-teal-600 dark:border-teal-500 bg-teal-50/60 dark:bg-teal-950/30 ring-2 ring-teal-500/30 shadow-sm'
                    : 'border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800/40'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-zinc-900 dark:text-zinc-100">INV-2026-8841</span>
                  <span className="text-sm font-mono font-extrabold text-teal-700 dark:text-teal-400">₹4,82,500</span>
                </div>
                <div className="text-sm font-bold text-zinc-900 dark:text-zinc-100 mt-1">Apex Courier Pvt Ltd</div>
                <div className="text-xs text-zinc-500 dark:text-zinc-400 mt-1 leading-snug">
                  Trade alias discrepancy &amp; MSME 43B(h) Split Escrow hold.
                </div>
              </button>

              {/* Scenario 2: Specter Cloud Ghost Vendor */}
              <button
                type="button"
                onClick={loadGhostVendorPreset}
                className={`w-full p-3.5 text-left rounded-xl border transition-all relative ${
                  selectedScenario === 'ghost'
                    ? 'border-rose-600 dark:border-rose-500 bg-rose-50/60 dark:bg-rose-950/30 ring-2 ring-rose-500/30 shadow-sm'
                    : 'border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800/40'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-zinc-900 dark:text-zinc-100">INV-2026-8842</span>
                  <span className="text-sm font-mono font-extrabold text-rose-700 dark:text-rose-400">₹2,95,000</span>
                </div>
                <div className="text-sm font-bold text-zinc-900 dark:text-zinc-100 mt-1">Specter Cloud Shell</div>
                <div className="text-xs text-zinc-500 dark:text-zinc-400 mt-1 leading-snug">
                  NCLT petition &amp; 38-firm ghost hub (Forensic Freeze).
                </div>
              </button>
            </div>
          </div>

          {/* Autonomous Telemetry Pipeline Guide */}
          <div className="bg-zinc-50/90 dark:bg-zinc-900/50 border border-zinc-200/90 dark:border-zinc-800/90 rounded-2xl p-4.5 text-xs space-y-2.5 text-zinc-600 dark:text-zinc-400">
            <div className="font-bold text-sm text-zinc-800 dark:text-zinc-200 flex items-center space-x-2">
              <Sparkles className="h-4 w-4 text-teal-600 dark:text-teal-400" />
              <span>TinyFish 4-Hop Autonomous Pipeline</span>
            </div>
            <div className="grid grid-cols-2 gap-2.5 text-xs pt-1 font-mono">
              <div className="flex items-center space-x-1.5 text-zinc-700 dark:text-zinc-300 font-medium">
                <span className="w-2 h-2 rounded-full bg-teal-500"></span>
                <span>1. GSTN Velocity</span>
              </div>
              <div className="flex items-center space-x-1.5 text-zinc-700 dark:text-zinc-300 font-medium">
                <span className="w-2 h-2 rounded-full bg-teal-500"></span>
                <span>2. MCA Shell Network</span>
              </div>
              <div className="flex items-center space-x-1.5 text-zinc-700 dark:text-zinc-300 font-medium">
                <span className="w-2 h-2 rounded-full bg-teal-500"></span>
                <span>3. DGGI Radar</span>
              </div>
              <div className="flex items-center space-x-1.5 text-zinc-700 dark:text-zinc-300 font-medium">
                <span className="w-2 h-2 rounded-full bg-teal-500"></span>
                <span>4. IndiaMART Benchmarks</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column (7 cols): Invoice Claim Parameters & Pre-Disbursal Projection */}
        <div className="lg:col-span-7 space-y-5">
          <div className="bg-white dark:bg-[#0e1420] border border-zinc-200/90 dark:border-zinc-800/90 rounded-2xl p-6 sm:p-7 shadow-subtle space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-zinc-100 dark:border-zinc-800/80">
              <div>
                <h2 className="text-base sm:text-lg font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
                  <span>{file ? 'Extracted Invoice Credentials' : 'Invoice Claim Parameters'}</span>
                  {file && (
                    <span className="text-[10px] uppercase font-mono font-bold px-2 py-0.5 rounded bg-teal-100 dark:bg-teal-950 text-teal-800 dark:text-teal-300 border border-teal-300 dark:border-teal-800">
                      AI Extracted
                    </span>
                  )}
                </h2>
                <p className="text-xs sm:text-sm text-zinc-500 dark:text-zinc-400 mt-0.5">
                  {file ? 'Autonomous telemetry extracted from document — zero manual entry required' : 'Declared supplier details & statutory billing credentials'}
                </p>
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                <button
                  type="button"
                  onClick={() => setIsEditing(!isEditing)}
                  className="px-3 py-1 rounded-lg text-xs font-semibold border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-700 transition cursor-pointer flex items-center gap-1.5"
                >
                  <span>{isEditing ? '✓ Lock Credentials' : '✏️ Override Values'}</span>
                </button>
                <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/60 text-xs font-semibold text-emerald-700 dark:text-emerald-400">
                  <ShieldCheck className="h-4 w-4" />
                  <span>Pre-Disbursal Gated</span>
                </div>
              </div>
            </div>

            {/* Error Alert */}
            {error && (
              <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/60 text-sm text-rose-800 dark:text-rose-300 flex items-center space-x-2.5 font-medium">
                <AlertCircle className="h-5 w-5 shrink-0 text-rose-600" />
                <span>{error}</span>
              </div>
            )}

            {/* Forensic Anomaly Callout (e.g. malformed supplier GST or buyer GST separation) */}
            {extractionTelemetry?.forensic_anomaly && (
              <div className="p-4 rounded-xl bg-amber-50/80 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/60 space-y-1.5">
                <div className="flex items-center gap-2 text-xs font-bold text-amber-900 dark:text-amber-200">
                  <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0" />
                  <span>Forensic Discrepancy Flagged</span>
                </div>
                <p className="text-xs text-amber-800 dark:text-amber-300 leading-relaxed font-mono">
                  {extractionTelemetry.forensic_anomaly}
                </p>
              </div>
            )}

            {/* Form Fields vs Autonomous Verified Display */}
            <form onSubmit={handleSubmit} className="space-y-6">
              {!isEditing ? (
                /* Autonomous Read-Only Credential Cards */
                <div className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                    {/* Card 1: Supplier Name */}
                    <div className="p-4 rounded-xl bg-zinc-50/80 dark:bg-zinc-900/80 border border-zinc-200/90 dark:border-zinc-800/90 space-y-1">
                      <span className="text-[11px] font-bold text-zinc-400 uppercase tracking-wider block">
                        Supplier / Billed By
                      </span>
                      <div className="font-bold text-base text-zinc-900 dark:text-zinc-100 truncate">
                        {supplierName || <span className="text-amber-500 text-sm italic">Not detected on scan</span>}
                      </div>
                      <span className="text-xs text-zinc-500">Autonomous Trade Name Detection</span>
                    </div>

                    {/* Card 2: Supplier GSTIN & Modulo-36 Badge */}
                    <div className="p-4 rounded-xl bg-zinc-50/80 dark:bg-zinc-900/80 border border-zinc-200/90 dark:border-zinc-800/90 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] font-bold text-zinc-400 uppercase tracking-wider block">
                          Supplier GSTIN
                        </span>
                        {gstin && (
                          gstinValidation.valid ? (
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                              ✓ Valid Modulo-36
                            </span>
                          ) : (
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-rose-50 text-rose-700 dark:bg-rose-950 dark:text-rose-300 border border-rose-200 dark:border-rose-800">
                              ⚠️ Checksum Mismatch
                            </span>
                          )
                        )}
                      </div>
                      <div className="font-mono font-bold text-base text-zinc-900 dark:text-zinc-100 tracking-wide">
                        {gstin || <span className="text-amber-500 text-sm italic">Not detected</span>}
                      </div>
                      <span className="text-xs text-zinc-500 font-mono">15-Digit Statutory Identifier</span>
                    </div>

                    {/* Card 3: Invoice Reference */}
                    <div className="p-4 rounded-xl bg-zinc-50/80 dark:bg-zinc-900/80 border border-zinc-200/90 dark:border-zinc-800/90 space-y-1">
                      <span className="text-[11px] font-bold text-zinc-400 uppercase tracking-wider block">
                        Invoice Reference
                      </span>
                      <div className="font-mono font-bold text-base text-zinc-900 dark:text-zinc-100 truncate">
                        {invoiceNumber || <span className="text-amber-500 text-sm italic">INV-UNKNOWN</span>}
                      </div>
                      <span className="text-xs text-zinc-500">Tax Invoice Number</span>
                    </div>

                    {/* Card 4: Total Invoiced Amount */}
                    <div className="p-4 rounded-xl bg-zinc-50/80 dark:bg-zinc-900/80 border border-zinc-200/90 dark:border-zinc-800/90 space-y-1">
                      <span className="text-[11px] font-bold text-zinc-400 uppercase tracking-wider block">
                        Claimed Gross Value
                      </span>
                      {parsedTotal > 0 ? (
                        <div className="font-mono font-extrabold text-lg text-emerald-600 dark:text-emerald-400">
                          {formattedAmount}
                        </div>
                      ) : (
                        <div className="flex items-center gap-2 pt-1">
                          <input
                            type="number"
                            step="0.01"
                            value={totalAmount}
                            onChange={(e) => setTotalAmount(e.target.value)}
                            placeholder="Enter amount (INR)"
                            className="w-full px-2.5 py-1 text-xs font-mono rounded bg-white dark:bg-zinc-950 border border-amber-400 focus:outline-none"
                          />
                        </div>
                      )}
                      <span className="text-xs text-zinc-500">
                        {parsedTotal > 0 ? 'Pre-Disbursal Base & Tax Sum' : '⚠️ Blank on invoice — enter to gate'}
                      </span>
                    </div>
                  </div>

                  {/* Detected Buyer / Client Context Pill */}
                  {(extractionTelemetry?.buyer_name || extractionTelemetry?.buyer_gstin) && (
                    <div className="p-3 rounded-lg bg-zinc-100/70 dark:bg-zinc-900/60 border border-zinc-200/80 dark:border-zinc-800/80 flex items-center justify-between text-xs text-zinc-600 dark:text-zinc-400">
                      <span>
                        <strong className="text-zinc-700 dark:text-zinc-300">Billed To (Client):</strong> {extractionTelemetry.buyer_name || 'Client'}
                      </span>
                      {extractionTelemetry.buyer_gstin && (
                        <span className="font-mono text-[11px] font-semibold text-zinc-500">
                          GSTIN: {extractionTelemetry.buyer_gstin}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              ) : (
                /* Editable Mode (Expanded for Manual Auditor Override) */
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 text-sm p-4 rounded-xl bg-zinc-50/40 dark:bg-zinc-900/40 border border-zinc-200/80 dark:border-zinc-800/80">
                  {/* Supplier Name */}
                  <div className="space-y-2">
                    <label className="block text-zinc-800 dark:text-zinc-200 font-bold text-sm">
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
                      className="w-full px-4 py-3 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 font-medium text-sm transition-colors shadow-xs"
                      placeholder="e.g. Havells India Ltd"
                    />
                  </div>

                  {/* Supplier GSTIN */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="block text-zinc-800 dark:text-zinc-200 font-bold text-sm">
                        Supplier GSTIN <span className="text-rose-500">*</span>
                      </label>
                      <span className="text-xs text-zinc-400 font-mono font-semibold">
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
                        className="w-full px-4 py-3 font-mono uppercase bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 font-bold text-sm transition-colors shadow-xs"
                        placeholder="07AAACH0828A1ZE"
                      />
                      {gstin.length === 15 && (
                        <div className="absolute right-3 top-1/2 -translate-y-1/2">
                          {gstinValidation.valid ? (
                            <span className="text-xs font-bold px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/60 flex items-center gap-1">
                              ✓ Valid Modulo-36
                            </span>
                          ) : (
                            <span className="text-xs font-bold px-2 py-0.5 rounded bg-rose-50 dark:bg-rose-950/60 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-800/60 flex items-center gap-1" title={gstinValidation.reason}>
                              ⚠️ Checksum Mismatch
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Invoice Number */}
                  <div className="space-y-2">
                    <label className="block text-zinc-800 dark:text-zinc-200 font-bold text-sm">
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
                      className="w-full px-4 py-3 font-mono bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 font-medium text-sm transition-colors shadow-xs"
                      placeholder="INV-2026-9901"
                    />
                  </div>

                  {/* Total Amount */}
                  <div className="space-y-2">
                    <label className="block text-zinc-800 dark:text-zinc-200 font-bold text-sm">
                      Total Payable Amount (INR) <span className="text-rose-500">*</span>
                    </label>
                    <div className="relative">
                      <span className="absolute left-4 top-1/2 -translate-y-1/2 font-mono text-zinc-400 text-sm font-semibold">
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
                        className="w-full pl-9 pr-4 py-3 font-mono bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 font-bold text-sm tabular-nums transition-colors shadow-xs"
                        placeholder="498550.00"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Real-time Dynamic Split-Settlement Routing Preview */}
              <div className="p-4 sm:p-5 rounded-2xl bg-zinc-50 dark:bg-[#090d16] border border-zinc-200/90 dark:border-zinc-800/90 space-y-3.5">
                <div className="flex items-center justify-between text-xs sm:text-sm">
                  <span className="font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
                    <Zap className="h-4 w-4 text-amber-500" />
                    <span>Projected Pre-Disbursal Settlement Routing</span>
                  </span>
                  <span className="text-xs font-mono font-semibold text-zinc-500 dark:text-zinc-400">
                    2026 GSTN IMS Model
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3.5 pt-1">
                  <div className="p-3.5 rounded-xl bg-white dark:bg-zinc-900/90 border border-zinc-200/90 dark:border-zinc-800/90">
                    <div className="text-xs text-zinc-500 dark:text-zinc-400 font-semibold">Safe Base Disbursal (82%)</div>
                    <div className="text-base sm:text-xl font-extrabold font-mono text-emerald-600 dark:text-emerald-400 mt-1">
                      ₹{(parsedTotal * 0.82).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                    <div className="text-xs text-zinc-400 mt-1">Immediate wire disbursal</div>
                  </div>

                  <div className="p-3.5 rounded-xl bg-white dark:bg-zinc-900/90 border border-zinc-200/90 dark:border-zinc-800/90">
                    <div className="text-xs text-zinc-500 dark:text-zinc-400 font-semibold">Contingent GST Escrow (18%)</div>
                    <div className="text-base sm:text-xl font-extrabold font-mono text-amber-600 dark:text-amber-400 mt-1">
                      ₹{(parsedTotal * 0.18).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                    <div className="text-xs text-zinc-400 mt-1">Auto-released on GSTR-2B reflection</div>
                  </div>
                </div>
              </div>

              {/* Submit & Cancel Actions */}
              <div className="flex items-center justify-between pt-2">
                <Link
                  href="/queue"
                  className="text-xs sm:text-sm text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200 font-medium transition-colors"
                >
                  Cancel and Return
                </Link>

                <button
                  type="submit"
                  disabled={loading || isExtracting}
                  className="group inline-flex items-center space-x-2 px-6 py-3 rounded-xl text-xs sm:text-sm font-bold text-white bg-teal-700 hover:bg-teal-600 dark:bg-teal-600 dark:hover:bg-teal-500 transition-all duration-200 shadow-md hover:shadow-teal-500/20 active:scale-95 disabled:opacity-50 cursor-pointer"
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
