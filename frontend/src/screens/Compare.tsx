import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { CompareOut, SearchOut } from "../api/types";
import { CompanyLink, ErrorBanner, HalalBadge, Spinner, useDebounced } from "../components/ui";
import { MiniPillarBars, Sparkline } from "../components/viz";
import { Card, Page } from "../components/layout";
import InfoTip from "../components/InfoTip";
import { mixedCurrencyWarning } from "../api/copy";
import { multiple, percentish } from "../lib/format";
import { COMPARE_MAX, useCompare, clearCompareSelection, COMPARE_EVENT } from "../lib/sessionCompare";

const MAX = COMPARE_MAX;

export default function Compare() {
  const [params, setParams] = useSearchParams();
  const showHalal = params.get("halal") === "1";
  const ids = (params.get("ids") ?? "").split(",").filter(Boolean).slice(0, MAX);
  const [data, setData] = useState<CompareOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Atomic event-driven basket - stays in sync with Dossier / AppShell via `compare-updated`
  const compare = useCompare();
  const [columnGroup, setColumnGroup] = useState<"core" | "forensics" | "dividends" | "banks">("core");

  const setIds = useCallback(
    (next: string[]) => {
      // Keep URL as source of truth for comparison view, but also persist to
      // localStorage atomically so AppShell badge and other tabs see it immediately.
      const sliced = next.filter(Boolean).slice(0, MAX);
      if (sliced.length) {
        try {
          localStorage.setItem("compareIds", JSON.stringify(sliced));
          window.dispatchEvent(new CustomEvent(COMPARE_EVENT, { detail: sliced }));
          window.dispatchEvent(new Event(COMPARE_EVENT));
        } catch {
          /* storage unavailable */
        }
      } else {
        try {
          localStorage.removeItem("compareIds");
          window.dispatchEvent(new CustomEvent(COMPARE_EVENT, { detail: [] }));
          window.dispatchEvent(new Event(COMPARE_EVENT));
        } catch {
          /* ignore */
        }
      }
      setParams(sliced.length ? { ids: sliced.join(",") } : {});
    },
    [setParams],
  );

  /** Explicit atomic clear: empties state, clears localStorage, dispatches
   *  `compare-updated`, and clears active comparison query parameters in the URL.
   */
  const clearCompare = useCallback(() => {
    // Clear localStorage + dispatch event via helper
    clearCompareSelection();
    // Ensure in-memory hook state also clears (dispatch already does, but be explicit)
    // Clearing URL query params
    setParams({}, { replace: true });
  }, [setParams]);

  // Keep URL ↔ basket in sync when basket is mutated elsewhere (e.g. Dossier "Add to Compare")
  useEffect(() => {
    const onCompareUpdated = () => {
      const basket = compare.ids;
      // If we're on /compare and basket was changed externally, optionally mirror to URL
      // Only auto-push when basket is non-empty and URL is empty (initial hydration)
      if (basket.length > 0 && ids.length === 0) {
        // Don't auto-navigate; user can click "Load basket"
      }
    };
    window.addEventListener(COMPARE_EVENT, onCompareUpdated);
    return () => window.removeEventListener(COMPARE_EVENT, onCompareUpdated);
  }, [compare.ids, ids.length]);

  useEffect(() => {
    if (ids.length < 2) {
      setData(null);
      return;
    }
    setLoading(true);
    setError(null);
    api
      .compare(ids)
      .then(setData)
      .catch((e: ApiError) => setError(e.message))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params]);

  const warning = data ? mixedCurrencyWarning(data.currencies) : null;

  return (
    <Page
      title="Compare companies"
      description="Pick 2 to 8 names. Ratios and scores are comparable across currencies; money amounts stay in each company's own currency and are never converted."
    >
      <AddRows ids={ids} onChange={setIds} />

      <div className="flex flex-wrap items-center gap-2" role="tablist" aria-label="Column selector">
        <span className="font-mono text-[11px] uppercase tracking-wider text-ink-2">Columns:</span>
        {(["core","forensics","dividends","banks"] as const).map((g) => (
          <button
            key={g}
            role="tab"
            aria-selected={columnGroup===g}
            onClick={() => setColumnGroup(g)}
            className={`px-2.5 py-1 rounded-chip text-xs font-mono border ${columnGroup===g ? "bg-accent text-bg-0 border-accent" : "bg-bg-0 text-ink-1 border-border hover:border-accent"}`}
          >
            {g === "core" ? "Core KPIs" : g === "forensics" ? "Forensics" : g === "dividends" ? "Dividend Safety" : "Bank Ratios"}
          </button>
        ))}
        <span className="text-[11px] text-ink-2 ml-1">Core: Market Cap, Composite, P/E, EV/EBITDA, ROIC, FCF Yield, Shareholder Yield, Altman Z, Net Debt/EBITDA</span>
      </div>

      {ids.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
          <span className="text-ink-2">Selected ({ids.length}/{MAX}):</span>
          {ids.map((id) => (
            <span key={id} className="inline-flex items-center gap-1 rounded-chip border border-border bg-bg-2 px-2 py-0.5 text-ink-0">
              <span>{id}</span>
              <button
                type="button"
                onClick={() => setIds(ids.filter((x) => x !== id))}
                className="text-ink-2 hover:text-neg ml-1"
                aria-label={`Remove ${id}`}
              >
                ✕
              </button>
            </span>
          ))}
          <button
            type="button"
            onClick={clearCompare}
            className="ml-2 rounded-chip border border-border px-2 py-0.5 text-ink-2 hover:text-neg hover:border-neg/40 transition-colors"
            aria-label="Clear all comparisons"
          >
            Clear all
          </button>
        </div>
      )}

      {compare.ids.length > 0 && compare.ids.join(",") !== ids.join(",") && (
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="text-ink-2">Basket ({compare.ids.length}/{MAX}): {compare.ids.join(", ")}</span>
          <button
            type="button"
            onClick={() => setIds(compare.ids)}
            className="rounded-chip border border-accent/60 bg-accent-weak px-2 py-0.5 text-accent hover:bg-accent/20 transition-colors"
          >
            Load basket → Compare
          </button>
          <button
            type="button"
            onClick={compare.clearCompare}
            className="rounded-chip border border-border px-2 py-0.5 text-ink-2 hover:text-neg transition-colors"
          >
            Clear basket
          </button>
        </div>
      )}

      {ids.length < 2 && compare.ids.length < 2 && (
        <p className="rounded-card border border-border bg-bg-1 p-4 text-xs text-ink-1" role="status" aria-live="polite">
          Add at least two companies to compare side by side.
        </p>
      )}

      {loading && <Spinner label="Comparing…" />}
      {error && <ErrorBanner message={error} />}

      {data && !loading && (
        <div className="space-y-5">
          {warning && (
            <div role="alert" className="rounded-card border border-warn/60 bg-warn-weak px-4 py-3 text-xs text-ink-0">
              {warning}
            </div>
          )}
          <Card padding="none" className="overflow-hidden">
            <div className="overflow-x-auto">
              <CompareTable data={data} showHalal={showHalal} columnGroup={columnGroup} />
            </div>
          </Card>
          <p className="text-xs text-ink-2">
            Best value per column is highlighted with a gold accent band (min PE/PB/EV-EBITDA, max ROE/composite). Not reported in filing means the field is not on file.
          </p>
          <CompareRadarOverlay rows={data.rows} />
          <CompareTrendOverlays ids={ids} />
          <CompareKPIDetail ids={ids} />
        </div>
      )}
    </Page>
  );
}

function CompareRadarOverlay({ rows }: { rows: CompareOut["rows"] }) {
  const foundRows = rows.filter((r) => r.found && (r.quality != null || r.value != null || r.growth != null || r.risk != null));
  if (foundRows.length < 2) return null;

  const cx = 130;
  const cy = 130;
  const maxR = 85;

  const getR = (val: number | null | undefined) => {
    if (val === null || val === undefined || isNaN(val)) return 0;
    return (Math.max(0, Math.min(10, val)) / 10) * maxR;
  };

  const colors = [
    "var(--accent)",
    "var(--info)",
    "var(--pos)",
    "var(--warn)",
    "var(--neg)",
    "#a855f7",
    "#06b6d4",
    "#f43f5e",
  ];

  return (
    <Card
      title="Pillar Radar Comparison — Multi-Asset Overlay"
      subtitle="Overlaid Quality · Value · Growth · Risk radar profiles across compared companies"
      padding="md"
    >
      <div className="grid md:grid-cols-[280px_1fr] items-center gap-6">
        <div className="flex justify-center">
          <svg
            viewBox="0 0 260 260"
            width={260}
            height={260}
            role="img"
            aria-label={`Pillar radar comparison overlay for ${foundRows.length} companies`}
            className="overflow-visible select-none"
          >
            {/* Concentric Reference Polygons */}
            {[0.25, 0.5, 0.75, 1.0].map((step) => {
              const r = maxR * step;
              return (
                <polygon
                  key={step}
                  points={`${cx},${cy - r} ${cx + r},${cy} ${cx},${cy + r} ${cx - r},${cy}`}
                  fill="none"
                  stroke="var(--border)"
                  strokeWidth={step === 1.0 ? "1.5" : "1"}
                  strokeDasharray={step === 1.0 ? undefined : "2 2"}
                  opacity={step === 1.0 ? 0.9 : 0.5}
                />
              );
            })}

            {/* Cross Axes */}
            <line x1={cx} y1={cy - maxR} x2={cx} y2={cy + maxR} stroke="var(--border-strong)" strokeWidth={1} />
            <line x1={cx - maxR} y1={cy} x2={cx + maxR} y2={cy} stroke="var(--border-strong)" strokeWidth={1} />

            {/* Axis Labels */}
            <text x={cx} y={cy - maxR - 8} textAnchor="middle" className="font-mono text-[9px] uppercase font-bold fill-ink-1">
              Quality
            </text>
            <text x={cx + maxR + 8} y={cy + 3} textAnchor="start" className="font-mono text-[9px] uppercase font-bold fill-ink-1">
              Value
            </text>
            <text x={cx} y={cy + maxR + 14} textAnchor="middle" className="font-mono text-[9px] uppercase font-bold fill-ink-1">
              Growth
            </text>
            <text x={cx - maxR - 8} y={cy + 3} textAnchor="end" className="font-mono text-[9px] uppercase font-bold fill-ink-1">
              Risk
            </text>

            {/* Polygons for each company */}
            {foundRows.map((r, idx) => {
              const col = colors[idx % colors.length];
              const qR = getR(r.quality);
              const vR = getR(r.value);
              const gR = getR(r.growth);
              const rR = getR(r.risk);
              const points = `${cx},${cy - qR} ${cx + vR},${cy} ${cx},${cy + gR} ${cx - rR},${cy}`;

              return (
                <g key={r.company_id}>
                  <polygon
                    points={points}
                    fill={col}
                    fillOpacity={0.15}
                    stroke={col}
                    strokeWidth={2}
                    strokeLinejoin="round"
                  />
                  <circle cx={cx} cy={cy - qR} r={3} fill={col} stroke="var(--bg-1)" strokeWidth={1} />
                  <circle cx={cx + vR} cy={cy} r={3} fill={col} stroke="var(--bg-1)" strokeWidth={1} />
                  <circle cx={cx} cy={cy + gR} r={3} fill={col} stroke="var(--bg-1)" strokeWidth={1} />
                  <circle cx={cx - rR} cy={cy} r={3} fill={col} stroke="var(--bg-1)" strokeWidth={1} />
                </g>
              );
            })}
          </svg>
        </div>

        {/* Legend / Pillar Score Matrix */}
        <div className="grid sm:grid-cols-2 gap-3">
          {foundRows.map((r, idx) => {
            const col = colors[idx % colors.length];
            return (
              <div
                key={r.company_id}
                className="rounded-card border border-border bg-bg-0 p-3 flex flex-col justify-between space-y-2 hover:border-accent/40 transition-colors"
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: col }} />
                    <span className="font-bold text-xs text-ink-0 truncate">
                      {r.name || r.company_id}
                    </span>
                  </div>
                  <span className="font-mono text-[10px] uppercase text-ink-2 px-1.5 py-0.5 rounded bg-bg-2">
                    {r.currency}
                  </span>
                </div>

                <div className="grid grid-cols-4 gap-1.5 pt-1 text-center font-mono text-[10px]">
                  <div className="rounded bg-bg-2/70 p-1 border border-border/60">
                    <span className="text-ink-2 block text-[9px] uppercase">Q</span>
                    <span className="font-semibold text-ink-0">{r.quality != null ? r.quality.toFixed(1) : "—"}</span>
                  </div>
                  <div className="rounded bg-bg-2/70 p-1 border border-border/60">
                    <span className="text-ink-2 block text-[9px] uppercase">V</span>
                    <span className="font-semibold text-ink-0">{r.value != null ? r.value.toFixed(1) : "—"}</span>
                  </div>
                  <div className="rounded bg-bg-2/70 p-1 border border-border/60">
                    <span className="text-ink-2 block text-[9px] uppercase">G</span>
                    <span className="font-semibold text-ink-0">{r.growth != null ? r.growth.toFixed(1) : "—"}</span>
                  </div>
                  <div className="rounded bg-bg-2/70 p-1 border border-border/60">
                    <span className="text-ink-2 block text-[9px] uppercase">R</span>
                    <span className="font-semibold text-ink-0">{r.risk != null ? r.risk.toFixed(1) : "—"}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </Card>
  );
}

function CompareTrendOverlays({ ids }: { ids: string[] }) {
  const [histories, setHistories] = useState<Record<string, { year: number; revenue: number | null; margin: number | null }[]>>({});
  useEffect(() => {
    let cancelled = false;
    if (ids.length < 2) return;
    Promise.all(ids.map(async (id) => {
      try {
        const d: any = await api.dossier(id);
        const hist = (d.history_annual ?? []).filter((h: any) => h.fiscal_year != null).sort((a: any, b: any) => a.fiscal_year - b.fiscal_year).slice(-10);
        return { id, hist: hist.map((h: any) => ({ year: h.fiscal_year, revenue: h.revenue, margin: h.revenue ? (h.fcf_calc ?? h.net_income) / h.revenue : null })) };
      } catch { return { id, hist: [] }; }
    })).then(arr => {
      if (!cancelled) {
        const map: Record<string, any> = {};
        arr.forEach(({ id, hist }) => map[id] = hist);
        setHistories(map);
      }
    });
    return () => { cancelled = true; };
  }, [ids.join(",")]);

  if (ids.length < 2 || Object.keys(histories).length === 0) return null;
  const W = 520, H = 140, LM = 36, RM = 12, TM = 16, BM = 24;
  const plotW = W - LM - RM, plotH = H - TM - BM;
  const allYears = Array.from(new Set(Object.values(histories).flat().map(h => h.year))).sort((a, b) => a - b);
  if (allYears.length < 2) return null;
  const allRevs = Object.values(histories).flat().map(h => h.revenue).filter((v): v is number => v != null);
  const maxR = Math.max(...allRevs, 1), minR = Math.min(...allRevs, 0);
  const y = (v: number) => TM + (1 - (v - minR) / (maxR - minR || 1)) * plotH;
  const x = (year: number) => {
    const idx = allYears.indexOf(year);
    return LM + (idx / Math.max(1, allYears.length - 1)) * plotW;
  };
  const colors = ["var(--accent)", "var(--info)", "var(--pos)", "var(--warn)", "var(--neg)", "var(--ink-2)"];

  return (
    <Card title="10-Year Trend Overlays — Revenue Growth Synchronized" subtitle="Pure SVG side-by-side trajectories. Hover point for exact figure." padding="sm">
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`10-year revenue trend overlay for ${ids.length} companies`} className="w-full h-auto">
        {[0, 0.5, 1].map(t => <line key={t} x1={LM} x2={W - RM} y1={TM + t * plotH} y2={TM + t * plotH} stroke="var(--border)" strokeWidth={0.6} opacity={0.4} strokeDasharray="2 3" />)}
        {ids.map((id, idx) => {
          const hist = histories[id] ?? [];
          if (hist.length < 2) return null;
          const path = hist.map((h, i) => `${i === 0 ? "M" : "L"} ${x(h.year)} ${y(h.revenue ?? minR)}`).join(" ");
          return <path key={id} d={path} fill="none" stroke={colors[idx % colors.length]} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />;
        })}
        {allYears.map(yv => <text key={yv} x={x(yv)} y={H - BM + 14} textAnchor="middle" fontSize={8} fill="var(--ink-2)" fontFamily="IBM Plex Mono">{yv}</text>)}
        {ids.map((id, idx) => {
          const hist = histories[id] ?? [];
          return hist.map(h => (
            <circle key={`${id}-${h.year}`} cx={x(h.year)} cy={y(h.revenue ?? minR)} r={3} fill={colors[idx % colors.length]} stroke="var(--bg-1)" strokeWidth={1.2}>
              <title>{`${id} FY${h.year}: ${h.revenue != null ? (h.revenue/1e9).toFixed(1)+"B" : "Not reported in filing"}`}</title>
            </circle>
          ));
        })}
      </svg>
      <div className="flex flex-wrap gap-2 mt-1 text-[11px] font-mono">
        {ids.map((id, idx) => (
          <span key={id} className="inline-flex items-center gap-1.5"><span className="w-3 h-0.5 inline-block" style={{ background: colors[idx % colors.length] }} />{id}</span>
        ))}
      </div>
    </Card>
  );
}

function CompareKPIDetail({ ids }: { ids: string[] }) {
  const [details, setDetails] = useState<Record<string, any>>({});
  useEffect(() => {
    let cancelled = false;
    Promise.all(ids.map(async id => {
      try {
        const forensics: any = await api.forensicsSummary(id).catch(() => null);
        const dossier: any = await api.dossier(id).catch(() => null);
        const snap = dossier?.latest_snapshot ?? {};
        return { id, forensics, snap };
      } catch { return { id, forensics: null, snap: {} }; }
    })).then(arr => {
      if (!cancelled) {
        const map: Record<string, any> = {};
        arr.forEach(({ id, forensics, snap }) => map[id] = { forensics, snap });
        setDetails(map);
      }
    });
    return () => { cancelled = true; };
  }, [ids.join(",")]);
  if (ids.length < 2) return null;
  return (
    <Card title="Consolidated KPI Detail — High-Signal View" subtitle="Market Cap · Composite · P/E · EV/EBITDA · ROIC · FCF Yield · Shareholder Yield · Altman Z · Net Debt/EBITDA" padding="sm">
      <div className="overflow-x-auto">
        <table className="w-full text-xs" role="grid" aria-label="Consolidated KPIs">
          <thead>
            <tr className="border-b border-border bg-bg-2/60 text-left font-mono text-[10px] uppercase tracking-wider text-ink-2">
              <th className="px-2 py-2">Metric</th>
              {ids.map(id => <th key={id} className="px-2 py-2 text-right font-mono">{id.split(":")[1]}</th>)}
            </tr>
          </thead>
          <tbody className="divide-y divide-border font-mono text-xs">
            {[
              ["Market Cap", (d: any) => d.snap.market_cap != null ? `$${(d.snap.market_cap/1e9).toFixed(1)}B` : "Not reported in filing"],
              ["ROIC", (d: any) => d.snap.roic != null ? `${(d.snap.roic*100).toFixed(1)}%` : d.snap.roic_calc != null ? `${(d.snap.roic_calc*100).toFixed(1)}%` : "Not applicable: Bank model"],
              ["FCF Yield", (d: any) => d.snap.fcf_calc != null && d.snap.market_cap ? `${((d.snap.fcf_calc/d.snap.market_cap)*100).toFixed(1)}%` : "Not reported in filing"],
              ["Altman Z", (d: any) => d.forensics?.distress?.active_z != null ? d.forensics.distress.active_z.toFixed(2) : d.forensics?.distress?.z_score != null ? d.forensics.distress.z_score.toFixed(2) : "Not applicable: Bank model"],
              ["Net Debt/EBITDA", (d: any) => d.snap.netdebt_calc != null && d.snap.ebitda ? `${(d.snap.netdebt_calc/d.snap.ebitda).toFixed(1)}x` : "Not reported in filing"],
            ].map(([label, fn]) => (
              <tr key={label as string} className="hover:bg-bg-2/30">
                <td className="px-2 py-1.5 text-ink-1">{label as string}</td>
                {ids.map(id => {
                  const d = details[id];
                  const v = d ? (fn as any)(d) : "Not reported in filing";
                  return <td key={id} className="px-2 py-1.5 text-right tabular-nums text-ink-0">{v}</td>;
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

function CompareTable({ data, showHalal, columnGroup = "core" as const }: { data: CompareOut; showHalal: boolean; columnGroup?: "core" | "forensics" | "dividends" | "banks" }) {
  const num = (v: number | null) => (v === null || v === undefined ? null : v);

  const bestOf = (key: keyof (typeof data.rows)[number], dir: "high" | "low"): number | null => {
    const vals = data.rows
      .filter((r) => r.found)
      .map((r) => num(r[key] as number | null))
      .filter((v): v is number => v !== null && (dir === "high" || v > 0));
    if (!vals.length) return null;
    return dir === "high" ? Math.max(...vals) : Math.min(...vals);
  };

  const bestComposite = bestOf("composite", "high");
  const bestRoe = bestOf("roe_calc", "high");
  const bestRoa = bestOf("roa_calc", "high");
  const bestPe = bestOf("pe_calc", "low");
  const bestPb = bestOf("pb_calc", "low");
  const bestEv = bestOf("ev_to_ebitda_calc", "low");
  const bestFcf = bestOf("fcfmargin_calc", "high");

  const coreKeys: [string, keyof (typeof data.rows)[number], "high" | "low", (v: number) => string][] = [
    ["Composite", "composite", "high", (v) => v.toFixed(1)],
    ["PE", "pe_calc", "low", (v) => multiple(v)],
    ["PB", "pb_calc", "low", (v) => multiple(v)],
    ["EV/EBITDA", "ev_to_ebitda_calc", "low", (v) => multiple(v)],
    ["ROE", "roe_calc", "high", (v) => percentish(v)],
    ["ROA", "roa_calc", "high", (v) => percentish(v)],
    ["FCF margin", "fcfmargin_calc", "high", (v) => percentish(v)],
  ];
  const forensicsKeys: [string, keyof (typeof data.rows)[number], "high" | "low", (v: number) => string][] = [
    ["Composite", "composite", "high", (v) => v.toFixed(1)],
    ["ROIC", "roe_calc", "high", (v) => percentish(v)],
    ["Altman Z*", "composite", "high", (v) => v.toFixed(1)],
    ["FCF Yield*", "fcfmargin_calc", "high", (v) => percentish(v)],
  ];
  const dividendKeys: [string, keyof (typeof data.rows)[number], "high" | "low", (v: number) => string][] = [
    ["Composite", "composite", "high", (v) => v.toFixed(1)],
    ["ROE", "roe_calc", "high", (v) => percentish(v)],
    ["FCF margin", "fcfmargin_calc", "high", (v) => percentish(v)],
    ["PE", "pe_calc", "low", (v) => multiple(v)],
  ];
  const bankKeys: [string, keyof (typeof data.rows)[number], "high" | "low", (v: number) => string][] = [
    ["Composite", "composite", "high", (v) => v.toFixed(1)],
    ["PB", "pb_calc", "low", (v) => multiple(v)],
    ["ROE", "roe_calc", "high", (v) => percentish(v)],
    ["ROA", "roa_calc", "high", (v) => percentish(v)],
  ];
  const compKeys = columnGroup === "forensics" ? forensicsKeys : columnGroup === "dividends" ? dividendKeys : columnGroup === "banks" ? bankKeys : coreKeys;

  return (
    <table className="w-full text-xs" role="table" aria-label="Comparison table">
      <thead className="sticky top-0 z-20" style={{ backgroundColor: "var(--bg-0)", borderBottom: "2px solid var(--border-subtle)" }}>
        <tr className="font-mono text-[10px] uppercase tracking-widest text-ink-2">
          <th scope="col" className="sticky left-0 z-20 px-3 py-2.5 text-left min-w-[200px] border-r border-border" style={{ backgroundColor: "var(--bg-0)" }}>Company</th>
          <th scope="col" className="px-3 py-2.5 text-center min-w-[90px] whitespace-nowrap" style={{ backgroundColor: "var(--bg-0)" }} aria-label="Pillar bars">
            <span>Q·V·G·R</span>
            <InfoTip term="Q·V·G·R" />
          </th>
          <th scope="col" className="px-3 py-2.5 text-center min-w-[70px] whitespace-nowrap" style={{ backgroundColor: "var(--bg-0)" }}>
            <span>CCY</span>
            <InfoTip term="Cur" />
          </th>
          {compKeys.map(([label]) => (
            <th key={label} scope="col" className="px-3 py-2.5 text-right font-mono tabular-nums min-w-[90px] whitespace-nowrap" style={{ backgroundColor: "var(--bg-0)" }}>
              <span>{label}</span>
              <InfoTip term={label} />
            </th>
          ))}
          <th scope="col" className="px-3 py-2.5 text-right font-mono tabular-nums min-w-[90px] whitespace-nowrap" style={{ backgroundColor: "var(--bg-0)" }}>
            <span>Peer rank</span>
            <InfoTip term="Peer rank" />
          </th>
          {showHalal && <th scope="col" className="px-3 py-2.5 text-center min-w-[90px]" style={{ backgroundColor: "var(--bg-0)" }}>Halal</th>}
        </tr>
      </thead>
      <tbody className="divide-y divide-border">
        {data.rows.map((r) => (
          <tr key={r.company_id} className={`hover:bg-bg-2/40 transition-colors ${r.found ? "" : "opacity-40"}`}>
            <td className="sticky left-0 z-10 bg-bg-1 px-4 py-3 border-r border-border">
              {r.found ? (
                <CompanyLink companyId={r.company_id} className="font-semibold text-ink-0">
                  {r.name ?? r.company_id}
                </CompanyLink>
              ) : (
                <span className="text-ink-2 font-mono">{r.company_id} (not found)</span>
              )}
            </td>
            <td className="px-3 py-3">
              <div className="flex items-center gap-2">
                <MiniPillarBars quality={r.quality} value={r.value} growth={r.growth} risk={r.risk} />
                <Sparkline data={[r.quality, r.value, r.growth, r.risk]} width={40} height={14} />
              </div>
            </td>
            <td className="px-3 py-2.5 text-center min-w-[70px] font-mono text-xs text-info font-medium">{r.currency ?? "Not reported in filing"}</td>
            {compKeys.map(([label, key, , fmt]) => {
              const v = num(r[key] as number | null);
              const best = { composite: bestComposite, pe_calc: bestPe, pb_calc: bestPb, ev_to_ebitda_calc: bestEv, roe_calc: bestRoe, roa_calc: bestRoa, fcfmargin_calc: bestFcf }[
                key as "composite" | "pe_calc" | "pb_calc" | "ev_to_ebitda_calc" | "roe_calc" | "roa_calc" | "fcfmargin_calc"
              ];
              const isBest = v !== null && best !== null && v === best;
              return (
                <td
                  key={label}
                  className={`px-3 py-2.5 text-right font-mono tabular-nums min-w-[90px] ${isBest ? "rounded-chip bg-accent-weak font-semibold text-accent" : "text-ink-1"}`}
                >
                  {v === null ? "Not reported in filing" : fmt(v)}
                </td>
              );
            })}
            <td className="px-3 py-2.5 text-right font-mono tabular-nums text-ink-1 min-w-[90px]">{r.peer_rank ?? "Not reported in filing"}</td>
            {showHalal && (
              <td className="px-3 py-2.5 text-center min-w-[90px]">
                <span className="inline-flex justify-center w-full"><HalalBadge status={r.halal_status} /></span>
              </td>
            )}
          </tr>
        ))}
        {/* Highlight legend row */}
        <tr className="border-t border-border bg-bg-2/50 font-mono text-[9px] uppercase tracking-widest text-ink-2">
          <td className="sticky left-0 bg-bg-2 px-4 py-2 border-r border-border font-bold text-accent">best</td>
          <td />
          <td />
          {compKeys.map(([label, key, dir]) => {
            const best = dir === "high" ? bestOf(key, "high") : bestOf(key, "low");
            const bestName =
              best === null
                ? "Not reported in filing"
                : (data.rows.find((r) => num(r[key] as number | null) === best)?.name ?? "Not reported in filing");
            return <td key={label} className="px-3 py-2 text-right normal-case tracking-normal text-ink-1 truncate max-w-[100px]">{bestName}</td>;
          })}
          <td />
          {showHalal && <td />}
        </tr>
      </tbody>
    </table>
  );
}

function AddRows({ ids, onChange }: { ids: string[]; onChange: (ids: string[]) => void }) {
  const [query, setQuery] = useState("");
  const debounced = useDebounced(query, 250);
  const [results, setResults] = useState<SearchOut | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [focusedIdx, setFocusedIdx] = useState(0);
  const compare = useCompare();

  useEffect(() => {
    const q = debounced.trim();
    if (!q) {
      setResults(null);
      setErr(null);
      return;
    }
    api.search(q, 6).then(setResults).catch((e: ApiError) => setErr(e.message));
  }, [debounced]);

  useEffect(() => setFocusedIdx(0), [results]);

  const add = (cid: string) => {
    if (ids.includes(cid) || ids.length >= MAX) return;
    // Use sessionCompare for reactive sync across tabs
    compare.add(cid);
    onChange([...ids.filter((x) => x !== cid), cid].slice(0, MAX));
    setQuery("");
    setResults(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!results || results.items.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setFocusedIdx((prev) => Math.min(prev + 1, results.items.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setFocusedIdx((prev) => Math.max(prev - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      const target = results.items[focusedIdx] ?? results.items[0];
      if (target) add(target.company_id);
    } else if (e.key === "Escape") {
      setResults(null);
    }
  };

  return (
    <Card padding="sm" className="relative">
      <div className="flex flex-wrap items-center gap-3">
        <input
          type="search"
          placeholder="Add ticker or company name to compare…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={ids.length >= MAX}
          aria-label="Add company to compare"
          aria-expanded={!!results && results.items.length > 0}
          aria-controls="compare-search-results"
          className="flex-1 min-w-[200px] rounded-card border border-border bg-bg-0 px-3 py-1.5 font-mono text-xs text-ink-0 placeholder:text-ink-2 disabled:opacity-50 focus:border-accent focus:outline-none"
        />
        {ids.length >= MAX && (
          <span className="text-[11px] text-ink-2 font-mono">Maximum {MAX} reached</span>
        )}
      </div>

      {err && <p className="mt-2 text-xs text-neg font-mono">{err}</p>}

      {results && results.items.length > 0 && (
        <ul id="compare-search-results" role="listbox" aria-label="Search results" className="absolute left-0 right-0 top-full mt-1.5 z-20 divide-y divide-border rounded-card border border-border bg-bg-1 shadow-card max-h-56 overflow-auto">
          {results.items.map((it, idx) => {
            const added = ids.includes(it.company_id);
            const isFocused = idx === focusedIdx;
            return (
              <li key={it.company_id} role="option" aria-selected={isFocused}>
                <button
                  type="button"
                  onClick={() => add(it.company_id)}
                  disabled={added || ids.length >= MAX}
                  className={`w-full flex items-center justify-between px-3.5 py-2 text-left text-xs transition-colors disabled:opacity-40 ${isFocused ? "bg-accent-weak text-accent" : "hover:bg-bg-2"}`}
                >
                  <span className="text-ink-0 font-medium truncate">
                    {it.name ?? it.company_id} <span className="text-ink-2 font-mono ml-1.5 text-[10px]">{it.company_id}</span>
                  </span>
                  <span className="shrink-0 ml-2 font-mono text-xs text-accent">
                    {added ? "Added" : "+ Add"}
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </Card>
  );
}