'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Shield, Layers, Plus, Menu, X, ArrowUpRight, ArrowRight, Key, UserCheck, Check } from 'lucide-react';
import { ThemeToggle } from './ThemeProvider';

export function Navbar() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [currentToken, setCurrentToken] = useState('dev-reviewer-token');
  const [tokenInput, setTokenInput] = useState('');

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = sessionStorage.getItem('vendorshield_token') || 'garv-reviewer-token-2026';
      setCurrentToken(saved);
      setTokenInput(saved);

      const handleAuthError = () => {
        setAuthModalOpen(true);
      };
      window.addEventListener('vendorshield_auth_error', handleAuthError);
      return () => window.removeEventListener('vendorshield_auth_error', handleAuthError);
    }
  }, []);

  const saveToken = (tok: string) => {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('vendorshield_token', tok.trim());
      setCurrentToken(tok.trim());
      setAuthModalOpen(false);
    }
  };

  const isActive = (path: string) => {
    if (path === '/' && pathname === '/') return true;
    if (path === '/queue' && (pathname === '/queue' || pathname === '/dashboard' || pathname.startsWith('/cases'))) return true;
    if (path === '/upload' && pathname.startsWith('/upload')) return true;
    return false;
  };

  const roleLabel = currentToken.includes('analyst') ? 'AP Analyst (Priya)' : 'Reviewer (Garv)';

  return (
    <>
      <header className="sticky top-0 z-50 h-14 border-b border-zinc-200/80 dark:border-zinc-800/80 bg-white/95 dark:bg-[#090d14]/95 backdrop-blur-md transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-full flex items-center justify-between">
          {/* Brand */}
          <div className="flex items-center space-x-6">
            <Link href="/" className="flex items-center space-x-2.5 group">
              <div className="w-7 h-7 rounded-md bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 flex items-center justify-center transition-transform group-hover:scale-105 shadow-sm">
                <Shield className="h-4 w-4 stroke-[2.2]" />
              </div>
              <div className="flex items-baseline space-x-2">
                <span className="font-semibold text-sm tracking-tight text-zinc-900 dark:text-zinc-100">
                  VendorShield
                </span>
                <span className="text-[10px] font-medium uppercase tracking-wider text-teal-600 dark:text-teal-400">
                  AI Sentinel
                </span>
              </div>
            </Link>

            {/* Navigation Links (Desktop) */}
            <nav className="hidden lg:flex items-center space-x-1">
              <Link
                href="/"
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  pathname === '/'
                    ? 'bg-zinc-100 dark:bg-zinc-800/80 text-zinc-900 dark:text-zinc-100'
                    : 'text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200 hover:bg-zinc-100/60 dark:hover:bg-zinc-800/40'
                }`}
              >
                Overview
              </Link>

              <Link
                href="/#sequence"
                className="px-3 py-1.5 rounded-md text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200 hover:bg-zinc-100/60 dark:hover:bg-zinc-800/40 transition-colors"
              >
                Execution Sequence
              </Link>

              <div className="h-4 w-px bg-zinc-200 dark:bg-zinc-800 mx-1" />

              <Link
                href="/queue"
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  isActive('/queue')
                    ? 'bg-zinc-100 dark:bg-zinc-800/80 text-zinc-900 dark:text-zinc-100'
                    : 'text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200 hover:bg-zinc-100/60 dark:hover:bg-zinc-800/40'
                }`}
              >
                Cases Queue
              </Link>

              <Link
                href="/upload"
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  isActive('/upload')
                    ? 'bg-zinc-100 dark:bg-zinc-800/80 text-zinc-900 dark:text-zinc-100'
                    : 'text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200 hover:bg-zinc-100/60 dark:hover:bg-zinc-800/40'
                }`}
              >
                Intake Invoice
              </Link>
            </nav>
          </div>

          {/* Right Section: Auth Role Pill, CTA, Theme */}
          <div className="hidden sm:flex items-center space-x-3">
            {/* Bearer Auth Token Pill */}
            <button
              type="button"
              onClick={() => setAuthModalOpen(true)}
              className="flex items-center space-x-1.5 px-2.5 py-1 rounded text-[11px] font-mono text-zinc-600 dark:text-zinc-400 bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-200/70 dark:border-zinc-800/70 hover:border-teal-500 transition"
              title="Click to configure Access Token"
            >
              <Key className="h-3 w-3 text-teal-600 dark:text-teal-400" />
              <span>{roleLabel}</span>
            </button>

            <div className="hidden md:block h-4 w-px bg-zinc-200 dark:bg-zinc-800" />

            {/* Primary Action Button */}
            <Link
              href="/queue"
              className="group inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium text-white bg-teal-700 hover:bg-teal-600 dark:bg-teal-600 dark:hover:bg-teal-500 transition-all duration-200 shadow-subtle hover:shadow-md hover:shadow-teal-500/20 active:scale-95"
            >
              <span>Explore Platform</span>
              <ArrowRight className="h-3 w-3 group-hover:translate-x-0.5 transition-transform" />
            </Link>

            {/* Theme Switcher */}
            <ThemeToggle />
          </div>

          {/* Mobile Menu & Theme Toggle */}
          <div className="flex items-center space-x-2 sm:hidden">
            <button
              type="button"
              onClick={() => setAuthModalOpen(true)}
              className="p-1.5 rounded-md text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800"
              title="Access Token"
            >
              <Key className="h-4 w-4 text-teal-500" />
            </button>
            <ThemeToggle />
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-1.5 rounded-md text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Drawer */}
        {mobileMenuOpen && (
          <div className="sm:hidden border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#090d14] px-4 py-3 space-y-1 shadow-dropdown">
            <Link
              href="/"
              onClick={() => setMobileMenuOpen(false)}
              className={`block px-3 py-2 rounded-md text-xs font-medium ${
                pathname === '/'
                  ? 'bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100'
                  : 'text-zinc-600 dark:text-zinc-400'
              }`}
            >
              Overview
            </Link>
            <Link
              href="/queue"
              onClick={() => setMobileMenuOpen(false)}
              className={`block px-3 py-2 rounded-md text-xs font-medium ${
                isActive('/queue')
                  ? 'bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100'
                  : 'text-zinc-600 dark:text-zinc-400'
              }`}
            >
              Cases Queue
            </Link>
            <Link
              href="/upload"
              onClick={() => setMobileMenuOpen(false)}
              className={`block px-3 py-2 rounded-md text-xs font-medium ${
                isActive('/upload')
                  ? 'bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100'
                  : 'text-zinc-600 dark:text-zinc-400'
              }`}
            >
              Intake Invoice
            </Link>
          </div>
        )}
      </header>

      {/* Auth Token Configuration Modal */}
      {authModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-reveal-up">
          <div className="bg-white dark:bg-[#0f172a] border border-zinc-200 dark:border-slate-700 rounded-xl max-w-md w-full p-5 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-zinc-200 dark:border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <Key className="h-4 w-4 text-teal-600 dark:text-teal-400" />
                <h3 className="text-xs font-bold font-mono uppercase text-zinc-900 dark:text-white">
                  Access Token Authentication
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setAuthModalOpen(false)}
                className="text-zinc-400 hover:text-zinc-600 dark:hover:text-white text-xs font-mono"
              >
                &times; Close
              </button>
            </div>

            <p className="text-xs text-zinc-600 dark:text-slate-300 leading-relaxed">
              VendorShield protects accounts payable operations using token authentication. Choose a team role or enter your Bearer token.
            </p>

            {/* Quick Switch Preset Buttons */}
            <div className="space-y-2">
              <span className="text-[10px] font-mono uppercase text-zinc-400 font-semibold block">Quick Roles</span>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <button
                  type="button"
                  onClick={() => saveToken('garv-reviewer-token-2026')}
                  className="p-2.5 text-left rounded-lg border border-zinc-200 dark:border-slate-700 hover:border-teal-500 bg-zinc-50 dark:bg-slate-900/60"
                >
                  <div className="font-semibold text-zinc-900 dark:text-white">Garv Goyal</div>
                  <div className="text-[10px] font-mono text-teal-600 dark:text-teal-400">role: reviewer</div>
                </button>

                <button
                  type="button"
                  onClick={() => saveToken('priya-analyst-token-2026')}
                  className="p-2.5 text-left rounded-lg border border-zinc-200 dark:border-slate-700 hover:border-teal-500 bg-zinc-50 dark:bg-slate-900/60"
                >
                  <div className="font-semibold text-zinc-900 dark:text-white">Priya Sharma</div>
                  <div className="text-[10px] font-mono text-cyan-600 dark:text-cyan-400">role: ap_analyst</div>
                </button>
              </div>
            </div>

            {/* Manual Token Input */}
            <div className="space-y-1.5 pt-1">
              <label className="text-[10px] font-mono uppercase text-zinc-400 font-semibold block">Bearer Token</label>
              <input
                type="text"
                value={tokenInput}
                onChange={(e) => setTokenInput(e.target.value)}
                placeholder="Enter Bearer access token..."
                className="w-full px-3 py-2 text-xs font-mono bg-zinc-50 dark:bg-[#0b0f19] border border-zinc-200 dark:border-slate-700 rounded-lg text-zinc-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-teal-500"
              />
            </div>

            <div className="flex justify-end space-x-2 pt-2 border-t border-zinc-200 dark:border-slate-800">
              <button
                type="button"
                onClick={() => setAuthModalOpen(false)}
                className="px-3 py-1.5 text-xs text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => saveToken(tokenInput)}
                className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-teal-600 hover:bg-teal-500 text-white transition shadow-sm"
              >
                Save Token
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
