import React, { useEffect, useRef, useState } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import { api, ApiError, enc } from "../api/client";
import type { SearchOut } from "../api/types";
import { navItems } from "../lib/nav";
import { getCompareSelection } from "../lib/sessionCompare";
import { Score, SignalBadge, useDebounced } from "./ui";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const [hasJobs, setHasJobs] = useState(false);
  const [query, setQuery] = useState("");
  const debounced = useDebounced(query, 250);
  const [results, setResults] = useState<SearchOut | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [compareCount, setCompareCount] = useState(0);
  const nav = useNavigate();
  const loc = useLocation();
  const searchRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const active = document.activeElement;
      const isInput = active && (active.tagName === "INPUT" || active.tagName === "TEXTAREA");
      if (e.key === "/" && !isInput) {
        e.preventDefault();
        searchRef.current?.focus();
        setOpen(true);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  useEffect(() => {
    api.jobs().then(() => setHasJobs(true)).catch(() => setHasJobs(false));
  }, []);

  useEffect(() => {
    setCompareCount(getCompareSelection().length);
  }, [loc]);

  useEffect(() => {
    const q = debounced.trim();
    if (!q) {
      setResults(null);
      setSearchError(null);
      setOpen(false);
      return;
    }
    api.search(q, 8).then(setResults).catch((e: ApiError) => setSearchError(e.message));
  }, [debounced]);

  useEffect(() => {
    setQuery("");
    setResults(null);
    setOpen(false);
  }, [loc.pathname]);

  const pick = (cid: string) => {
    setQuery("");
    setResults(null);
    setOpen(false);
    nav(`/c/${enc(cid)}`);
  };

  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-20 border-b border-line bg-panel/90 backdrop-blur">
        <div className="mx-auto max-w-desk px-6 py-3 flex items-center gap-6">
          <Link to="/" className="flex items-baseline gap-2.5 shrink-0 group">
            <span className="h-2.5 w-2.5 rounded-full bg-gold inline-block" aria-hidden="true" />
            <span className="font-display text-lg tracking-tight text-paper group-hover:text-gold transition-colors">
              Research Desk
            </span>
          </Link>

          <nav className="flex gap-1 text-sm" aria-label="Main">
            {navItems(hasJobs).map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  `rounded px-3 py-1.5 transition-colors ${
                    isActive ? "bg-panel2 text-gold" : "text-fog hover:text-paper"
                  }`
                }
              >
                {item.label}
                {item.to === "/compare" && compareCount > 0 && (
                  <span
                    className="ml-1.5 rounded bg-gold/20 px-1.5 py-0.5 font-mono text-[10px] text-gold"
                    aria-label={`${compareCount} companies in the compare basket`}
                  >
                    {compareCount}
                  </span>
                )}
              </NavLink>
            ))}
          </nav>

          <div className="relative ml-auto w-full max-w-md">
            <input
              ref={searchRef}
              type="search"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setOpen(true);
              }}
              onFocus={() => setOpen(true)}
              placeholder="Search name, ticker, or ID… (Press /)"
              aria-label="Search companies"
              className="w-full rounded-md border border-line bg-ink px-3 py-2 text-sm placeholder:text-dim"
            />
            {open && (results || searchError) && (
              <div className="absolute left-0 right-0 top-full mt-2 rounded-md border border-line bg-panel shadow-xl z-30">
                {searchError ? (
                  <p className="px-4 py-3 text-sm text-bad">{searchError}</p>
                ) : results && results.items.length === 0 ? (
                  <div className="p-3 text-center">
                    <p className="text-xs text-fog mb-2">Not in 720 library.</p>
                    <button
                      type="button"
                      onClick={() => {
                        const q = query.trim();
                        setOpen(false);
                        setQuery("");
                        nav(`/?ingest=${enc(q)}`);
                      }}
                      className="inline-flex items-center gap-1.5 rounded border border-gold/60 bg-gold/10 px-3 py-1.5 text-xs font-medium text-gold hover:bg-gold/20 transition-colors"
                    >
                      Not in library — fetch {query.trim().toUpperCase()}?
                    </button>
                  </div>
                ) : (
                  <ul className="divide-y divide-line max-h-96 overflow-auto">
                    {results?.items.map((it) => (
                      <li key={it.company_id}>
                        <button
                          onClick={() => pick(it.company_id)}
                          className="w-full flex items-center justify-between gap-4 px-4 py-2.5 text-left hover:bg-panel2"
                        >
                          <span>
                            <span className="text-sm text-paper">{it.name ?? it.company_id}</span>
                            <span className="ml-2 font-mono text-xs text-dim">{it.company_id}</span>
                          </span>
                          <span className="flex items-center gap-2">
                            <Score value={it.composite} />
                            <SignalBadge signal={it.signal} small />
                          </span>
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>
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
