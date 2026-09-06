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

      {ids.length < 2 && (
        <p className="rounded-card border border-border bg-bg-1 p-4 text-xs text-ink-1">
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
          <CompareTrendOverlays ids={ids} />
          <CompareKPIDetail ids={ids} />
        </div>
      )}
    </Page>
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
    <table className="w-full text-xs">
      <thead>
        <tr className="border-b border-border bg-bg-2/70 text-left font-mono text-[10px] uppercase tracking-widest text-ink-2">
          <th scope="col" className="sticky left-0 z-10 bg-bg-2 px-4 py-3 border-r border-border">Company</th>
          <th scope="col" className="px-3 py-3 whitespace-nowrap" aria-label="Pillar bars">
            <span>Q·V·G·R</span>
            <InfoTip term="Q·V·G·R" />
          </th>
          <th scope="col" className="px-3 py-3 whitespace-nowrap">
            <span>Cur</span>
            <InfoTip term="Cur" />
          </th>
          {compKeys.map(([label]) => (
            <th key={label} scope="col" className="px-3 py-3 text-right whitespace-nowrap">
              <span>{label}</span>
              <InfoTip term={label} />
            </th>
          ))}
          <th scope="col" className="px-3 py-3 text-right whitespace-nowrap">
            <span>Peer rank</span>
            <InfoTip term="Peer rank" />
          </th>
          {showHalal && <th scope="col" className="px-3 py-3">Halal</th>}
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
            <td className="px-3 py-3 font-mono text-xs text-info font-medium">{r.currency ?? "Not reported in filing"}</td>
            {compKeys.map(([label, key, , fmt]) => {
              const v = num(r[key] as number | null);
              const best = { composite: bestComposite, pe_calc: bestPe, pb_calc: bestPb, ev_to_ebitda_calc: bestEv, roe_calc: bestRoe, roa_calc: bestRoa, fcfmargin_calc: bestFcf }[
                key as "composite" | "pe_calc" | "pb_calc" | "ev_to_ebitda_calc" | "roe_calc" | "roa_calc" | "fcfmargin_calc"
              ];
              const isBest = v !== null && best !== null && v === best;
              return (
                <td
                  key={label}
                  className={`px-3 py-3 text-right font-mono tabular-nums ${isBest ? "rounded-chip bg-accent-weak font-semibold text-accent" : "text-ink-1"}`}
                >
                  {v === null ? "Not reported in filing" : fmt(v)}
                </td>
              );
            })}
            <td className="px-3 py-3 text-right font-mono tabular-nums text-ink-1">{r.peer_rank ?? "Not reported in filing"}</td>
            {showHalal && (
              <td className="px-3 py-3">
                <HalalBadge status={r.halal_status} />
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

  useEffect(() => {
    const q = debounced.trim();
    if (!q) {
      setResults(null);
      setErr(null);
      return;
    }
    api.search(q, 6).then(setResults).catch((e: ApiError) => setErr(e.message));
  }, [debounced]);

  const add = (cid: string) => {
    if (ids.includes(cid) || ids.length >= MAX) return;
    onChange([...ids, cid]);
    setQuery("");
    setResults(null);
  };

  return (
    <Card padding="sm" className="relative">
      <div className="flex flex-wrap items-center gap-3">
        <input
          type="search"
          placeholder="Add ticker or company name to compare…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={ids.length >= MAX}
          className="flex-1 min-w-[200px] rounded-card border border-border bg-bg-0 px-3 py-1.5 font-mono text-xs text-ink-0 placeholder:text-ink-2 disabled:opacity-50"
        />
        {ids.length >= MAX && (
          <span className="text-[11px] text-ink-2 font-mono">Maximum {MAX} reached</span>
        )}
      </div>

      {err && <p className="mt-2 text-xs text-neg font-mono">{err}</p>}

      {results && results.items.length > 0 && (
        <ul className="absolute left-0 right-0 top-full mt-1.5 z-20 divide-y divide-border rounded-card border border-border bg-bg-1 shadow-card max-h-56 overflow-auto">
          {results.items.map((it) => {
            const added = ids.includes(it.company_id);
            return (
              <li key={it.company_id}>
                <button
                  type="button"
                  onClick={() => add(it.company_id)}
                  disabled={added || ids.length >= MAX}
                  className="w-full flex items-center justify-between px-3.5 py-2 text-left text-xs hover:bg-bg-2 disabled:opacity-40 transition-colors"
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