import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { ScreenerPreset, ScreenerResult } from "../api/types";
import { CompanyLink, ErrorBanner, Score, SignalBadge, Spinner } from "../components/ui";
import { Card, Chip, Page } from "../components/layout";
import { multiple, percentish } from "../lib/format";

/**
 * Forensic multi-metric screener (directive §4).
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
];

type SortKey =
  | "composite"
  | "roic"
  | "sloan_accrual"
  | "cash_conversion"
  | "expectations_gap"
  | "name"
  | "ticker";

const COLUMNS: { key: SortKey | "signal" | "currency"; label: string; tip?: string }[] = [
  { key: "ticker", label: "Ticker" },
  { key: "name", label: "Company" },
  { key: "currency", label: "Cur" },
  { key: "signal", label: "Signal" },
  { key: "composite", label: "Score" },
  { key: "roic", label: "ROIC" },
  { key: "cash_conversion", label: "Cash conv." },
  { key: "sloan_accrual", label: "Sloan" },
  { key: "expectations_gap", label: "Exp. gap" },
];

export default function Screener() {
  const [params, setParams] = useSearchParams();
  const [presets, setPresets] = useState<ScreenerPreset[]>([]);
  const [result, setResult] = useState<ScreenerResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // --- criteria persisted in the URL ---
  const activePreset = params.get("preset") ?? "";
  const currency = (params.get("currency") ?? "ALL").toUpperCase();
  const sortBy = (params.get("sort_by") as SortKey) || "composite";
  const sortDir = params.get("sort_dir") === "asc" ? "asc" : "desc";

  const criteria = useMemo(() => {
    const c: Record<string, unknown> = { sort_by: sortBy, sort_dir: sortDir };
    if (currency === "USD" || currency === "CAD") c.currency = currency;
    for (const s of SLIDERS) {
      const raw = params.get(s.key);
      if (raw !== null && raw !== "") c[s.key] = Number(raw);
    }
    return c;
  }, [currency, sortBy, sortDir, params]);

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

  const patch = (updates: Record<string, string | null>) => {
    const next = new URLSearchParams(params);
    for (const [k, v] of Object.entries(updates)) {
      if (v === null || v === "") next.delete(k);
      else next.set(k, v);
    }
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

  const rows = result?.items ?? [];

  return (
    <Page
      title="Forensic screener"
      description="Deep-value and accounting-quality screens over TTM forensics and reverse-DCF expectations. All metrics are unitless ratios — safe to compare across USD and CAD."
      actions={
        <div className="flex items-center gap-2">
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
        </div>
      }
    >
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
              <p className="text-xs text-ink-2">
                {result?.count ?? 0} matches{activePreset && presets.find((p) => p.id === activePreset) ? ` · preset: ${presets.find((p) => p.id === activePreset)?.name}` : ""}
              </p>
              {rows.length === 0 ? (
                <Card padding="lg">
                  <p className="text-sm text-ink-1">
                    No companies match. Loosen a bound or clear the preset — TTM/DCF coverage is still filling in for
                    parts of the universe.
                  </p>
                </Card>
              ) : (
                <div className="overflow-x-auto rounded-card border border-border bg-bg-1 shadow-card">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border bg-bg-2/60 text-left font-mono text-[10px] uppercase tracking-widest text-ink-2">
                        {COLUMNS.map((col) => {
                          const sortable = ["ticker", "name", "composite", "roic", "sloan_accrual", "cash_conversion", "expectations_gap"].includes(col.key);
                          return (
                            <th key={col.key} scope="col" className="px-3 py-2.5 whitespace-nowrap">
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
                          <td className="sticky left-0 z-10 bg-bg-1 px-3 py-2 font-mono text-xs whitespace-nowrap">
                            <CompanyLink companyId={r.company_id}>{r.ticker ?? r.company_id}</CompanyLink>
                          </td>
                          <td className="max-w-[220px] truncate px-3 py-2 whitespace-nowrap" title={r.name ?? ""}>
                            {r.name ?? "—"}
                          </td>
                          <td className="px-3 py-2 font-mono text-xs text-info">{r.currency ?? "—"}</td>
                          <td className="px-3 py-2">
                            <SignalBadge signal={r.signal} small />
                          </td>
                          <td className="px-3 py-2 text-right font-mono tabular-nums">
                            <Score value={r.composite} size="sm" />
                          </td>
                          <td className="px-3 py-2 text-right font-mono tabular-nums">
                            {r.roic === null || r.roic === undefined ? (
                              "—"
                            ) : (
                              <span className={r.roic >= 0.2 ? "" : "text-ink-1"}>
                                {percentish(r.roic)}
                                {r.roic >= 0.2 && (
                                  <Chip tone="positive" size="sm" showIcon={false} className="ml-1.5">ROIC 20%+</Chip>
                                )}
                              </span>
                            )}
                          </td>
                          <td className="px-3 py-2 text-right font-mono tabular-nums">
                            {r.cash_conversion_ratio === null || r.cash_conversion_ratio === undefined ? (
                              "—"
                            ) : (
                              <span>
                                {r.cash_conversion_ratio.toFixed(2)}
                                {r.cash_conversion_ratio < 0.7 && (
                                  <Chip tone="warning" size="sm" showIcon={false} className="ml-1.5">Weak conversion</Chip>
                                )}
                              </span>
                            )}
                          </td>
                          <td className="px-3 py-2 text-right font-mono tabular-nums">
                            {r.sloan_accrual_ratio === null || r.sloan_accrual_ratio === undefined ? (
                              "—"
                            ) : (
                              <span>
                                {percentish(r.sloan_accrual_ratio)}
                                {r.sloan_accrual_ratio > 0.1 && (
                                  <Chip tone="negative" size="sm" showIcon={false} className="ml-1.5">High accruals</Chip>
                                )}
                              </span>
                            )}
                          </td>
                          <td className="px-3 py-2 text-right font-mono tabular-nums text-ink-1">
                            {r.expectations_gap === null || r.expectations_gap === undefined ? "—" : percentish(r.expectations_gap)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </div>
      </div>
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
    "composite", "signal", "roic", "fcf_yield", "ev_ebitda", "pe_ratio",
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
      r.composite, r.signal, r.roic, r.fcf_yield, r.ev_ebitda, r.pe_ratio,
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
