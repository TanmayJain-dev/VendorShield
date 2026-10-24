'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Shield, Layers, Plus, Menu, X, ArrowUpRight, ArrowRight } from 'lucide-react';
import { ThemeToggle } from './ThemeProvider';

export function Navbar() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const isActive = (path: string) => {
    if (path === '/' && pathname === '/') return true;
    if (path === '/queue' && (pathname === '/queue' || pathname === '/dashboard' || pathname.startsWith('/cases'))) return true;
    if (path === '/upload' && pathname.startsWith('/upload')) return true;
    return false;
  };

  return (
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
              href="/#workflow"
              className="px-3 py-1.5 rounded-md text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200 hover:bg-zinc-100/60 dark:hover:bg-zinc-800/40 transition-colors"
            >
              5-Step Workflow
            </Link>

            <Link
              href="/#architecture"
              className="px-3 py-1.5 rounded-md text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200 hover:bg-zinc-100/60 dark:hover:bg-zinc-800/40 transition-colors"
            >
              Architecture
            </Link>

            <Link
              href="/#limitations"
              className="px-3 py-1.5 rounded-md text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200 hover:bg-zinc-100/60 dark:hover:bg-zinc-800/40 transition-colors"
            >
              Safety & Limits
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

        {/* Right Section: Status, CTA, Theme */}
        <div className="hidden sm:flex items-center space-x-3">
          {/* Subtle Engine Status */}
          <div className="hidden md:flex items-center space-x-1.5 px-2.5 py-1 rounded text-[11px] font-medium text-zinc-600 dark:text-zinc-400 bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-200/70 dark:border-zinc-800/70">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span>TinyFish Engine Active</span>
          </div>

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
            Cases Queue (Platform)
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
          <Link
            href="/#workflow"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-md text-xs font-medium text-zinc-600 dark:text-zinc-400"
          >
            5-Step Workflow
          </Link>
          <Link
            href="/#architecture"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-md text-xs font-medium text-zinc-600 dark:text-zinc-400"
          >
            System Architecture
          </Link>
          <div className="pt-2 border-t border-zinc-100 dark:border-zinc-800/80 flex items-center justify-between text-[11px] text-zinc-500 px-3">
            <span className="flex items-center space-x-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              <span>TinyFish Engine Active</span>
            </span>
          </div>
        </div>
      )}
    </header>
  );
}
