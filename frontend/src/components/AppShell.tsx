import React, { useEffect, useRef, useState } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import { api, ApiError, enc } from "../api/client";
import type { SuggestionsOut } from "../api/types";
import { navItems } from "../lib/nav";
import { getCompareSelection, COMPARE_EVENT } from "../lib/sessionCompare";
import { Score, SignalBadge, useDebounced } from "./ui";
import ThemeToggle from "./ThemeToggle";
import CommandPalette from "./common/CommandPalette";
import TerminalMarketTape from "./viz/TerminalMarketTape";

function AlertDrawerContent() {
  const [events, setEvents] = React.useState<any[]>([]);
  React.useEffect(() => {
    api.alertsEvents().then((r: any) => setEvents(r.events ?? [])).catch(() => {});
  }, []);
  if (events.length === 0) return <p className="text-xs text-ink-2">No alerts - daemon evaluated clean. Heartbeat operational.</p>;
  return (
    <div className="space-y-1 text-xs">
      {events.slice(0, 8).map((e: any) => (
        <div key={e.id ?? e.rule_id} className="flex justify-between border-b border-border py-1">
          <span className="font-mono">{e.ticker ?? e.company_id} · {e.rule_type}</span>
          <span className="text-ink-2 truncate max-w-[120px]">{e.detail}</span>
        </div>
      ))}
    </div>
  );
}


export default function AppShell({ children }: { children: React.ReactNode }) {
  const [hasJobs, setHasJobs] = useState(false);
  const [query, setQuery] = useState("");
  const debounced = useDebounced(query, 200);
  const [results, setResults] = useState<SuggestionsOut | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [compareCount, setCompareCount] = useState(0);
  const [alertCount, setAlertCount] = useState(0);
  const [alertOpen, setAlertOpen] = useState(false);
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
    const syncCompare = () => setCompareCount(getCompareSelection().length);
    syncCompare();
    window.addEventListener(COMPARE_EVENT, syncCompare);
    window.addEventListener("storage", syncCompare);
    return () => {
      window.removeEventListener(COMPARE_EVENT, syncCompare);
      window.removeEventListener("storage", syncCompare);
    };
  }, []);

  useEffect(() => {
    setCompareCount(getCompareSelection().length);
    api.alertsEvents().then((r: any) => setAlertCount(r.count ?? r.events?.length ?? 0)).catch(() => {});
  }, [loc]);

  useEffect(() => {
    const q = debounced.trim();
    if (!q) {
      setResults(null);
      setSearchError(null);
      setOpen(false);
      return;
    }
    api.suggestions(q, 8).then(setResults).catch((e: ApiError) => setSearchError(e.message));
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
    <div className="min-h-screen flex flex-col bg-bg-0 text-ink-0">
      <TerminalMarketTape />
      <header className="sticky top-0 z-20 border-b border-border bg-bg-1/90 backdrop-blur shadow-sm">
        <div className="w-full max-w-desk mx-auto px-3 sm:px-5 lg:px-6 xl:px-8 py-2.5 flex items-center gap-4 sm:gap-6">
          <Link to="/" className="flex items-center gap-2.5 shrink-0 group">
            <span className="h-2.5 w-2.5 rounded-full bg-accent inline-block" aria-hidden="true" />
            <span className="font-display text-lg tracking-tight text-ink-0 group-hover:text-accent transition-colors font-semibold">
              Research Desk
            </span>
          </Link>

          <nav className="flex gap-1 text-xs font-medium" aria-label="Main">
            {navItems(hasJobs).map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  `rounded-chip px-3 py-1.5 transition-colors ${
                    isActive
                      ? "bg-bg-2 text-accent font-semibold shadow-xs"
                      : "text-ink-1 hover:text-ink-0 hover:bg-bg-2/50"
                  }`
                }
              >
                {item.label}
                {item.to === "/compare" && compareCount > 0 && (
                  <span
                    className="ml-1.5 rounded-chip bg-accent-weak px-1.5 py-0.5 font-mono text-[10px] text-accent"
                    aria-label={`${compareCount} companies in the compare basket`}
                  >
                    {compareCount}
                  </span>
                )}
              </NavLink>
            ))}
            <NavLink
              to="/portfolio"
              className={({ isActive }) =>
                `rounded-chip px-3 py-1.5 transition-colors ${isActive ? "bg-bg-2 text-accent font-semibold" : "text-ink-1 hover:text-ink-0 hover:bg-bg-2/50"}`
              }
            >
              Portfolio
            </NavLink>
            <NavLink
              to="/alerts"
              className={({ isActive }) =>
                `rounded-chip px-3 py-1.5 transition-colors flex items-center gap-1 ${isActive ? "bg-bg-2 text-accent font-semibold" : "text-ink-1 hover:text-ink-0 hover:bg-bg-2/50"}`
              }
            >
              Alerts
              {alertCount > 0 && (
                <span className="rounded-chip bg-neg text-white px-1.5 py-0.5 font-mono text-[10px]" aria-label={`${alertCount} alerts`}>
                  {alertCount}
                </span>
              )}
            </NavLink>
            <button
              onClick={() => setAlertOpen((v) => !v)}
              aria-label="Open alerts drawer"
              aria-expanded={alertOpen}
              className="rounded-chip px-2 py-1 text-ink-1 hover:text-ink-0 border border-border"
            >
              🔔
            </button>
          </nav>

          <div className="relative ml-auto flex items-center gap-2.5 w-full max-w-md">
            <div className="relative flex-1">
              <input
                ref={searchRef}
                type="search"
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setOpen(true);
                }}
                onFocus={() => setOpen(true)}
                placeholder="Search name, ticker, or ID… (Press / or ⌘K)"
                aria-label="Search companies"
                className="w-full rounded-card border border-border bg-bg-0 px-3 py-1.5 text-xs text-ink-0 placeholder:text-ink-2 focus:border-accent focus:outline-none transition-colors"
              />
              {open && (results || searchError) && (
                <div className="absolute left-0 right-0 top-full mt-2 rounded-card border border-border bg-bg-1 shadow-modal z-30 overflow-hidden">
                  {searchError ? (
                    <p className="px-4 py-3 text-xs text-neg font-mono">{searchError}</p>
                  ) : results && results.items.length === 0 ? (
                    <div className="p-3 text-center">
                      <p className="text-xs text-ink-1 mb-2">Not in 720 library.</p>
                      <button
                        type="button"
                        onClick={() => {
                          const q = query.trim();
                          setOpen(false);
                          setQuery("");
                          nav(`/?ingest=${enc(q)}`);
                        }}
                        className="inline-flex items-center gap-1.5 rounded-card border border-accent/60 bg-accent-weak px-3 py-1.5 text-xs font-mono text-accent hover:bg-accent/20 transition-colors"
                      >
                        Not in library - fetch {query.trim().toUpperCase()}?
                      </button>
                    </div>
                  ) : (
                    <ul className="divide-y divide-border max-h-96 overflow-auto">
                      {results?.items.map((it) => {
                        const ex = (it.exchange || "US").toUpperCase();
                        const badgeColor =
                          ex === "NASDAQ"
                            ? "bg-sky-500/10 text-sky-400 border-sky-500/30"
                            : ex === "NYSE"
                            ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                            : ex === "TSX" || ex === "TSXV"
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                            : "bg-indigo-500/10 text-indigo-400 border-indigo-500/30";

                        return (
                          <li key={it.company_id}>
                            <button
                              onClick={() => pick(it.company_id)}
                              className="w-full flex items-center justify-between gap-3 px-3.5 py-2.5 text-left hover:bg-bg-2 transition-colors group"
                            >
                              <div className="flex items-center gap-2.5 min-w-0">
                                <span className="font-mono font-bold text-xs text-ink-0 group-hover:text-accent shrink-0">
                                  {it.ticker}
                                </span>
                                <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-medium border shrink-0 ${badgeColor}`}>
                                  {it.exchange}
                                </span>
                                <span className="text-xs text-ink-1 truncate">
                                  {it.name || it.company_id}
                                </span>
                                {it.sector && (
                                  <span className="hidden sm:inline text-[10px] text-ink-2 truncate">
                                    · {it.sector}
                                  </span>
                                )}
                              </div>
                              <div className="flex items-center gap-2 shrink-0">
                                {it.in_database ? (
                                  <>
                                    <Score value={it.composite ?? null} />
                                    {it.signal && <SignalBadge signal={it.signal as any} small />}
                                  </>
                                ) : (
                                  <span className="inline-flex items-center gap-1 rounded border border-accent/40 bg-accent-weak px-1.5 py-0.5 font-mono text-[10px] text-accent">
                                    <span>+</span> Ingest
                                  </span>
                                )}
                              </div>
                            </button>
                          </li>
                        );
                      })}
                    </ul>
                  )}
                </div>
              )}
            </div>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <CommandPalette />

      {alertOpen && (
        <div role="dialog" aria-modal="true" aria-label="Alerts drawer" className="fixed inset-y-0 right-0 z-40 w-80 bg-bg-1 border-l border-border shadow-2xl p-4 overflow-y-auto">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-heading font-semibold text-ink-0">Alerts</h3>
            <button onClick={() => setAlertOpen(false)} aria-label="Close alerts drawer" className="p-1 text-ink-2 hover:text-ink-0" onKeyDown={(e) => { if (e.key === "Escape") setAlertOpen(false); }}>✕</button>
          </div>
          <AlertDrawerContent />
          <p className="text-[11px] font-mono text-ink-2 mt-3 border-t border-border pt-2">Personal research software, not investment advice. Portfolio tracking and alerts run locally.</p>
        </div>
      )}

      <main className="mx-auto w-full max-w-desk flex-1 px-3 sm:px-5 lg:px-6 xl:px-8 py-3 sm:py-5">{children}</main>

      <footer className="border-t border-border mt-12">
        <div className="mx-auto max-w-desk px-6 py-6 text-xs leading-relaxed text-ink-2">
          <p className="mb-1">
            Personal research software. <span className="text-ink-1">Not investment advice.</span> Scores are
            research signals, never trade orders. Halal is an informational flag, not a religious ruling.
          </p>
          <p className="font-mono text-[10px] text-ink-2">
            method_version v1 · data: owner workbook snapshot + SEC/Yahoo history · local only
          </p>
        </div>
      </footer>
    </div>
  );
}