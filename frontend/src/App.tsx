import React from "react";
import { Link } from "react-router-dom";

export default function App({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-line bg-panel/80 backdrop-blur sticky top-0 z-10">
        <div className="mx-auto max-w-desk px-6 py-4 flex items-baseline justify-between gap-6">
          <Link to="/" className="flex items-baseline gap-3 group">
            <span className="h-2.5 w-2.5 rounded-full bg-gold inline-block" aria-hidden="true" />
            <span className="font-display text-xl tracking-tight text-paper group-hover:text-gold transition-colors">
              Research Desk
            </span>
            <span className="font-mono text-[10px] uppercase tracking-widest text-dim">v1 scores</span>
          </Link>
          <nav className="flex gap-6 text-sm" aria-label="Main">
            <Link to="/" className="text-fog hover:text-gold">Home</Link>
            <Link to="/compare" className="text-fog hover:text-gold">Compare</Link>
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-desk flex-1 px-6 py-8">{children}</main>

      <footer className="border-t border-line mt-12">
        <div className="mx-auto max-w-desk px-6 py-6 text-xs leading-relaxed text-dim">
          <p className="mb-1">
            Personal research software. <span className="text-fog">Not investment advice.</span> Scores are
            research signals, never trade orders. Halal is an informational flag, not a religious ruling.
          </p>
          <p className="font-mono text-[10px]">
            method_version v1 · data: owner workbook snapshot + SEC/Yahoo history · local only
          </p>
        </div>
      </footer>
    </div>
  );
}
