import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { CompareOut, SearchOut } from "../api/types";
import { CompanyLink, ErrorBanner, HalalBadge, Score, SignalBadge, Spinner, useDebounced } from "../components/ui";
import { PillarMiniBars } from "../components/bars";
import { mixedCurrencyWarning, ratio } from "../api/copy";

const MAX = 8;

export default function Compare() {
  const [params, setParams] = useSearchParams();
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

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <h1 className="font-display text-3xl tracking-tight">Compare companies</h1>
        <p className="text-sm text-fog">
          Pick 2 to 8 names. Ratios and scores are comparable across currencies; money amounts stay in each
          company's own currency and are never converted.
        </p>
      </header>

      <AddRows ids={ids} onChange={setIds} />

      {ids.length > 0 && (
        <p className="font-mono text-xs text-dim">
          Selected ({ids.length}/{MAX}): {ids.join(" · ")}
        </p>
      )}
      {ids.length < 2 && <p className="text-sm text-fog">Add at least two companies to compare.</p>}

      {loading && <Spinner label="Comparing…" />}
      {error && <ErrorBanner message={error} />}

      {data && !loading && (
        <>
          {data.currency_warning && (
            <div role="alert" className="rounded-md border border-warn/60 bg-warn/10 px-4 py-3 text-sm text-paper">
              {mixedCurrencyWarning(data.currencies)}
            </div>
          )}
          <div className="overflow-x-auto rounded-md border border-line">
            <CompareTable data={data} />
          </div>
          <p className="text-xs text-dim">
            Highlighted cells mark the best value in each comparable column. “—” means the field is not on file.
          </p>
        </>
      )}
    </div>
  );
}

function CompareTable({ data }: { data: CompareOut }) {
  const num = (v: number | null) => (v === null || v === undefined ? null : v);
  const bestOf = (key: keyof (typeof data.rows)[number]): number | null => {
    const vals = data.rows.filter((r) => r.found).map((r) => num(r[key] as number | null)).filter((v): v is number => v !== null);
    if (!vals.length) return null;
    return Math.max(...vals); // higher composite/pillar = best; ratios are positive-scaled
  };
  const bestRatioOf = (key: keyof (typeof data.rows)[number]): number | null => {
    const vals = data.rows.filter((r) => r.found).map((r) => num(r[key] as number | null)).filter((v): v is number => v !== null && v > 0);
    if (!vals.length) return null;
    return Math.min(...vals); // cheaper multiple = best
  };

  const compKeys: [string, keyof (typeof data.rows)[number], "high" | "low"][] = [
    ["Composite", "composite", "high"],
    ["Quality", "quality", "high"],
    ["Value", "value", "high"],
    ["Growth", "growth", "high"],
    ["Risk", "risk", "high"],
    ["PE", "pe_calc", "low"],
    ["PB", "pb_calc", "low"],
    ["EV/EBITDA", "ev_to_ebitda_calc", "low"],
    ["ROE", "roe_calc", "high"],
    ["ROA", "roa_calc", "high"],
    ["FCF margin", "fcfmargin_calc", "high"],
  ];

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-line bg-panel text-left font-mono text-[10px] uppercase tracking-widest text-dim">
          <th scope="col" className="px-4 py-3">Company</th>
          <th scope="col" className="px-4 py-3" aria-label="Pillar bars">Q·V·G·R</th>
          {data.rows[0]?.money?.currency !== undefined && <th scope="col" className="px-4 py-3">Cur</th>}
          {compKeys.map(([label]) => (
            <th key={label} scope="col" className="px-4 py-3 text-right">{label}</th>
          ))}
          <th scope="col" className="px-4 py-3 text-right">Peer rank</th>
          <th scope="col" className="px-4 py-3">Signal</th>
          <th scope="col" className="px-4 py-3">Halal</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-line">
        {data.rows.map((r) => (
          <tr key={r.company_id} className={r.found ? "" : "opacity-40"}>
            <td className="px-4 py-3">
              {r.found ? <CompanyLink companyId={r.company_id}>{r.name ?? r.company_id}</CompanyLink> : <span className="text-dim">{r.company_id} (not found)</span>}
            </td>
            <td className="px-4 py-3">
              <PillarMiniBars p={{ quality: r.quality, value: r.value, growth: r.growth, risk: r.risk }} />
            </td>
            <td className="px-4 py-3 font-mono text-xs text-info">{r.currency ?? "—"}</td>
            {compKeys.map(([label, key, dir]) => {
              const v = num(r[key] as number | null);
              const best = dir === "high" ? bestOf(key) : bestRatioOf(key);
              const isBest = v !== null && best !== null && v === best;
              return (
                <td key={label} className={`px-4 py-3 text-right font-mono tabular-nums ${isBest ? "rounded bg-gold/15 font-semibold text-gold" : "text-fog"}`}>
                  {v === null ? "—" : key === "pe_calc" || key === "pb_calc" || key === "ev_to_ebitda_calc" ? ratio(v, 1) : v.toFixed(1)}
                </td>
              );
            })}
            <td className="px-4 py-3 text-right font-mono tabular-nums text-fog">{r.peer_rank ?? "—"}</td>
            <td className="px-4 py-3"><SignalBadge signal={r.signal} small /></td>
            <td className="px-4 py-3"><HalalBadge status={r.halal_status} /></td>
          </tr>
        ))}
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
      return;
    }
    api
      .search(q, 8)
      .then(setResults)
      .catch((e: ApiError) => setErr(e.message));
  }, [debounced]);

  const toggle = (cid: string) => {
    if (ids.includes(cid)) onChange(ids.filter((x) => x !== cid));
    else if (ids.length < MAX) onChange([...ids, cid]);
  };

  return (
    <div className="space-y-3">
      <input
        type="search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search to add companies — e.g. Apple"
        aria-label="Search companies to add to the comparison"
        className="w-full rounded-md border border-line bg-panel px-4 py-2.5 placeholder:text-dim"
      />
      {err && <ErrorBanner message={err} onDismiss={() => setErr(null)} />}
      {results && results.items.length > 0 && (
        <ul className="divide-y divide-line rounded-md border border-line bg-panel" aria-label="Addable search results">
          {results.items.map((it) => {
            const selected = ids.includes(it.company_id);
            return (
              <li key={it.company_id} className="flex items-center justify-between gap-4 px-4 py-2.5">
                <label className="flex flex-1 cursor-pointer items-center gap-3 text-sm">
                  <input
                    type="checkbox"
                    checked={selected}
                    onChange={() => toggle(it.company_id)}
                    disabled={!selected && ids.length >= MAX}
                    aria-label={`Add ${it.name ?? it.company_id} to comparison`}
                    className="h-4 w-4 accent-[#e0a84f]"
                  />
                  <span className="text-paper">{it.name ?? it.company_id}</span>
                  <span className="font-mono text-xs text-dim">{it.company_id}</span>
                  {it.currency && <span className="font-mono text-xs text-info">{it.currency}</span>}
                </label>
                <Score value={it.composite} />
              </li>
            );
          })}
        </ul>
      )}
      {ids.length >= MAX && <p className="text-xs text-warn">Maximum of 8 companies per comparison.</p>}
    </div>
  );
}
