'use client';

import { useState, useEffect, useRef } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  FileText,
  Database,
  Globe,
  Building2,
  Lock,
  ArrowRight,
  Sparkles,
  CheckCircle2,
  XCircle,
  HelpCircle
} from 'lucide-react';

type OutcomeState = 'PASS' | 'REVIEW' | 'BLOCK';

export function Hero3DScene() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [rotateX, setRotateX] = useState(10);
  const [rotateY, setRotateY] = useState(-12);
  const [activeOutcome, setActiveOutcome] = useState<OutcomeState>('PASS');
  const [isHovered, setIsHovered] = useState(false);
  const [pulseTick, setPulseTick] = useState(0);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Smooth mouse parallax interpolation (respects prefers-reduced-motion)
  useEffect(() => {
    if (typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setRotateX(0);
      setRotateY(0);
      return;
    }

    let targetX = 10;
    let targetY = -12;
    let currentX = 10;
    let currentY = -12;
    let animationFrameId: number;

    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      const normX = (x / rect.width - 0.5) * 2;
      const normY = (y / rect.height - 0.5) * 2;

      // Soft constrained angle bounds for realistic depth
      targetY = -12 + normX * 18;
      targetX = 10 - normY * 16;
    };

    const handleMouseLeave = () => {
      targetX = 10;
      targetY = -12;
    };

    const container = containerRef.current;
    if (container) {
      container.addEventListener('mousemove', handleMouseMove);
      container.addEventListener('mouseleave', handleMouseLeave);
    }

    const animate = () => {
      currentX += (targetX - currentX) * 0.08;
      currentY += (targetY - currentY) * 0.08;
      setRotateX(currentX);
      setRotateY(currentY);
      animationFrameId = requestAnimationFrame(animate);
    };

    animationFrameId = requestAnimationFrame(animate);

    return () => {
      if (container) {
        container.removeEventListener('mousemove', handleMouseMove);
        container.removeEventListener('mouseleave', handleMouseLeave);
      }
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  // Idle tick for subtle conduit pulse animation
  useEffect(() => {
    const interval = setInterval(() => {
      setPulseTick((prev) => (prev + 1) % 100);
    }, 45);
    return () => clearInterval(interval);
  }, []);

  // Preset outcome data strictly mapped to semantic Green / Amber / Red
  const outcomeData = {
    PASS: {
      score: 12,
      label: 'PASS',
      headline: 'Low Risk — Safe to Release Payment',
      desc: 'All invoice claims match official GST & MCA registries with checksum verification.',
      badgeClass: 'bg-emerald-50 text-emerald-800 border-emerald-300 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-700/60',
      dotColor: 'bg-emerald-500',
      strokeColor: '#10b981',
      glow: 'from-emerald-500/20 via-teal-500/10 to-transparent',
      shieldBorder: 'border-emerald-500/60 dark:border-emerald-400/60',
      shieldGlow: '0 25px 60px -12px rgba(16, 185, 129, 0.45)',
      gstStatus: 'ACTIVE & MATCHED',
      gstStatusColor: 'text-emerald-600 dark:text-emerald-400',
      mcaStatus: 'VERIFIED ENTITY',
      mcaStatusColor: 'text-emerald-600 dark:text-emerald-400',
      webStatus: 'DOMAIN ALIGNED (6.2 yrs)',
      webStatusColor: 'text-emerald-600 dark:text-emerald-400'
    },
    REVIEW: {
      score: 48,
      label: 'MANUAL REVIEW',
      headline: 'Discrepancy Detected — Requires Human Sign-off',
      desc: 'Invoice trade name differs from legal entity filing. First invoice with modified bank IFSC.',
      badgeClass: 'bg-amber-50 text-amber-800 border-amber-300 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-700/60',
      dotColor: 'bg-amber-500',
      strokeColor: '#f59e0b',
      glow: 'from-amber-500/20 via-orange-500/10 to-transparent',
      shieldBorder: 'border-amber-500/60 dark:border-amber-400/60',
      shieldGlow: '0 25px 60px -12px rgba(245, 158, 11, 0.45)',
      gstStatus: 'ACTIVE (TRADE ALIAS)',
      gstStatusColor: 'text-amber-600 dark:text-amber-400',
      mcaStatus: 'NAME VARIATION FOUND',
      mcaStatusColor: 'text-amber-600 dark:text-amber-400',
      webStatus: 'PARTIAL ADDRESS MATCH',
      webStatusColor: 'text-amber-600 dark:text-amber-400'
    },
    BLOCK: {
      score: 84,
      label: 'CRITICAL BLOCK',
      headline: 'High ITC Risk — Payment Execution Halted',
      desc: 'Cancelled GSTIN / suspicious shell footprint. Tax credit clawback guaranteed if paid.',
      badgeClass: 'bg-rose-50 text-rose-800 border-rose-300 dark:bg-rose-950/40 dark:text-rose-300 dark:border-rose-700/60',
      dotColor: 'bg-rose-500',
      strokeColor: '#f43f5e',
      glow: 'from-rose-500/25 via-red-500/10 to-transparent',
      shieldBorder: 'border-rose-500/60 dark:border-rose-400/60',
      shieldGlow: '0 25px 60px -12px rgba(244, 63, 94, 0.45)',
      gstStatus: 'CANCELLED / SUSPENDED',
      gstStatusColor: 'text-rose-600 dark:text-rose-400',
      mcaStatus: 'STRIKE-OFF PROCEEDING',
      mcaStatusColor: 'text-rose-600 dark:text-rose-400',
      webStatus: 'ANONYMOUS WHOIS (<30d)',
      webStatusColor: 'text-rose-600 dark:text-rose-400'
    }
  };

  const current = outcomeData[activeOutcome];

  return (
    <div
      ref={containerRef}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className="relative w-full max-w-[620px] aspect-[4/3.7] mx-auto select-none flex items-center justify-center py-2 transition-all"
      style={{ perspective: '1200px' }}
      aria-label="Interactive 3D Vendor Due Diligence Scene"
    >
      {/* Ambient background glow ring with smooth state transition */}
      <div
        className={`absolute inset-0 bg-gradient-to-tr ${current.glow} rounded-full blur-3xl opacity-60 dark:opacity-75 transition-all duration-700 pointer-events-none`}
      />

      {/* 3D Stage Root */}
      <div
        className={`relative w-full h-full transition-transform duration-150 ease-out flex items-center justify-center ${
          mounted ? 'animate-reveal-up' : 'opacity-0'
        }`}
        style={{
          transformStyle: 'preserve-3d',
          transform: `rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(${isHovered ? 1.02 : 1})`
        }}
      >
        {/* Layer 0: Ground Grid Plane (Perspective Depth) */}
        <div
          className="absolute w-[120%] h-[120%] border border-teal-500/15 dark:border-teal-500/20 rounded-3xl pointer-events-none opacity-40 dark:opacity-60 transition-opacity"
          style={{
            transform: 'translateZ(-140px) rotateX(72deg)',
            backgroundImage:
              'radial-gradient(circle, rgba(20, 184, 166, 0.2) 1px, transparent 1px)',
            backgroundSize: '24px 24px'
          }}
        />

        {/* Layer 1: Floating Invoice Sheets Stack (Left-Back) */}
        <div
          className="absolute left-2 sm:left-4 top-4 sm:top-6 w-56 sm:w-64 bg-white/95 dark:bg-[#0c121e]/95 backdrop-blur-md rounded-xl p-3.5 border border-zinc-200/90 dark:border-zinc-700/80 shadow-2xl transition-all duration-300 animate-float-slow"
          style={{
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)'
          }}
        >
          {/* Subtle Paper Top Tab */}
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-zinc-200/80 dark:border-zinc-800">
            <div className="flex items-center space-x-1.5">
              <FileText className="h-3.5 w-3.5 text-teal-600 dark:text-teal-400" />
              <span className="text-[10.5px] font-mono font-semibold tracking-wider text-zinc-900 dark:text-zinc-100">
                INV-2026-8841
              </span>
            </div>
            <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300 font-medium">
              CLAIM
            </span>
          </div>

          <div className="space-y-1.5 text-[10px]">
            <div className="flex justify-between">
              <span className="text-zinc-500 dark:text-zinc-400">Supplier:</span>
              <span className="font-semibold text-zinc-900 dark:text-zinc-100">Apex Courier Pvt Ltd</span>
            </div>
            <div className="flex justify-between">
              <span className="text-zinc-500 dark:text-zinc-400">GSTIN Claim:</span>
              <span className="font-mono text-[9.5px] text-teal-700 dark:text-teal-300 font-bold">
                07AAAAA0000A1Z4
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-zinc-500 dark:text-zinc-400">Payable Amount:</span>
              <span className="font-mono font-bold text-zinc-900 dark:text-zinc-50">
                ₹4,82,500.00
              </span>
            </div>
          </div>

          <div className="mt-2.5 pt-2 border-t border-dashed border-zinc-200 dark:border-zinc-800 flex items-center justify-between text-[9px] text-zinc-400">
            <span>ITC Claimed: ₹73,602</span>
            <span className="text-teal-600 dark:text-teal-400 font-medium flex items-center space-x-1">
              <span className="w-1.5 h-1.5 rounded-full bg-teal-500 animate-pulse" />
              <span>Unverified Claim</span>
            </span>
          </div>
        </div>

        {/* Layer 2: Public Registry Evidence Nodes (Right Side) */}
        <div
          className="absolute right-1 sm:right-3 top-2 sm:top-5 space-y-2.5 w-52 sm:w-60 pointer-events-none animate-float-registry"
        >
          {/* Node 1: GST Portal */}
          <div className="bg-white/95 dark:bg-[#0c121e]/95 backdrop-blur-md rounded-lg p-2.5 border border-zinc-200/90 dark:border-zinc-700/80 shadow-lg flex items-center space-x-2.5 transition-all">
            <div className="w-6 h-6 rounded bg-teal-500/10 text-teal-600 dark:text-teal-400 flex items-center justify-center shrink-0">
              <Database className="h-3.5 w-3.5" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between text-[9px] text-zinc-400">
                <span>GST Portal API</span>
                <span className={`font-mono font-bold ${current.gstStatusColor}`}>
                  {current.gstStatus}
                </span>
              </div>
              <div className="text-[10px] font-semibold text-zinc-900 dark:text-zinc-100 truncate">
                07AAAAA0000A1Z4 Checksum Valid
              </div>
            </div>
          </div>

          {/* Node 2: MCA21 Registry */}
          <div className="bg-white/95 dark:bg-[#0c121e]/95 backdrop-blur-md rounded-lg p-2.5 border border-zinc-200/90 dark:border-zinc-700/80 shadow-lg flex items-center space-x-2.5 transition-all">
            <div className="w-6 h-6 rounded bg-sky-500/10 text-sky-600 dark:text-sky-400 flex items-center justify-center shrink-0">
              <Building2 className="h-3.5 w-3.5" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between text-[9px] text-zinc-400">
                <span>MCA21 Ministry</span>
                <span className={`font-mono font-bold ${current.mcaStatusColor}`}>
                  {current.mcaStatus}
                </span>
              </div>
              <div className="text-[10px] font-semibold text-zinc-900 dark:text-zinc-100 truncate">
                Active Incorporation (CIN Match)
              </div>
            </div>
          </div>

          {/* Node 3: TinyFish Web Agent */}
          <div className="bg-white/95 dark:bg-[#0c121e]/95 backdrop-blur-md rounded-lg p-2.5 border border-zinc-200/90 dark:border-zinc-700/80 shadow-lg flex items-center space-x-2.5 transition-all">
            <div className="w-6 h-6 rounded bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 flex items-center justify-center shrink-0">
              <Globe className="h-3.5 w-3.5" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between text-[9px] text-zinc-400">
                <span>TinyFish Public Web</span>
                <span className={`font-mono font-bold ${current.webStatusColor}`}>
                  {current.webStatus}
                </span>
              </div>
              <div className="text-[10px] font-semibold text-zinc-900 dark:text-zinc-100 truncate">
                Physical Office & Domain Match
              </div>
            </div>
          </div>
        </div>

        {/* Animated Connecting Data Conduits (SVG Laser Rays) */}
        <svg
          className="absolute inset-0 w-full h-full pointer-events-none"
          style={{ transform: 'translateZ(15px)' }}
          viewBox="0 0 500 400"
          fill="none"
        >
          {/* Conduit 1: Invoice to Central Shield */}
          <path
            d="M 170 135 C 210 155, 220 175, 250 195"
            stroke={current.strokeColor}
            strokeWidth="2"
            strokeDasharray="4 4"
            strokeDashoffset={-pulseTick * 2.5}
            className="opacity-75 transition-colors duration-300"
          />

          {/* Conduit 2: GST Node to Shield */}
          <path
            d="M 360 80 C 310 115, 290 155, 250 195"
            stroke={current.strokeColor}
            strokeWidth="2"
            strokeDasharray="4 4"
            strokeDashoffset={pulseTick * 2.5}
            className="opacity-75 transition-colors duration-300"
          />

          {/* Conduit 3: MCA Node to Shield */}
          <path
            d="M 360 140 C 320 160, 290 180, 250 195"
            stroke={current.strokeColor}
            strokeWidth="2"
            strokeDasharray="4 4"
            strokeDashoffset={pulseTick * 2.5}
            className="opacity-75 transition-colors duration-300"
          />

          {/* Conduit 4: Web Node to Shield */}
          <path
            d="M 360 200 C 320 200, 290 200, 250 195"
            stroke={current.strokeColor}
            strokeWidth="2"
            strokeDasharray="4 4"
            strokeDashoffset={pulseTick * 2.5}
            className="opacity-75 transition-colors duration-300"
          />

          {/* Radar Ping Beacon on Shield Reception Node */}
          <circle
            cx="250"
            cy="195"
            r="8"
            fill="none"
            stroke={current.strokeColor}
            strokeWidth="1.5"
            className="animate-ping"
          />
          <circle cx="250" cy="195" r="3.5" fill={current.strokeColor} />
        </svg>

        {/* Layer 3: Central 3D Verification Shield (Core Sentinel) */}
        <div
          className={`absolute z-20 w-36 sm:w-44 aspect-square rounded-2xl bg-gradient-to-b from-zinc-900 via-zinc-900 to-zinc-950 text-white p-4 flex flex-col items-center justify-between border-2 shadow-2xl transition-all duration-300 animate-float-shield ${current.shieldBorder}`}
          style={{
            boxShadow: `${current.shieldGlow}, inset 0 1px 1px rgba(255, 255, 255, 0.25)`
          }}
        >
          {/* Top Shield Status Bar */}
          <div className="w-full flex items-center justify-between text-[9px] text-zinc-300 font-mono">
            <span className="flex items-center space-x-1">
              <Lock className="h-2.5 w-2.5 text-teal-400" />
              <span>SENTINEL</span>
            </span>
            <span className="text-teal-400 font-semibold">SHA-256</span>
          </div>

          {/* Center 3D Shield Badge with dynamic status icon */}
          <div className="relative my-auto flex flex-col items-center">
            <div
              className="w-14 h-14 rounded-full flex items-center justify-center transition-all duration-500 shadow-inner"
              style={{
                backgroundColor: `${current.strokeColor}22`,
                border: `2px solid ${current.strokeColor}`
              }}
            >
              {activeOutcome === 'PASS' && (
                <ShieldCheck className="h-7 w-7 text-emerald-400 stroke-[2.2] animate-pulse" />
              )}
              {activeOutcome === 'REVIEW' && (
                <AlertTriangle className="h-7 w-7 text-amber-400 stroke-[2.2] animate-pulse" />
              )}
              {activeOutcome === 'BLOCK' && (
                <ShieldAlert className="h-7 w-7 text-rose-400 stroke-[2.2] animate-pulse" />
              )}
            </div>

            <div className="mt-2 text-center">
              <div className="text-xs font-bold tracking-tight text-white uppercase">
                {activeOutcome}
              </div>
              <div className="text-[9.5px] font-mono text-zinc-400">
                Score: <span className="text-white font-bold">{current.score}</span>/100
              </div>
            </div>
          </div>

          {/* Bottom Engine Indicator */}
          <div className="text-[8px] uppercase tracking-wider text-teal-400 font-mono">
            Deterministic Engine
          </div>
        </div>

        {/* Layer 4: Live Reconciliation Overlay Banner (Bottom Front) */}
        <div
          className="absolute bottom-1 sm:bottom-3 left-3 right-3 sm:left-6 sm:right-6 bg-white/95 dark:bg-[#0c121e]/95 backdrop-blur-md rounded-xl p-3 border border-zinc-200/90 dark:border-zinc-700/80 shadow-2xl flex flex-col sm:flex-row items-center justify-between gap-2.5"
          style={{ transform: 'translateZ(95px)' }}
        >
          <div className="flex items-center space-x-2.5 min-w-0">
            <span
              className={`px-2 py-0.5 rounded text-[10px] font-bold border shrink-0 ${current.badgeClass}`}
            >
              {current.label}
            </span>
            <div className="truncate text-left">
              <div className="text-[11px] font-semibold text-zinc-900 dark:text-zinc-100 truncate">
                {current.headline}
              </div>
              <div className="text-[10px] text-zinc-500 dark:text-zinc-400 truncate">
                {current.desc}
              </div>
            </div>
          </div>

          {/* Interactive Outcome State Toggles (Green / Amber / Red) */}
          <div className="flex items-center space-x-1 shrink-0 bg-zinc-100 dark:bg-zinc-800/80 p-0.5 rounded-lg border border-zinc-200 dark:border-zinc-700/60 text-[10px]">
            <button
              type="button"
              onClick={() => setActiveOutcome('PASS')}
              className={`px-2.5 py-1 rounded font-semibold transition-all ${
                activeOutcome === 'PASS'
                  ? 'bg-emerald-600 text-white shadow-sm scale-105'
                  : 'text-zinc-600 dark:text-zinc-400 hover:text-emerald-600 dark:hover:text-emerald-400'
              }`}
            >
              Pass (12)
            </button>
            <button
              type="button"
              onClick={() => setActiveOutcome('REVIEW')}
              className={`px-2.5 py-1 rounded font-semibold transition-all ${
                activeOutcome === 'REVIEW'
                  ? 'bg-amber-600 text-white shadow-sm scale-105'
                  : 'text-zinc-600 dark:text-zinc-400 hover:text-amber-600 dark:hover:text-amber-400'
              }`}
            >
              Review (48)
            </button>
            <button
              type="button"
              onClick={() => setActiveOutcome('BLOCK')}
              className={`px-2.5 py-1 rounded font-semibold transition-all ${
                activeOutcome === 'BLOCK'
                  ? 'bg-rose-600 text-white shadow-sm scale-105'
                  : 'text-zinc-600 dark:text-zinc-400 hover:text-rose-600 dark:hover:text-rose-400'
              }`}
            >
              Block (84)
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
