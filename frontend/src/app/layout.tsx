import type { Metadata } from 'next';
import './globals.css';
import Link from 'next/link';
import { ShieldCheck, UploadCloud, Layers, Cpu } from 'lucide-react';

export const metadata: Metadata = {
  title: 'VendorShield AI | Pre-Payment Vendor Due Diligence',
  description: 'Evidence-grounded accounts payable due-diligence platform powered by TinyFish. HackIIITD (Esya 26).',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#090d16] text-slate-100 antialiased min-h-screen flex flex-col">
        {/* Tactical Header */}
        <header className="border-b border-slate-800 bg-[#0d1322]/80 backdrop-blur-md sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="h-9 w-9 rounded-lg bg-cyan-950 border border-cyan-500/40 flex items-center justify-center text-cyan-400">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <div>
                <Link href="/" className="flex items-center space-x-2">
                  <span className="font-bold tracking-tight text-lg text-white">VendorShield</span>
                  <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/60 font-semibold">AI</span>
                </Link>
                <p className="text-[11px] text-slate-400 font-mono hidden sm:block">Astra-X &bull; HackIIITD Esya &apos;26</p>
              </div>
            </div>

            {/* Navigation & Status */}
            <nav className="flex items-center space-x-4">
              <Link
                href="/"
                className="flex items-center space-x-1.5 text-xs font-medium text-slate-300 hover:text-white px-3 py-1.5 rounded-md hover:bg-slate-800/60 transition"
              >
                <Layers className="h-4 w-4 text-slate-400" />
                <span>Cases</span>
              </Link>

              <Link
                href="/upload"
                className="flex items-center space-x-1.5 text-xs font-medium bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold px-3.5 py-1.5 rounded-md transition shadow-sm"
              >
                <UploadCloud className="h-4 w-4" />
                <span>Intake Invoice</span>
              </Link>

              <div className="hidden md:flex items-center space-x-1.5 text-[11px] font-mono text-cyan-400 bg-cyan-950/40 border border-cyan-800/50 px-2.5 py-1 rounded-full">
                <Cpu className="h-3.5 w-3.5 text-cyan-400 animate-pulse" />
                <span>TinyFish Engine Ready</span>
              </div>
            </nav>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {children}
        </main>

        {/* Footer */}
        <footer className="border-t border-slate-800/60 py-4 bg-[#0b0f19] text-center text-xs text-slate-500 font-mono">
          <p>VendorShield AI &bull; Axiom: TinyFish researches; VendorShield decides &bull; Fail-closed audit support</p>
        </footer>
      </body>
    </html>
  );
}
