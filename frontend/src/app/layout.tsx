import type { Metadata } from 'next';
import './globals.css';
import { ThemeProvider } from '../components/ThemeProvider';
import { Navbar } from '../components/Navbar';
import { Shield, Lock } from 'lucide-react';

export const metadata: Metadata = {
  title: 'VendorShield AI | Pre-Payment Vendor Due Diligence & Fraud Defense',
  description: 'Evidence-first accounts payable due-diligence platform powered by TinyFish browser research. HackIIITD (Esya 26).',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* Anti-flash inline theme initializer */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var stored = localStorage.getItem('vendorshield-theme');
                  var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                  if (stored === 'dark' || (!stored && prefersDark)) {
                    document.documentElement.classList.add('dark');
                  } else {
                    document.documentElement.classList.remove('dark');
                  }
                } catch (e) {}
              })();
            `,
          }}
        />
      </head>
      <body className="bg-background text-foreground antialiased min-h-screen flex flex-col transition-colors">
        <ThemeProvider>
          {/* Compact Enterprise Navbar */}
          <Navbar />

          {/* Main Workspace Area */}
          <main className="flex-1 w-full flex flex-col">
            {children}
          </main>

          {/* Subtle Enterprise Footer */}
          <footer className="border-t border-zinc-200/80 dark:border-zinc-800/80 py-4 bg-white/50 dark:bg-[#070a10]/50 text-xs text-zinc-500 dark:text-zinc-400 transition-colors">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-[11px]">
              <div className="flex items-center space-x-2 text-zinc-500 dark:text-zinc-400">
                <span className="font-medium text-zinc-700 dark:text-zinc-300">VendorShield AI</span>
                <span>&bull;</span>
                <span>Pre-Payment Due Diligence</span>
                <span>&bull;</span>
                <span>HackIIITD Esya &apos;26</span>
              </div>

              <div className="flex items-center space-x-3 text-zinc-400 dark:text-zinc-500">
                <span className="flex items-center space-x-1">
                  <Lock className="h-3 w-3" />
                  <span>SHA-256 Audit Trail</span>
                </span>
                <span>&bull;</span>
                <span>Axiom: TinyFish researches; VendorShield decides</span>
              </div>
            </div>
          </footer>
        </ThemeProvider>
      </body>
    </html>
  );
}
