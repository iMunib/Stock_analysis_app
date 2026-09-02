import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, ApiError, enc } from "../api/client";
import type { DossierOut, SimilarOut } from "../api/types";
import {
  bankPathCopy,
  coveragePenaltyCopy,
  gapLabel,
  growthCopy,
  halalCopy,
  signalCopy,
  whyBullets,
} from "../api/copy";
import { money, multiple, percentish, score1, yoyPct } from "../lib/format";
import { CompanyLink, ErrorBanner, HalalBadge, SignalBadge, Spinner } from "../components/ui";
import { ScoreBar } from "../components/bars";
import { columnHeights } from "../lib/bars";
import { getCompareSelection, toggleCompareSelection } from "../lib/sessionCompare";
import { getWatchlist, toggleWatch } from "../lib/watchlist";
import { dossierFlags, provenanceSentence } from "../lib/flags";
import InfoTip from "../components/InfoTip";
import NarrationPanel from "../components/NarrationPanel";

export default function Dossier() {
  const { companyId = "" } = useParams();
  const [data, setData] = useState<DossierOut | null>(null);
  const [similar, setSimilar] = useState<SimilarOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [loading, setLoading] = useState(true);
  const [compareSet, setCompareSet] = useState<string[]>(getCompareSelection());
  const [watched, setWatched] = useState(getWatchlist().includes(companyId));

  const load = () => {
    setLoading(true);
    setError(null);
    setNotFound(false);
    api.dossier(companyId)
      .then(setData)
      .catch((e: ApiError) => {
        if (e.status === 404) setNotFound(true);
        else setError(e.message);
      })
      .finally(() => setLoading(false));
    api.similar(companyId, 5).then(setSimilar).catch(() => setSimilar(null));
  };

  useEffect(load, [companyId]);
  useEffect(() => setWatched(getWatchlist().includes(companyId)), [companyId]);

  const bullets = useMemo(() => (data ? whyBulletsSafe(data) : []), [data]);

  if (loading) return <Spinner label={`Loading dossier for ${companyId}…`} />;
  if (notFound) return <NotFound companyId={companyId} />;
  if (error) return <ErrorBanner message={error} onRetry={load} />;
  if (!data) return null;

  const s = data.score;
  const snap = (data.latest_snapshot ?? {}) as Record<string, unknown>;
  const cur = data.identity.currency ?? "";
  const isFinancial =
    (data.identity.gics_sector ?? "").toLowerCase() === "financials" ||
    ["banks", "insurance", "credit_services"].includes((data.identity.custom_industry_sheet ?? "").toLowerCase());
  const bankNote = bankPathCopy(isFinancial);
  const penaltyNote = coveragePenaltyCopy(s?.coverage ?? null, s?.penalty ?? null);
  const pillars = s?.pillars ?? { quality: null, value: null, growth: null, risk: null };

  const history = data.history_annual;
  const sanitized = history.filter((h) => !h.quality_flag);
  const hasTrend = sanitized.length >= 3;
  const revHeights = columnHeights(sanitized.map((h) => h.revenue ?? null), 96);
  const prevOf = (fy: number) => history.find((h) => h.fiscal_year === fy - 1);
  const num = (k: string): number | null => (typeof snap[k] === "number" ? (snap[k] as number) : null);

  const tenK =
    data.identity.country === "US"
      ? `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company=${encodeURIComponent(data.identity.name ?? "")}&type=10-K&owner=exclude&count=10`
      : null;

  return (
    <div className="mx-auto max-w-[1280px] space-y-5 animate-fade-in">
      <nav className="col-span-12 text-xs text-dim" aria-label="Breadcrumb">
        <Link to="/" className="hover:text-gold">Desk</Link>
        <span className="mx-1.5">/</span>
        <Link to="/sectors" className="hover:text-gold">Sectors</Link>
        {data.identity.custom_industry_sheet && (
          <>
            <span className="mx-1.5">/</span>
            <Link to={`/sectors/${enc(data.identity.custom_industry_sheet)}?currency=${cur}`} className="hover:text-gold">
              {data.identity.custom_industry_sheet}
            </Link>
          </>
        )}
        <span className="mx-1.5">/</span>
        <span className="font-mono text-paper">{data.identity.name ?? companyId}</span>
      </nav>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
        {/* Hero: identity (1-8) */}
        <section aria-label="Identity" className="lg:col-span-8">
          <h1 className="font-display text-4xl tracking-tight">{data.identity.name ?? companyId}</h1>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-sm">
            <span className="font-mono text-dim">{companyId}</span>
            {cur && <span className="rounded border border-info/40 px-2 py-0.5 font-mono text-xs text-info">{cur}</span>}
            {data.identity.gics_sector && <span className="text-fog">{data.identity.gics_sector}</span>}
            {data.identity.custom_industry_sheet && <span className="text-fog">· {data.identity.custom_industry_sheet}</span>}
            {(data.identity.indexes ?? []).map((idx) => (
              <span key={idx} className="rounded border border-line2 px-2 py-0.5 font-mono text-[10px] text-fog">{idx}</span>
            ))}
          </div>
          <div className="mt-3 flex flex-wrap gap-3 text-xs">
            {tenK && (
              <a href={tenK} target="_blank" rel="noreferrer" className="text-gold hover:underline">
                10-K filings on EDGAR ↗
              </a>
            )}
            {!tenK && data.identity.country === "CA" && (
              <a href="https://www.sedarplus.ca/csa-party/records/document.html" target="_blank" rel="noreferrer" className="text-gold hover:underline">
                Canadian filings: SEDAR+ ↗
              </a>
            )}
            <button
              onClick={() => setWatched(toggleWatch(companyId).includes(companyId))}
              className={`rounded border px-2 py-0.5 ${watched ? "border-gold text-gold" : "border-line2 text-fog hover:border-gold"}`}
              aria-pressed={watched}
            >
              {watched ? "★ Watching" : "☆ Watch"}
            </button>
          </div>
        </section>

        {/* Verdict card (9-12) */}
        <section aria-label="Verdict" className="rounded-md border border-line bg-panel p-4 lg:col-span-4">
          <div className="flex items-center gap-3">
            <SignalBadge signal={s?.signal ?? "insufficient_data"} />
            {s?.peer_rank != null && s?.peer_n != null && (
              <span className="font-mono text-sm text-paper">
                #{s.peer_rank} of {s.peer_n} <span className="text-fog">({cur})</span>
              </span>
            )}
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-display text-4xl text-gold">{s ? score1(s.composite) : "—"}</span>
            {s && <span className="font-mono text-xs text-dim">{s.coverage}/4 pillars</span>}
          </div>
          <p className="mt-2 text-sm text-fog">{s === null ? "Not scored yet." : signalCopy(s.signal)}</p>
          <p className="mt-1 font-mono text-[10px] uppercase tracking-wider text-dim">{provenanceSentence(data)}</p>
          <div className="mt-2 flex flex-wrap gap-1.5" aria-label="Flags">
            {dossierFlags(data).map((f) => (
              <span
                key={f.key}
                className={`rounded border px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider ${
                  f.tone === "good" ? "border-good/50 text-good" : f.tone === "bad" ? "border-bad/50 text-bad" : f.tone === "mid" ? "border-mid/50 text-mid" : "border-info/50 text-info"
                }`}
              >
                {f.label}
              </span>
            ))}
          </div>
        </section>

        {/* Pillars: one row of 4 (cols 1-12) */}
        <section aria-label="Score pillars" id="pillars" className="lg:col-span-12">
          <h2 className="font-display text-lg">How it scores</h2>
          <div className="mt-2 grid grid-cols-2 gap-3 lg:grid-cols-4">
            {(["quality", "value", "growth", "risk"] as const).map((name) => {
              const v = s ? pillars[name] : null;
              return (
                <button
                  key={name}
                  onClick={() => document.getElementById("why")?.scrollIntoView({ behavior: "smooth" })}
                  className="rounded-md border border-line bg-panel p-3 text-left hover:border-gold/60 transition-colors"
                >
                  <div className="flex items-baseline justify-between">
                    <span className="font-mono text-[10px] uppercase tracking-widest text-dim">
                      {name}
                      <InfoTip term={name.charAt(0).toUpperCase() + name.slice(1)} />
                    </span>
                    <span className="font-mono text-sm tabular-nums text-paper">{score1(v)}</span>
                  </div>
                  <div className="mt-1.5"><ScoreBar value={v} label={name} /></div>
                  <p className="mt-1.5 text-[11px] text-fog">
                    {v == null
                      ? name === "growth"
                        ? growthCopy(null)
                        : "Not scored — missing inputs."
                      : pillarNote(name)}
                  </p>
                </button>
              );
            })}
          </div>
        </section>

        {/* Mid: Why + flags (1-7) | Similar (8-12) */}
        <section aria-label="Why this score" id="why" className="rounded-md border border-line bg-panel p-4 lg:col-span-7">
          <h2 className="font-display text-lg">Why this score</h2>
          {bullets.length === 0 ? (
            <p className="mt-2 text-sm text-fog">Not enough fields on file.</p>
          ) : (
            <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-paper">
              {bullets.map((b, i) => <li key={i}>{b}</li>)}
            </ul>
          )}
          {data.data_gaps.length > 0 && (
            <>
              <p className="mt-3 font-mono text-[10px] uppercase tracking-widest text-dim">What is missing</p>
              <ul className="mt-1 list-inside list-disc space-y-0.5 text-xs text-fog">
                {data.data_gaps.map((g) => <li key={g}>{gapLabel(g)}</li>)}
              </ul>
            </>
          )}
          {penaltyNote && <p className="mt-2 text-xs text-fog">{penaltyNote}</p>}
          {bankNote && <p className="mt-1 text-xs text-fog">{bankNote}</p>}
        </section>

        <section aria-label="Similar names" className="rounded-md border border-line bg-panel p-4 lg:col-span-5">
          <h2 className="font-display text-lg">Similar names</h2>
          {!similar || similar.items.length === 0 ? (
            <p className="mt-2 text-sm text-fog">No scored peers yet.</p>
          ) : (
            <table className="mt-2 w-full text-sm">
              <tbody className="divide-y divide-line">
                {similar.items.map((it) => (
                  <tr key={it.company_id}>
                    <td className="py-1.5 pr-2">
                      <CompanyLink companyId={it.company_id}>{it.name ?? it.company_id}</CompanyLink>
                    </td>
                    <td className="py-1.5 text-right font-mono tabular-nums">{score1(it.composite)}</td>
                    <td className="py-1.5 pl-2"><SignalBadge signal={it.signal} small /></td>
                    <td className="py-1.5 pl-2 text-right">
                      <Link to={`/compare?ids=${[companyId, it.company_id].map(enc).join(",")}`} className="text-xs text-gold hover:underline">
                        vs
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        {/* Snapshot tiles: 4 columns */}
        <section aria-label="Latest snapshot" className="lg:col-span-12">
          <h2 className="font-display text-lg">Latest snapshot</h2>
          <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
            <Tile label="Revenue" tip={null} value={money(num("revenue"), cur)} yoy={yoyOf(history, "revenue")} />
            <Tile label="Net income" tip={null} value={money(num("net_income"), cur)} yoy={yoyOf(history, "net_income")} />
            <Tile label="EPS (diluted)" tip="PE" value={multiple(num("diluted_eps"), 2)} yoy={yoyOf(history, "diluted_eps")} />
            <Tile label="Free cash flow" tip="FCF margin" value={money(num("fcf_calc"), cur)} yoy={yoyOf(history, "fcf_calc")} />
            <Tile label="ROE" value={percentish(num("roe_calc"))} />
            <Tile label="ROA" value={percentish(num("roa_calc"))} />
            <Tile label="FCF margin" value={percentish(num("fcfmargin_calc"))} />
            <Tile label="Gross margin" value={percentish(num("grossmargin_calc"))} />
            <Tile label="PE" tip="PE" value={multiple(num("pe_calc"))} />
            <Tile label="PB" tip="PB" value={multiple(num("pb_calc"))} />
            <Tile label="EV/EBITDA" tip="EV/EBITDA" value={multiple(num("ev_to_ebitda_calc"))} />
            <Tile label="Price" value={money(num("price"), (snap.price_currency as string) ?? cur)} />
            <Tile label="Market cap" value={money(num("market_cap"), (snap.price_currency as string) ?? cur)} />
            <Tile label="Total debt" value={money(num("total_debt"), cur)} />
            <Tile label="Cash + ST inv." value={money(num("cash_st_investments"), cur)} />
            <Tile label="Net debt" value={money(num("netdebt_calc"), cur)} />
            <Tile label="Shares" value={num("shares_snapshot") != null ? (snap.shares_snapshot as number).toLocaleString() : "—"} />
            <Tile label="Book equity" value={money(num("book_equity"), cur)} />
          </div>
          <p className="mt-2 text-xs text-dim">
            Money in {cur || "native currency"} — never converted. Source: {String(snap.source ?? "—")}
            {snap.as_of_date ? ` · as of ${String(snap.as_of_date)}` : ""}
            {tenK ? " · " : ""}
            {tenK && <a href={tenK} target="_blank" rel="noreferrer" className="text-gold hover:underline">10-K on EDGAR ↗</a>}
          </p>
        </section>

        {/* History: table (1-7) + bars (8-12) */}
        <section aria-label="Annual history" className="lg:col-span-7">
          <h2 className="font-display text-lg">Annual history</h2>
          {history.length === 0 ? (
            <p className="mt-2 text-sm text-fog">No annual history on file.</p>
          ) : (
            <div className="mt-2 overflow-x-auto rounded-md border border-line">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-line bg-panel text-left font-mono text-[9px] uppercase tracking-widest text-dim">
                    <th scope="col" className="px-2 py-1.5">FY</th>
                    <th scope="col" className="px-2 py-1.5 text-right">Revenue</th>
                    <th scope="col" className="px-2 py-1.5 text-right">YoY</th>
                    <th scope="col" className="px-2 py-1.5 text-right">NI</th>
                    <th scope="col" className="px-2 py-1.5 text-right">EPS</th>
                    <th scope="col" className="px-2 py-1.5">Flag</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {history.map((h) => {
                    const yoy = yoyPct(h.revenue ?? null, prevOf(h.fiscal_year)?.revenue ?? null);
                    const suspect = Boolean(h.quality_flag);
                    return (
                      <tr key={h.fiscal_year} className={suspect ? "italic text-dim" : ""}>
                        <td className="px-2 py-1.5 font-mono text-paper">{h.fiscal_year}</td>
                        <td className="px-2 py-1.5 text-right font-mono tabular-nums text-fog">{money(h.revenue ?? null, null)}</td>
                        <td className={`px-2 py-1.5 text-right font-mono tabular-nums ${yoy == null ? "text-dim" : yoy >= 0 ? "text-good" : "text-bad"}`}>
                          {yoy == null ? "—" : `${yoy > 0 ? "+" : ""}${yoy.toFixed(1)}%`}
                        </td>
                        <td className="px-2 py-1.5 text-right font-mono tabular-nums text-fog">{money(h.net_income ?? null, null)}</td>
                        <td className="px-2 py-1.5 text-right font-mono tabular-nums text-fog">{h.diluted_eps ?? "—"}</td>
                        <td className="px-2 py-1.5">
                          {suspect ? (
                            <span className="rounded border border-mid/50 px-1 py-0.5 font-mono text-[8px] uppercase text-mid" title={h.warning ?? undefined}>
                              excluded from growth
                            </span>
                          ) : h.used_for_growth ? (
                            <span className="font-mono text-[8px] text-dim">growth</span>
                          ) : null}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section aria-label="History bars" className="lg:col-span-5">
          <h2 className="font-display text-lg">Revenue trend</h2>
          {!hasTrend ? (
            <p className="mt-2 rounded-md border border-line bg-panel p-3 text-sm text-fog">
              {growthCopy(s?.pillars.growth ?? null)} A trend line would be guesswork, so we show the raw rows instead.
            </p>
          ) : (
            <div className="mt-2">
              <svg viewBox={`0 0 ${sanitized.length * 40} 100`} className="h-24 w-full" role="img" aria-label="Revenue by fiscal year (sanitized)">
                {sanitized.map((h, i) => {
                  const hh = revHeights[i] ?? 0;
                  return <rect key={h.fiscal_year} x={i * 40 + 8} y={100 - hh} width={26} height={Math.max(hh, 0)} rx="2" fill="#e0a84f" />;
                })}
              </svg>
              <div className="mt-1 flex justify-between font-mono text-[9px] text-dim">
                <span>{sanitized[0]?.fiscal_year}</span>
                <span>{sanitized[sanitized.length - 1]?.fiscal_year}</span>
              </div>
              <p className="mt-1 text-[10px] text-dim">Sanitized years only — suspect filings excluded.</p>
            </div>
          )}
        </section>

        {/* Narration */}
        <section className="lg:col-span-12">
          <NarrationPanel endpoint={`/api/v1/companies/${enc(companyId)}/narrate`} label="Plain-English explanation" />
        </section>

        {/* Halal + actions */}
        <section aria-label="Halal flag" className="lg:col-span-7">
          {data.halal && (
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <HalalBadge status={data.halal.status ?? "unknown"} />
              <span className="text-xs text-fog">{halalCopy(data.halal.status)}</span>
            </div>
          )}
        </section>
        <section aria-label="Actions" className="flex flex-wrap items-center justify-end gap-4 lg:col-span-5">
          <label className="flex cursor-pointer items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={compareSet.includes(companyId)}
              onChange={() => setCompareSet(toggleCompareSelection(companyId))}
              className="h-4 w-4 accent-[#e0a84f]"
            />
            Add to compare
          </label>
          {similar && similar.items.length > 0 && (
            <Link
              to={`/compare?ids=${[companyId, ...similar.items.slice(0, 3).map((i) => i.company_id)].map(enc).join(",")}`}
              className="text-sm text-gold hover:underline"
            >
              Compare with similar →
            </Link>
          )}
          {compareSet.length >= 2 && (
            <Link to={`/compare?ids=${compareSet.map(enc).join(",")}`} className="text-sm text-gold hover:underline">
              Go to compare ({compareSet.length}) →
            </Link>
          )}
        </section>
      </div>
    </div>
  );
}

function yoyOf(history: DossierOut["history_annual"], key: string): number | null {
  const dated = [...history].sort((a, b) => b.fiscal_year - a.fiscal_year);
  const cur = dated[0]?.[key as keyof (typeof dated)[number]] as number | null | undefined;
  const prev = dated[1]?.[key as keyof (typeof dated)[number]] as number | null | undefined;
  return yoyPct(cur ?? null, prev ?? null);
}

function Tile({ label, value, yoy, tip }: { label: string; value: string; yoy?: number | null; tip?: string | null }) {
  return (
    <div className="rounded-md border border-line bg-panel px-3 py-2">
      <p className="font-mono text-[9px] uppercase tracking-widest text-dim">
        {label}
        {tip && <InfoTip term={tip} />}
      </p>
      <div className="mt-0.5 flex items-baseline justify-between gap-2">
        <span className="font-mono text-sm tabular-nums text-paper">{value}</span>
        {yoy != null && (
          <span className={`font-mono text-[10px] ${yoy >= 0 ? "text-good" : "text-bad"}`}>
            {yoy > 0 ? "+" : ""}{yoy.toFixed(1)}%
          </span>
        )}
      </div>
    </div>
  );
}

function pillarNote(name: string): string {
  switch (name) {
    case "quality":
      return "Profitability and accounting quality versus sector peers.";
    case "value":
      return "How cheap this name is versus peers in the same currency.";
    case "growth":
      return "Annual growth over the years on file.";
    default:
      return "Balance-sheet and earnings-stability risks (higher is safer).";
  }
}

function whyBulletsSafe(d: DossierOut): string[] {
  // delegates to the deterministic builder (kept out of this file for testability)
  return whyBullets(d);
}

function NotFound({ companyId }: { companyId: string }) {
  return (
    <div className="space-y-4">
      <h1 className="font-display text-3xl tracking-tight">Company not found</h1>
      <p className="text-sm text-fog">
        No company with ID <span className="font-mono">{companyId}</span> in the database.
      </p>
      <div className="flex gap-4 text-sm">
        <Link to="/sectors" className="text-gold hover:underline">Browse sectors →</Link>
        <Link to="/" className="text-gold hover:underline">Back to the desk →</Link>
      </div>
    </div>
  );
}
