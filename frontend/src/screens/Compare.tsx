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

const MAX = 8;

export default function Compare() {
  const [params, setParams] = useSearchParams();
  const showHalal = params.get("halal") === "1";
  const ids = (params.get("ids") ?? "").split(",").filter(Boolean).slice(0, MAX);
  const [data, setData] = useState<CompareOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const setIds = useCallback(
    (next: string[]) => {
      setParams(next.length ? { ids: next.join(",") } : {});
    },
    [setParams],
  );

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
        <div className="space-y-4">
          {warning && (
            <div role="alert" className="rounded-card border border-warn/60 bg-warn-weak px-4 py-3 text-xs text-ink-0">
              {warning}
            </div>
          )}
          <Card padding="none" className="overflow-hidden">
            <div className="overflow-x-auto">
              <CompareTable data={data} showHalal={showHalal} />
            </div>
          </Card>
          <p className="text-xs text-ink-2">
            Best value per column is highlighted with a gold accent band (min PE/PB/EV-EBITDA, max ROE/composite). “—” means the field is
            not on file.
          </p>
        </div>
      )}
    </Page>
  );
}

function CompareTable({ data, showHalal }: { data: CompareOut; showHalal: boolean }) {
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
  const bestPe = bestOf("pe_calc", "low");
  const bestPb = bestOf("pb_calc", "low");
  const bestEv = bestOf("ev_to_ebitda_calc", "low");
  const bestFcf = bestOf("fcfmargin_calc", "high");

  const compKeys: [string, keyof (typeof data.rows)[number], "high" | "low", (v: number) => string][] = [
    ["Composite", "composite", "high", (v) => v.toFixed(1)],
    ["PE", "pe_calc", "low", (v) => multiple(v)],
    ["PB", "pb_calc", "low", (v) => multiple(v)],
    ["EV/EBITDA", "ev_to_ebitda_calc", "low", (v) => multiple(v)],
    ["ROE", "roe_calc", "high", (v) => percentish(v)],
    ["ROA", "roa_calc", "high", (v) => percentish(v)],
    ["FCF margin", "fcfmargin_calc", "high", (v) => percentish(v)],
  ];

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
            <td className="px-3 py-3 font-mono text-xs text-info font-medium">{r.currency ?? "—"}</td>
            {compKeys.map(([label, key, , fmt]) => {
              const v = num(r[key] as number | null);
              const best = { composite: bestComposite, pe_calc: bestPe, pb_calc: bestPb, ev_to_ebitda_calc: bestEv, roe_calc: bestRoe, roa_calc: null, fcfmargin_calc: bestFcf }[
                key as "composite" | "pe_calc" | "pb_calc" | "ev_to_ebitda_calc" | "roe_calc" | "fcfmargin_calc"
              ];
              const isBest = v !== null && best !== null && v === best;
              return (
                <td
                  key={label}
                  className={`px-3 py-3 text-right font-mono tabular-nums ${isBest ? "rounded-chip bg-accent-weak font-semibold text-accent" : "text-ink-1"}`}
                >
                  {v === null ? "—" : fmt(v)}
                </td>
              );
            })}
            <td className="px-3 py-3 text-right font-mono tabular-nums text-ink-1">{r.peer_rank ?? "—"}</td>
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
                ? "—"
                : (data.rows.find((r) => num(r[key] as number | null) === best)?.name ?? "—");
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
