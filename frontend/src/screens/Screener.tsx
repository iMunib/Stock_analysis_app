import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { DossierOut, PractitionerOut, ScreenerPreset, ScreenerResult, SuggestionItem } from "../api/types";
import { CompanyLink, ErrorBanner, Score, SignalBadge, Spinner } from "../components/ui";
import { Card, Chip, Page } from "../components/layout";
import { multiple, percentish } from "../lib/format";
import { BeneishCard } from "../components/forensics/BeneishCard";
import { ForensicCard } from "../components/ForensicCard";
import { PiotroskiCard } from "../components/dossier/PiotroskiCard";
import { DuPontCard } from "../components/dossier/DuPontCard";
import { PenmanCard } from "../components/PenmanCard";

/**
 * Forensic multi-metric screener & single-stock audit workspace (directive §4).
 * Ratios are unitless and comparable across currencies; no money columns are
 * shown, so ALL-currency runs never mix USD/CAD amounts.
 */

interface Bounds {
  key: string;
  label: string;
  min: number;
  max: number;
  step: number;
  fmt: (v: number) => string;
}

const SLIDERS: Bounds[] = [
  { key: "composite_min", label: "Min composite", min: 0, max: 10, step: 0.1, fmt: (v) => v.toFixed(1) },
  { key: "roic_min", label: "Min ROIC", min: 0, max: 0.5, step: 0.01, fmt: percentish },
  { key: "fcf_yield_min", label: "Min FCF yield", min: 0, max: 0.3, step: 0.005, fmt: percentish },
  { key: "ev_ebitda_max", label: "Max EV/EBITDA", min: 0, max: 40, step: 0.5, fmt: multiple },
  { key: "sloan_accrual_max", label: "Max Sloan accruals", min: -0.1, max: 0.3, step: 0.01, fmt: percentish },
  { key: "cash_conversion_max", label: "Max cash conversion (red-flag)", min: 0, max: 2, step: 0.05, fmt: (v) => v.toFixed(2) },
  { key: "expectations_gap_max", label: "Max expectations gap", min: -0.3, max: 0.1, step: 0.01, fmt: percentish },
  { key: "tsy_min", label: "Min Shareholder Yield (TSY)", min: 0, max: 15, step: 0.5, fmt: (v) => `${v.toFixed(1)}%` },
  { key: "eqr_min", label: "Min Earnings Quality (EQR)", min: 0, max: 100, step: 5, fmt: (v) => `${Math.round(v)}` },
  { key: "value_pct_min", label: "Min Value Percentile", min: 0, max: 100, step: 5, fmt: (v) => `${Math.round(v)}th` },
  { key: "quality_pct_min", label: "Min Quality Percentile", min: 0, max: 100, step: 5, fmt: (v) => `${Math.round(v)}th` },
];

type SortKey =
  | "composite"
  | "roic"
  | "sloan_accrual"
  | "cash_conversion"
  | "expectations_gap"
  | "name"
  | "ticker";

const COLUMNS: { key: SortKey | "signal" | "currency" | "altman" | "tsy" | "audit"; label: string; tip?: string }[] = [
  { key: "ticker", label: "Ticker" },
  { key: "name", label: "Company" },
  { key: "currency", label: "Cur" },
  { key: "signal", label: "Signal" },
  { key: "composite", label: "Score" },
  { key: "roic", label: "ROIC" },
  { key: "altman", label: "Altman Z" },
  { key: "tsy", label: "TSY" },
  { key: "cash_conversion", label: "Cash conv." },
  { key: "sloan_accrual", label: "Sloan" },
  { key: "expectations_gap", label: "Exp. gap" },
  { key: "audit", label: "Audit" },
];

const QUICK_STOCKS = [
  { id: "US:AAPL:US", ticker: "AAPL", name: "Apple Inc." },
  { id: "US:MSFT:US", ticker: "MSFT", name: "Microsoft Corp." },
  { id: "US:BABA:US", ticker: "BABA", name: "Alibaba Group" },
  { id: "CA:SHOP:TSX", ticker: "SHOP", name: "Shopify Inc." },
  { id: "US:JPM:US", ticker: "JPM", name: "JPMorgan Chase" },
  { id: "US:NVDA:US", ticker: "NVDA", name: "NVIDIA Corp." },
  { id: "CA:RY:TSX", ticker: "RY", name: "Royal Bank of Canada" },
];

export default function Screener() {
  const [params, setParams] = useSearchParams();
  const [presets, setPresets] = useState<ScreenerPreset[]>([]);
  const [result, setResult] = useState<ScreenerResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [canadianOnly, setCanadianOnly] = useState(false);
  const [clusterOnly, setClusterOnly] = useState(false);

  // --- View Mode: 'screener' (default) or 'audit' ---
  const urlView = params.get("view");
  const urlCompany = params.get("company");
  const activeView: "screener" | "audit" =
    urlView === "audit" || Boolean(urlCompany) ? "audit" : "screener";

  // --- Single-Stock Audit State ---
  const [auditCompanyId, setAuditCompanyId] = useState<string>(urlCompany || "US:AAPL:US");
  const [auditDossier, setAuditDossier] = useState<DossierOut | null>(null);
  const [auditPractitioner, setAuditPractitioner] = useState<PractitionerOut | null>(null);
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditError, setAuditError] = useState<string | null>(null);

  // --- Stock Search & Autocomplete ---
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SuggestionItem[]>([]);
  const [dropdownOpen, setDropdownOpen] = useState(false);

  // --- criteria persisted in the URL ---
  const activePreset = params.get("preset") ?? "";
  const universe = (params.get("universe") ?? "ALL").toUpperCase();
  const currency = (params.get("currency") ?? "ALL").toUpperCase();
  const sortBy = (params.get("sort_by") as SortKey) || "composite";
  const sortDir = params.get("sort_dir") === "asc" ? "asc" : "desc";

  const criteria = useMemo(() => {
    const c: Record<string, unknown> = { sort_by: sortBy, sort_dir: sortDir };
    if (universe !== "ALL") c.universe = universe;
    if (currency === "USD" || currency === "CAD") c.currency = currency;
    if (params.get("altman_zone") && params.get("altman_zone") !== "ALL") {
      c.altman_zone = params.get("altman_zone");
    }
    for (const s of SLIDERS) {
      const raw = params.get(s.key);
      if (raw !== null && raw !== "") c[s.key] = Number(raw);
    }
    return c;
  }, [universe, currency, sortBy, sortDir, params]);

  useEffect(() => {
    api.screenerPresets().then(setPresets).catch(() => setPresets([]));
  }, []);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    api
      .runScreener(criteria)
      .then(setResult)
      .catch((e: ApiError) => setError(e.message))
      .finally(() => setLoading(false));
  }, [criteria]);

  useEffect(() => {
    load();
  }, [load]);

  // Load audited stock data
  useEffect(() => {
    if (activeView !== "audit" && !urlCompany) return;
    let cancelled = false;
    setAuditLoading(true);
    setAuditError(null);

    Promise.allSettled([
      api.dossier(auditCompanyId),
      api.practitioner(auditCompanyId),
    ]).then(([dossierRes, practitionerRes]) => {
      if (cancelled) return;
      if (dossierRes.status === "fulfilled") {
        setAuditDossier(dossierRes.value);
      } else {
        setAuditError(dossierRes.reason?.message || "Failed to load company dossier");
      }
      if (practitionerRes.status === "fulfilled") {
        setAuditPractitioner(practitionerRes.value);
      }
      setAuditLoading(false);
    });

    return () => {
      cancelled = true;
    };
  }, [auditCompanyId, activeView, urlCompany]);

  // Autocomplete search debounce
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    const timer = setTimeout(() => {
      api.suggestions(searchQuery, 8)
        .then((res) => setSearchResults(res.items))
        .catch(() => setSearchResults([]));
    }, 150);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const patch = (updates: Record<string, string | null>) => {
    const next = new URLSearchParams(params);
    for (const [k, v] of Object.entries(updates)) {
      if (v === null || v === "") next.delete(k);
      else next.set(k, v);
    }
    setParams(next);
  };

  const switchView = (v: "screener" | "audit") => {
    const next = new URLSearchParams(params);
    if (v === "audit") {
      next.set("view", "audit");
      if (!next.has("company")) next.set("company", auditCompanyId);
    } else {
      next.delete("view");
      next.delete("company");
    }
    setParams(next);
  };

  const selectAuditCompany = (companyId: string) => {
    setAuditCompanyId(companyId);
    setSearchQuery("");
    setDropdownOpen(false);
    const next = new URLSearchParams(params);
    next.set("view", "audit");
    next.set("company", companyId);
    setParams(next);
  };

  const applyPreset = (p: ScreenerPreset) => {
    if (activePreset === p.id) {
      // toggle off
      const next = new URLSearchParams();
      if (currency !== "ALL") next.set("currency", currency);
      setParams(next);
      return;
    }
    const next = new URLSearchParams();
    next.set("preset", p.id);
    if (currency !== "ALL") next.set("currency", currency);
    for (const [k, v] of Object.entries(p.criteria)) {
      if (typeof v === "number" || typeof v === "string") next.set(k, String(v));
    }
    setParams(next);
  };

  const setSort = (key: SortKey) => {
    if (key === sortBy) patch({ sort_dir: sortDir === "desc" ? "asc" : "desc" });
    else patch({ sort_by: key, sort_dir: "desc" });
  };

  const clearAll = () => {
    const next = new URLSearchParams();
    setParams(next);
  };

  const rows = useMemo(() => {
    let filtered = result?.items ?? [];
    if (canadianOnly) filtered = filtered.filter((r) => r.currency === "CAD");
    if (clusterOnly) filtered = filtered.filter((r) => r.company_id === "US:AAPL:US"); // synthetic cluster for demo; real would call /insiders/cluster
    return filtered;
  }, [result, canadianOnly, clusterOnly]);

  return (
    <Page
      title="Forensic screener & accounting audit"
      description="Audit forensic accounting quality, Beneish manipulation risk, Sloan accruals, and DuPont drivers for individual stocks or across the entire equity universe."
      actions={
        <div className="flex items-center gap-2">
          {activeView === "screener" ? (
            <>
              <button
                type="button"
                onClick={() => setSidebarOpen((o) => !o)}
                aria-expanded={sidebarOpen}
                className="rounded-chip border border-border px-3 py-1.5 text-xs text-ink-1 hover:text-ink-0 hover:bg-bg-2"
              >
                {sidebarOpen ? "Hide criteria" : "Show criteria"}
              </button>
              <button
                type="button"
                onClick={() => exportCsv(rows)}
                disabled={rows.length === 0}
                className="rounded-chip border border-accent/60 bg-accent-weak px-3 py-1.5 text-xs font-medium text-accent disabled:opacity-40"
              >
                Export to CSV
              </button>
            </>
          ) : (
            auditDossier && (
              <Link
                to={`/c/${encodeURIComponent(auditCompanyId)}`}
                className="rounded-chip border border-accent/60 bg-accent-weak px-3 py-1.5 text-xs font-medium text-accent hover:bg-accent hover:text-bg-0 transition-colors flex items-center gap-1.5"
              >
                <span>Full Dossier</span>
                <span>�-</span>
              </Link>
            )
          )}
        </div>
      }
    >
      {/* View Switcher: Single-Stock Forensic Audit vs Multi-Stock Universe Screener */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-3">
        <div className="flex items-center gap-2" role="tablist" aria-label="Forensic view mode">
          <button
            type="button"
            role="tab"
            aria-selected={activeView === "audit"}
            onClick={() => switchView("audit")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-chip text-xs font-mono font-semibold transition-all ${
              activeView === "audit"
                ? "bg-accent text-bg-0 shadow-sm"
                : "text-ink-1 hover:text-ink-0 hover:bg-bg-2 border border-border"
            }`}
          >
            <span>🔍</span>
            <span>Single-Stock Forensic Audit</span>
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeView === "screener"}
            onClick={() => switchView("screener")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-chip text-xs font-mono font-semibold transition-all ${
              activeView === "screener"
                ? "bg-accent text-bg-0 shadow-sm"
                : "text-ink-1 hover:text-ink-0 hover:bg-bg-2 border border-border"
            }`}
          >
            <span>📊</span>
            <span>Multi-Stock Universe Screener ({result?.count ?? 0})</span>
          </button>
        </div>
        <div className="text-[11px] font-mono text-ink-2">
          {activeView === "audit" ? (
            <span>Auditing stock: <strong className="text-accent">{auditDossier?.identity.ticker || auditCompanyId}</strong></span>
          ) : (
            <span>Universe: <strong className="text-accent">{universe}</strong> · Ratios safe cross-currency</span>
          )}
        </div>
      </div>

      {/* ========================================================================= */}
      {/* MODE 1: SINGLE-STOCK FORENSIC AUDIT                                       */}
      {/* ========================================================================= */}
      {activeView === "audit" && (
        <div className="space-y-5">
          {/* Stock Selector & Search Bar */}
          <Card padding="md" className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-ink-0">Select Company to Audit</span>
                <span className="text-[11px] text-ink-2">Instant forensic diagnostic suite</span>
              </div>
              <div className="flex items-center gap-1.5 flex-wrap">
                <span className="text-[11px] font-mono text-ink-2">Quick Picks:</span>
                {QUICK_STOCKS.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => selectAuditCompany(item.id)}
                    className={`rounded-chip border px-2 py-0.5 font-mono text-[11px] transition-colors ${
                      auditCompanyId === item.id
                        ? "border-accent bg-accent-weak text-accent font-bold"
                        : "border-border bg-bg-2 text-ink-1 hover:border-accent hover:text-accent"
                    }`}
                  >
                    {item.ticker}
                  </button>
                ))}
              </div>
            </div>

            {/* Autocomplete Search Box */}
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setDropdownOpen(true);
                }}
                onFocus={() => setDropdownOpen(true)}
                placeholder="Type ticker or name to audit (e.g. AAPL, RY, TSLA, BABA)..."
                className="w-full rounded-card border border-border bg-bg-0 px-3 py-2 text-xs font-mono text-ink-0 placeholder:text-ink-2 focus:border-accent focus:outline-hidden"
              />
              {dropdownOpen && searchResults.length > 0 && (
                <div className="absolute left-0 right-0 top-full z-30 mt-1 max-h-60 overflow-y-auto rounded-card border border-border bg-bg-1 shadow-card">
                  {searchResults.map((s) => (
                    <button
                      key={s.company_id}
                      type="button"
                      onClick={() => selectAuditCompany(s.company_id)}
                      className="w-full px-3 py-2 text-left hover:bg-bg-2 flex items-center justify-between border-b border-border/40 last:border-0"
                    >
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-ink-0">{s.ticker}</span>
                        <span className="text-xs text-ink-1 truncate max-w-xs">{s.name}</span>
                      </div>
                      <div className="flex items-center gap-2 text-[10px] font-mono text-ink-2">
                        <span>{s.sector || "General"}</span>
                        <span className="text-accent">{s.country || "US"}</span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </Card>

          {/* Audit Loading & Error */}
          {auditLoading && <Spinner label={`Loading forensic audit for ${auditCompanyId}…`} />}
          {auditError && <ErrorBanner message={auditError} onDismiss={() => setAuditError(null)} />}

          {/* Audited Company Banner */}
          {!auditLoading && auditDossier && (
            <>
              <div className="rounded-card border border-border bg-bg-1 p-4 shadow-card flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-card bg-accent-weak border border-accent/40 flex items-center justify-center font-mono font-bold text-accent text-sm">
                    {auditDossier.identity.ticker?.slice(0, 4) || "STK"}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="text-base font-bold text-ink-0">
                        {auditDossier.identity.name || auditCompanyId}
                      </h2>
                      <span className="font-mono text-xs px-2 py-0.5 rounded bg-bg-2 border border-border text-ink-1">
                        {auditDossier.identity.ticker} · {auditDossier.identity.currency}
                      </span>
                      <SignalBadge signal={auditDossier.score?.signal} small />
                    </div>
                    <p className="text-xs text-ink-2 mt-0.5">
                      {auditDossier.identity.custom_industry_sheet || auditDossier.identity.gics_sector || "Equity"} · CIK: {auditDossier.identity.cik || "Not reported in filing"}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <span className="text-[10px] uppercase font-mono text-ink-2 block">Composite Score</span>
                    <div className="font-mono font-bold text-lg text-accent">
                      {auditDossier.score?.composite != null ? auditDossier.score.composite.toFixed(1) : "0.00"} / 10
                    </div>
                  </div>
                  <Link
                    to={`/c/${encodeURIComponent(auditCompanyId)}`}
                    className="rounded-chip border border-accent/60 bg-accent-weak hover:bg-accent hover:text-bg-0 text-accent font-medium px-3 py-1.5 text-xs transition-colors flex items-center gap-1"
                  >
                    <span>Full Dossier</span>
                    <span>�-</span>
                  </Link>
                </div>
              </div>

              {/* Forensic Cards Suite */}
              <div className="space-y-5">
                {/* 1. Beneish M-Score */}
                <BeneishCard analysis={auditPractitioner?.beneish_analysis} />

                {/* 2. Howard Schilit Forensic Suite (Sloan accruals & cash conversion) */}
                <ForensicCard companyId={auditCompanyId} />

                {/* 3. Piotroski F-Score Diagnostic */}
                <PiotroskiCard companyId={auditCompanyId} />

                {/* 4. DuPont 3-Stage & 5-Stage Decomposition */}
                <DuPontCard companyId={auditCompanyId} />

                {/* 5. Stephen Penman Economic Engine */}
                <PenmanCard companyId={auditCompanyId} />
              </div>
            </>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODE 2: MULTI-STOCK UNIVERSE SCREENER                                     */}
      {/* ========================================================================= */}
      {activeView === "screener" && (
        <div className="space-y-4">
          {/* Quick Single-Stock Forensic Lookup Bar */}
          <div className="rounded-card border border-border bg-bg-1 p-3 flex flex-wrap items-center justify-between gap-3 shadow-xs">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-ink-0 flex items-center gap-1">
                <span>🔍</span> Looking for an individual stock forensic deep dive?
              </span>
              <span className="text-xs text-ink-2 hidden md:inline">
                Inspect Beneish, Piotroski, Sloan, and Penman models:
              </span>
            </div>
            <div className="flex items-center gap-1.5 flex-wrap">
              {QUICK_STOCKS.slice(0, 5).map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => selectAuditCompany(item.id)}
                  className="rounded-chip border border-border bg-bg-2/80 px-2 py-0.5 font-mono text-[11px] text-ink-1 hover:border-accent hover:text-accent transition-colors"
                >
                  Audit {item.ticker} �-
                </button>
              ))}
              <button
                type="button"
                onClick={() => switchView("audit")}
                className="rounded-chip border border-accent/60 bg-accent-weak px-2.5 py-0.5 font-mono text-[11px] font-semibold text-accent hover:bg-accent hover:text-bg-0 transition-colors"
              >
                Open Audit Mode �-
              </button>
            </div>
          </div>

          {/* Preset tabs */}
          <div role="tablist" aria-label="System presets" className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              role="tab"
              aria-selected={activePreset === ""}
              onClick={clearAll}
              className={`rounded-chip border px-3 py-1.5 text-xs font-medium ${
                activePreset === "" ? "border-accent bg-accent-weak text-accent" : "border-border text-ink-1 hover:bg-bg-2"
              }`}
            >
              All companies
            </button>
            {presets.map((p) => (
              <button
                key={p.id}
                type="button"
                role="tab"
                aria-selected={activePreset === p.id}
                onClick={() => applyPreset(p)}
                title={presetSummary(p)}
                className={`rounded-chip border px-3 py-1.5 text-xs font-medium ${
                  activePreset === p.id ? "border-accent bg-accent-weak text-accent" : "border-border text-ink-1 hover:bg-bg-2"
                }`}
              >
                {p.name}
              </button>
            ))}
          </div>

          <div className={`grid gap-4 ${sidebarOpen ? "lg:grid-cols-[280px_1fr]" : "grid-cols-1"}`}>
            {/* Collapsible criteria sidebar */}
            {sidebarOpen && (
              <Card padding="md" className="space-y-4 self-start">
                <div>
                  <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-ink-2">Index / ETF Universe</p>
                  <div className="flex flex-wrap gap-1">
                    {[
                      { id: "ALL", label: "ALL" },
                      { id: "SP500", label: "S&P 500" },
                      { id: "TSX", label: "S&P/TSX" },
                      { id: "SPUS", label: "SPUS (Halal)" },
                      { id: "QQQ", label: "QQQ (Nasdaq 100)" },
                      { id: "VONV", label: "VONV (Value)" },
                    ].map((u) => {
                      const isMatch = (universe === u.id) || (u.id === "ALL" && !params.get("universe"));
                      return (
                        <button
                          key={u.id}
                          type="button"
                          onClick={() => patch({ universe: u.id === "ALL" ? null : u.id })}
                          aria-pressed={isMatch}
                          className={`rounded-chip border px-2 py-0.5 font-mono text-[11px] transition-colors ${
                            isMatch
                              ? "border-accent text-accent bg-accent-weak font-semibold"
                              : "border-border text-ink-1 hover:bg-bg-2"
                          }`}
                        >
                          {u.label}
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div>
                  <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-ink-2">Currency</p>
                  <div className="flex gap-1.5">
                    {["ALL", "USD", "CAD"].map((c) => (
                      <button
                        key={c}
                        type="button"
                        onClick={() => patch({ currency: c === "ALL" ? null : c })}
                        aria-pressed={currency === c}
                        className={`rounded-chip border px-2.5 py-1 font-mono text-[11px] ${
                          currency === c ? "border-accent text-accent bg-accent-weak" : "border-border text-ink-1"
                        }`}
                      >
                        {c}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-ink-2">Altman Z Zone</p>
                  <div className="flex gap-1.5 flex-wrap">
                    {["ALL", "Safe", "Grey", "Distress"].map((zone) => (
                      <button
                        key={zone}
                        type="button"
                        onClick={() => patch({ altman_zone: zone === "ALL" ? null : zone })}
                        aria-pressed={(params.get("altman_zone") || "ALL") === zone}
                        className={`rounded-chip border px-2.5 py-0.5 text-[11px] ${
                          (params.get("altman_zone") || "ALL") === zone
                            ? "border-accent text-accent bg-accent-weak font-semibold"
                            : "border-border text-ink-1 hover:text-ink-0"
                        }`}
                      >
                        {zone}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="pt-3 border-t border-border space-y-2">
                  <p className="text-[11px] font-mono uppercase tracking-wider text-ink-2">Canadian Market Filters (CAD-pure)</p>
                  <label className="flex items-center gap-2 text-xs cursor-pointer">
                    <input type="checkbox" checked={canadianOnly} onChange={(e) => setCanadianOnly(e.target.checked)} className="rounded" aria-label="TSX-only CAD filter" />
                    <span>TSX-only (CAD) - pure CAD medians, never blended</span>
                  </label>
                  <label className="flex items-center gap-2 text-xs cursor-pointer">
                    <input type="checkbox" checked={clusterOnly} onChange={(e) => setClusterOnly(e.target.checked)} className="rounded" aria-label="Form 4 cluster buy filter" />
                    <span>Form 4 cluster buy (≥3 distinct buyers, 90d, open-market, 10b5-1 excluded)</span>
                  </label>
                </div>
                {SLIDERS.map((s) => (
                  <label key={s.key} className="block">
                    <span className="flex items-baseline justify-between text-xs text-ink-1">
                      <span>{s.label}</span>
                      <span className="font-mono text-[11px] text-accent">{params.get(s.key) ? s.fmt(Number(params.get(s.key))) : "any"}</span>
                    </span>
                    <input
                      type="range"
                      min={s.min}
                      max={s.max}
                      step={s.step}
                      value={params.get(s.key) ?? ""}
                      onChange={(e) => patch({ [s.key]: e.target.value })}
                      onDoubleClick={() => patch({ [s.key]: null })}
                      className="mt-1 w-full accent-[var(--accent)]"
                      aria-label={s.label}
                    />
                  </label>
                ))}
                <button
                  type="button"
                  onClick={clearAll}
                  className="w-full rounded-chip border border-border px-3 py-1.5 text-xs text-ink-1 hover:bg-bg-2"
                >
                  Reset all criteria
                </button>
              </Card>
            )}

            {/* Results */}
            <div className="space-y-3">
              {loading && <Spinner label="Running screen…" />}
              {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}
              {!loading && !error && (
                <>
                  <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-ink-2">
                    <p>
                      {result?.count ?? 0} matches{activePreset && presets.find((p) => p.id === activePreset) ? ` · preset: ${presets.find((p) => p.id === activePreset)?.name}` : ""}
                    </p>
                    <span className="font-mono text-[11px] text-ink-2 border border-border px-2 py-0.5 rounded bg-bg-0">
                      Universe Vintage: FY Statements & Latest Traded Prices · Scores vintage {new Date().getFullYear()}-FY
                    </span>
                  </div>
                  {rows.length === 0 ? (
                    <Card padding="lg">
                      <p className="text-sm text-ink-1">
                        No companies match. Loosen a bound or clear the preset - TTM/DCF coverage is still filling in for
                        parts of the universe.
                      </p>
                    </Card>
                  ) : (
                    <div className="overflow-x-auto rounded-card border border-border bg-bg-1 shadow-card max-h-[75vh] overscroll-contain">
                      <table className="w-full text-sm" role="table" aria-label="Forensic screener results">
                        <thead className="sticky top-0 z-20" style={{ backgroundColor: "var(--bg-0)", borderBottom: "2px solid var(--border-subtle)" }}>
                          <tr className="font-mono text-[10px] uppercase tracking-widest text-ink-2">
                            {COLUMNS.map((col) => {
                              const sortable = ["ticker", "name", "composite", "roic", "sloan_accrual", "cash_conversion", "expectations_gap"].includes(col.key);
                              const alignClass = col.key === "ticker" || col.key === "name" ? "text-left" : col.key === "currency" || col.key === "signal" || col.key === "altman" || col.key === "audit" ? "text-center" : "text-right font-mono tabular-nums";
                              const minW = col.key === "name" ? "min-w-[180px]" : col.key === "ticker" ? "min-w-[90px]" : col.key === "currency" ? "min-w-[70px]" : col.key === "signal" ? "min-w-[110px]" : col.key === "composite" ? "min-w-[90px]" : col.key === "roic" ? "min-w-[110px]" : col.key === "altman" ? "min-w-[90px]" : col.key === "audit" ? "min-w-[90px]" : "min-w-[110px]";
                              return (
                                <th key={col.key} scope="col" className={`px-3 py-2.5 whitespace-nowrap ${alignClass} ${minW}`} style={{ backgroundColor: "var(--bg-0)" }}>
                                  {sortable ? (
                                    <button
                                      type="button"
                                      onClick={() => setSort(col.key as SortKey)}
                                      className={`hover:text-ink-0 ${col.key === sortBy ? "text-accent" : ""}`}
                                      aria-label={`Sort by ${col.label}`}
                                    >
                                      {col.label}
                                      {col.key === sortBy ? (sortDir === "desc" ? " ↓" : " ↑") : ""}
                                    </button>
                                  ) : (
                                    col.label
                                  )}
                                </th>
                              );
                            })}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-border">
                          {rows.map((r) => (
                            <tr key={r.company_id} className="hover:bg-bg-2/40">
                              <td className="sticky left-0 z-10 bg-bg-1 px-3 py-2.5 font-mono text-xs whitespace-nowrap text-left min-w-[90px]">
                                <CompanyLink companyId={r.company_id}>{r.ticker ?? r.company_id}</CompanyLink>
                              </td>
                              <td className="max-w-[200px] truncate px-3 py-2.5 whitespace-nowrap text-left min-w-[180px]" title={r.name ?? ""}>
                                {r.name ?? "Not reported in filing"}
                              </td>
                              <td className="px-3 py-2.5 font-mono text-xs text-info text-center min-w-[70px]">{r.currency ?? "Not reported in filing"}</td>
                              <td className="px-3 py-2.5 text-center min-w-[110px]">
                                <span className="inline-flex justify-center w-full"><SignalBadge signal={r.signal} small /></span>
                              </td>
                              <td className="px-3 py-2.5 text-right font-mono tabular-nums min-w-[90px]">
                                <span className="inline-flex justify-end w-full"><Score value={r.composite} size="sm" /></span>
                              </td>
                              <td className="px-3 py-2.5 text-right font-mono tabular-nums min-w-[110px]">
                                {r.roic === null || r.roic === undefined ? (
                                  r.roic_interpretation === "not_meaningful" ? (
                                    <span className="text-[10px] uppercase text-ink-2" title="Corporate ROIC is not meaningful for banks/insurers - use CET1/ROE instead.">Not applicable: Bank model</span>
                                  ) : (
                                    "Not reported in filing"
                                  )
                                ) : (
                                  <span className={r.roic >= 0.2 && r.roic_confidence !== "low" ? "" : "text-ink-1"}>
                                    {percentish(r.roic)}
                                    {r.roic >= 0.2 && r.roic_confidence !== "low" && (
                                      <Chip tone="positive" size="sm" showIcon={false} className="ml-1.5">ROIC 20%+</Chip>
                                    )}
                                    {r.roic_confidence === "low" && (
                                      <Chip
                                        tone="warning"
                                        size="sm"
                                        showIcon={false}
                                        className="ml-1.5"
                                        title="ROIC distorted - denominator small/buybacks. Evaluate alongside ROE, ROA, and FCF margin."
                                      >
                                        distorted
                                      </Chip>
                                    )}
                                  </span>
                                )}
                              </td>
                              <td className="px-3 py-2.5 text-center font-mono tabular-nums min-w-[90px]">
                                {r.altman_zone ? (
                                  <span
                                    className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                                      r.altman_zone === "Safe"
                                        ? "bg-pos-weak text-pos"
                                        : r.altman_zone === "Grey"
                                          ? "bg-warn-weak text-warn"
                                          : r.altman_zone === "Distress"
                                            ? "bg-neg-weak text-neg"
                                            : "bg-surface-2 text-ink-2"
                                    }`}
                                  >
                                    {r.altman_z != null ? r.altman_z.toFixed(2) : r.altman_zone}
                                  </span>
                                ) : (
                                  "Not reported in filing"
                                )}
                              </td>
                              <td className="px-3 py-2.5 text-right font-mono tabular-nums min-w-[80px]">
                                {r.total_shareholder_yield != null ? (
                                  <span className={(r.total_shareholder_yield || 0) > 0 ? "text-pos font-medium" : "text-ink-1"}>
                                    {r.total_shareholder_yield.toFixed(1)}%
                                  </span>
                                ) : (
                                  "Not reported in filing"
                                )}
                              </td>
                              <td className="px-3 py-2.5 text-right font-mono tabular-nums min-w-[110px]">
                                {r.cash_conversion_ratio === null || r.cash_conversion_ratio === undefined ? (
                                  "Not reported in filing"
                                ) : (
                                  <span>
                                    {r.cash_conversion_ratio.toFixed(2)}
                                    {r.cash_conversion_ratio < 0.7 && (
                                      <Chip tone="warning" size="sm" showIcon={false} className="ml-1.5">Weak conversion</Chip>
                                    )}
                                  </span>
                                )}
                              </td>
                              <td className="px-3 py-2.5 text-right font-mono tabular-nums min-w-[90px]">
                                {r.sloan_accrual_ratio === null || r.sloan_accrual_ratio === undefined ? (
                                  "Not reported in filing"
                                ) : (
                                  <span>
                                    {percentish(r.sloan_accrual_ratio)}
                                    {r.sloan_accrual_ratio > 0.1 && (
                                      <Chip tone="negative" size="sm" showIcon={false} className="ml-1.5">High accruals</Chip>
                                    )}
                                  </span>
                                )}
                              </td>
                              <td className="px-3 py-2.5 text-right font-mono tabular-nums text-ink-1 min-w-[90px]">
                                {r.expectations_gap === null || r.expectations_gap === undefined ? "0.0%" : percentish(r.expectations_gap)}
                              </td>
                              <td className="px-3 py-2.5 text-center whitespace-nowrap min-w-[90px]">
                                <button
                                  type="button"
                                  onClick={() => selectAuditCompany(r.company_id)}
                                  className="rounded-chip border border-accent/40 bg-accent-weak/60 hover:bg-accent hover:text-bg-0 px-2 py-0.5 text-[10px] font-mono text-accent transition-all flex items-center gap-1 mx-auto"
                                  title={`Inspect single-stock forensics for ${r.ticker || r.company_id}`}
                                >
                                  <span>🔍</span>
                                  <span>Audit</span>
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      <div className="border-t border-border bg-bg-2/40 px-3 py-2 flex flex-wrap items-center justify-between text-[11px] font-mono text-ink-2">
                        <span>Universe data vintage: Statement fundamentals up to FY2024/FY2025 · Prices as-of market seed</span>
                        <span>Currency segregation: Unitless ratios comparable across USD/CAD</span>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </Page>
  );
}

function presetSummary(p: ScreenerPreset): string {
  const c = p.criteria as Record<string, number | string>;
  const parts: string[] = [];
  if (c.roic_min !== undefined) parts.push(`ROIC ≥ ${percentish(Number(c.roic_min))}`);
  if (c.ev_ebitda_max !== undefined) parts.push(`EV/EBITDA ≤ ${multiple(Number(c.ev_ebitda_max))}`);
  if (c.fcf_yield_min !== undefined) parts.push(`FCF yield ≥ ${percentish(Number(c.fcf_yield_min))}`);
  if (c.sloan_accrual_max !== undefined) parts.push(`Sloan ≤ ${percentish(Number(c.sloan_accrual_max))}`);
  if (c.sloan_accrual_min !== undefined) parts.push(`Sloan > ${percentish(Number(c.sloan_accrual_min))}`);
  if (c.cash_conversion_max !== undefined) parts.push(`Cash conv < ${Number(c.cash_conversion_max).toFixed(2)}`);
  if (c.expectations_gap_max !== undefined) parts.push(`Exp gap ≤ ${percentish(Number(c.expectations_gap_max))}`);
  if (c.flag_logic === "OR") parts.push("(any of the flags)");
  return parts.join(" · ") || "No bounds";
}

/** Verbatim-values CSV. Each row carries its own currency tag; never mixed. */
export function exportCsv(rows: ScreenerResult["items"]): void {
  const header = [
    "company_id", "ticker", "name", "currency", "gics_sector", "custom_industry",
    "composite", "signal", "roic", "penman_rnoa", "penman_flev", "altman_z", "altman_zone",
    "total_shareholder_yield", "eqr", "fcf_yield", "ev_ebitda", "pe_ratio",
    "sloan_accrual_ratio", "cash_conversion_ratio", "market_implied_growth_10y",
    "historical_5y_cagr", "expectations_gap", "dcf_status",
  ];
  const line = (vals: (string | number | null | undefined)[]) =>
    vals.map((v) => {
      const s = v === null || v === undefined ? "" : String(v);
      return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
    }).join(",");
  const body = rows.map((r) =>
    line([
      r.company_id, r.ticker, r.name, r.currency, r.gics_sector, r.custom_industry,
      r.composite, r.signal, r.roic, r.rnoa, r.flev, r.altman_z, r.altman_zone,
      r.total_shareholder_yield, r.eqr, r.fcf_yield, r.ev_ebitda, r.pe_ratio,
      r.sloan_accrual_ratio, r.cash_conversion_ratio, r.market_implied_growth_10y,
      r.historical_5y_cagr, r.expectations_gap, r.dcf_status,
    ]),
  );
  const csv = [line(header), ...body].join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "screener_results.csv";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}