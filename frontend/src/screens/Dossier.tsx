import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, ApiError, enc } from "../api/client";
import type { DossierOut, SimilarOut, SwotOut } from "../api/types";
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
import { getWatchlist, recordOpened, toggleWatch } from "../lib/watchlist";
import { dossierFlags, provenanceSentence } from "../lib/flags";
import { getThesis, saveThesis } from "../lib/thesis";
import { evaluateAlert, getAlertForCompany, saveAlert } from "../lib/alerts";
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
  const [gapActionMsg, setGapActionMsg] = useState<string | null>(null);
  const [fetchingGap, setFetchingGap] = useState(false);

  const load = () => {
    setLoading(true);
    setError(null);
    setNotFound(false);
    api.dossier(companyId)
      .then((d) => {
        setData(d);
        recordOpened(companyId);
      })
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
  const alert = useMemo(() => getAlertForCompany(companyId), [companyId]);
  const alertMsg = useMemo(() => {
    if (!alert || !data) return null;
    const snap = data.latest_snapshot ?? {};
    return evaluateAlert(
      alert,
      data.identity.name || data.identity.cik?.toString() || companyId,
      typeof snap.pe_calc === "number" ? (snap.pe_calc as number) : null,
      data.score?.composite,
    );
  }, [alert, data, companyId]);

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

  const triggerGapFetch = async (target: "shares" | "edgar") => {
    setFetchingGap(true);
    setGapActionMsg(`Initiating ${target === "shares" ? "Yahoo shares & price" : "SEC EDGAR"} pull…`);
    try {
      const res = await api.ingest(companyId, true);
      if (res.job_id) {
        let attempts = 0;
        const interval = setInterval(async () => {
          attempts++;
          try {
            const j = await api.job(res.job_id);
            if (j.message) setGapActionMsg(j.message);
            if (j.status === "succeeded" || j.step === "done" || j.status === "failed" || attempts > 60) {
              clearInterval(interval);
              setFetchingGap(false);
              setGapActionMsg(null);
              load();
            }
          } catch {
            clearInterval(interval);
            setFetchingGap(false);
            setGapActionMsg(null);
            load();
          }
        }, 1000);
      } else {
        setFetchingGap(false);
        setGapActionMsg(null);
        load();
      }
    } catch (e) {
      setGapActionMsg(e instanceof Error ? e.message : String(e));
      setFetchingGap(false);
    }
  };
  const edgarLink = data.identity.cik ? `https://www.sec.gov/edgar/browse/?CIK=${data.identity.cik}` : null;
  const filingType = data.identity.filing_type ?? "10-K";

  return (
    <div className="space-y-6 animate-fade-in print:space-y-3">
      {alertMsg && (
        <div role="alert" className="rounded-md border border-gold/60 bg-gold/10 px-4 py-2.5 text-xs text-gold flex items-center justify-between no-print">
          <span>{alertMsg}</span>
          <span className="font-mono text-[10px] uppercase text-dim">Local Alert</span>
        </div>
      )}

      {/* Breadcrumbs */}
      <nav aria-label="Breadcrumb" className="flex items-center text-xs text-fog no-print">
        <Link to="/" className="hover:text-gold">Desk</Link>
        <span className="mx-1.5">/</span>
        <Link to="/screen" className="hover:text-gold">Screen</Link>
        <span className="mx-1.5">/</span>
        <Link to="/sectors" className="hover:text-gold">Sectors</Link>
        {data.identity.custom_industry_sheet && (
          <>
            <span className="mx-1.5">/</span>
            <Link to={`/sectors/${enc(data.identity.custom_industry_sheet)}`} className="hover:text-gold">
              {data.identity.custom_industry_sheet}
            </Link>
          </>
        )}
        <span className="mx-1.5">/</span>
        <span className="font-mono text-paper">{data.identity.name ?? companyId}</span>
      </nav>

      {/* Status Ribbon (12-col) */}
      <section
        aria-label="Coverage status ribbon"
        className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-line bg-panel2/60 px-4 py-2.5 text-xs text-fog"
      >
        <div className="flex flex-wrap items-center gap-3">
          <span>
            <strong className="font-mono text-dim uppercase tracking-wider">Source:</strong>{" "}
            <span className="font-mono text-paper">{String(snap.source ?? "Seed")}</span>
          </span>
          <span>·</span>
          <span>
            <strong className="font-mono text-dim uppercase tracking-wider">As of:</strong>{" "}
            <span className="font-mono text-paper">{String(snap.as_of_date ?? snap.price_asof ?? "Latest FY")}</span>
          </span>
          <span>·</span>
          <span>
            <strong className="font-mono text-dim uppercase tracking-wider">Currency:</strong>{" "}
            <span className="font-mono text-goldsoft">
              {data.identity.reporting_currency && data.identity.reporting_currency !== cur
                ? `Revenue ${data.identity.reporting_currency} ${typeof snap.revenue === "number" ? (snap.revenue / 1e9).toFixed(2) + "B" : "—"} · trading ${cur}`
                : `Trading & reporting in ${cur}`}
            </span>
          </span>
          <span>·</span>
          <span>
            <strong className="font-mono text-dim uppercase tracking-wider">Coverage:</strong>{" "}
            <span className="font-mono text-paper">{s?.coverage != null ? `${s.coverage}/4 pillars` : "—"}</span>
          </span>
        </div>
        <div>
          <span className="rounded border border-line px-2 py-0.5 font-mono text-[11px] text-paper">
            {s?.peer_set_type === "broad_peer_set"
              ? `broad peer set (n=${s?.peer_n ?? 1})`
              : s?.peer_set_type === "custom_industry_currency"
              ? `${data.identity.custom_industry_sheet || "Custom industry"} (n=${s?.peer_n ?? 1})`
              : `${data.identity.gics_sector || "Sector"} (n=${s?.peer_n ?? 1})`}
          </span>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
        {/* Hero: identity (1-8) */}
        <section aria-label="Identity" className="lg:col-span-8">
          <h1 className="font-display text-4xl tracking-tight">{data.identity.name ?? companyId}</h1>
          <p className="mt-2 text-xs text-fog leading-relaxed max-w-2xl">
            {data.profile?.summary || "No summary."}
          </p>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-sm">
            <span className="font-mono text-dim">{companyId}</span>
            {cur && <span className="rounded border border-info/40 px-2 py-0.5 font-mono text-xs text-info">{cur}</span>}
            {data.identity.gics_sector && <span className="text-fog">{data.identity.gics_sector}</span>}
            {data.identity.custom_industry_sheet && <span className="text-fog">· {data.identity.custom_industry_sheet}</span>}
            {(data.identity.indexes ?? []).map((idx) => (
              <span key={idx} className="rounded border border-line2 px-2 py-0.5 font-mono text-[10px] text-fog">{idx}</span>
            ))}
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-3 text-xs no-print">
            {edgarLink && (
              <a href={edgarLink} target="_blank" rel="noreferrer" className="text-gold hover:underline">
                {filingType} filings on EDGAR ↗
              </a>
            )}
            {data.identity.country === "CA" && (
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
            <button
              onClick={() => window.print()}
              className="rounded border border-line2 px-2 py-0.5 text-fog hover:border-gold hover:text-paper"
              title="Print clean summary"
            >
              Print / Save PDF
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
                <div
                  key={name}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      document.getElementById("why")?.scrollIntoView({ behavior: "smooth" });
                    }
                  }}
                  onClick={() => document.getElementById("why")?.scrollIntoView({ behavior: "smooth" })}
                  className="rounded-md border border-line bg-panel p-3 text-left hover:border-gold/60 transition-colors cursor-pointer"
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
                </div>
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
              <div className="mt-3 flex flex-wrap items-center gap-2">
                {(data.data_gaps.includes("shares") || data.data_gaps.includes("market_cap") || data.data_gaps.includes("price")) && (
                  <button
                    disabled={fetchingGap}
                    onClick={() => triggerGapFetch("shares")}
                    className="inline-flex items-center gap-1.5 rounded border border-gold/60 bg-gold/10 px-2.5 py-1 text-xs font-medium text-gold hover:bg-gold/20 disabled:opacity-50"
                  >
                    Fetch shares from Yahoo
                  </button>
                )}
                {(data.data_gaps.includes("history_short") || data.data_gaps.includes("revenue") || data.data_gaps.includes("net_income")) && (
                  <button
                    disabled={fetchingGap}
                    onClick={() => triggerGapFetch("edgar")}
                    className="inline-flex items-center gap-1.5 rounded border border-line bg-panel2 px-2.5 py-1 text-xs font-medium text-paper hover:bg-panel2/80 disabled:opacity-50"
                  >
                    Retry EDGAR filings
                  </button>
                )}
              </div>
              {gapActionMsg && (
                <p className="mt-2 font-mono text-xs text-gold animate-pulse">{gapActionMsg}</p>
              )}
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
            <Tile label="Revenue" tip="Revenue" value={money(num("revenue"), cur)} yoy={yoyOf(history, "revenue")} />
            <Tile label="Net income" tip="Net income" value={money(num("net_income"), cur)} yoy={yoyOf(history, "net_income")} />
            <Tile label="EPS (diluted)" tip="EPS" value={multiple(num("diluted_eps"), 2)} yoy={yoyOf(history, "diluted_eps")} />
            <Tile label="Free cash flow" tip="FCF margin" value={money(num("fcf_calc"), cur)} yoy={yoyOf(history, "fcf_calc")} />
            <Tile label="ROE" tip="ROE" value={percentish(num("roe_calc"))} />
            <Tile label="ROA" tip="ROA" value={percentish(num("roa_calc"))} />
            <Tile label="FCF margin" tip="FCF margin" value={percentish(num("fcfmargin_calc"))} />
            <Tile label="Gross margin" tip="Gross margin" value={percentish(num("grossmargin_calc"))} />
            <Tile label="PE" tip="PE" value={multiple(num("pe_calc"))} />
            <Tile label="PB" tip="PB" value={multiple(num("pb_calc"))} />
            <Tile label="EV/EBITDA" tip="EV/EBITDA" value={multiple(num("ev_to_ebitda_calc"))} />
            <Tile label="Price" tip="Price" value={money(num("price"), (snap.price_currency as string) ?? cur)} />
            <Tile label="Market cap" tip="Market cap" value={money(num("market_cap"), (snap.price_currency as string) ?? cur)} />
            <Tile label="Total debt" tip="Total debt" value={money(num("total_debt"), cur)} />
            <Tile label="Cash + ST inv." tip="Cash + ST inv." value={money(num("cash_st_investments"), cur)} />
            <Tile label="Net debt" tip="Net debt" value={money(num("netdebt_calc"), cur)} />
            <Tile label="Shares" tip="Shares" value={num("shares_snapshot") != null ? (snap.shares_snapshot as number).toLocaleString() : "—"} />
            <Tile label="Book equity" tip="Book equity" value={money(num("book_equity"), cur)} />
            <Tile
              label="Dividend yield"
              tip={null}
              value={data.profile?.dividend_yield != null ? `${(data.profile.dividend_yield * (data.profile.dividend_yield <= 0.15 ? 100 : 1)).toFixed(2)}%` : "—"}
            />
            <Tile
              label="Dividend / share"
              tip={null}
              value={data.profile?.dividend_rate != null ? `$${data.profile.dividend_rate.toFixed(2)}` : "—"}
            />
            <Tile
              label="Next earnings"
              tip={null}
              value={data.profile?.next_earnings_date || "—"}
            />
          </div>
          <p className="mt-2 text-xs text-dim">
            Money in {cur || "native currency"} — never converted. Source: {String(snap.source ?? "—")}
            {edgarLink ? " · " : ""}
            {edgarLink && <a href={edgarLink} target="_blank" rel="noreferrer" className="text-gold hover:underline">{filingType} on EDGAR ↗</a>}
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

          {data.quarterly && data.quarterly.length > 0 && (
            <div className="mt-4 border-t border-line pt-3">
              <h3 className="font-display text-sm mb-1.5">Quarterly history (last 4 quarters)</h3>
              <div className="overflow-x-auto rounded border border-line">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-line bg-panel text-left font-mono text-[9px] uppercase tracking-widest text-dim">
                      <th scope="col" className="px-2 py-1.5">Quarter</th>
                      <th scope="col" className="px-2 py-1.5 text-right">Revenue</th>
                      <th scope="col" className="px-2 py-1.5 text-right">NI</th>
                      <th scope="col" className="px-2 py-1.5 text-right">EPS</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line font-mono tabular-nums text-fog">
                    {data.quarterly.map((q) => (
                      <tr key={q.date}>
                        <td className="px-2 py-1.5 text-paper">{q.date}</td>
                        <td className="px-2 py-1.5 text-right">{money(q.revenue, cur)}</td>
                        <td className="px-2 py-1.5 text-right">{money(q.net_income, cur)}</td>
                        <td className="px-2 py-1.5 text-right">{q.diluted_eps != null ? `$${q.diluted_eps.toFixed(2)}` : "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
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

        {/* Research Pack: Moat / SWOT, Thesis, Toy DCF, Local Alerts */}
        <section aria-label="Research pack" className="grid grid-cols-1 gap-4 lg:col-span-12 lg:grid-cols-2">
          <SwotCard companyId={companyId} />
          <ThesisNotepad companyId={companyId} />
        </section>

        <section aria-label="Valuation and Alerts" className="grid grid-cols-1 gap-4 lg:col-span-12 lg:grid-cols-2">
          <ToyDcfCard
            isBank={data.identity.custom_industry_sheet === "Banks" || data.identity.gics_sector === "Financials"}
            latestFcf={num("fcf_calc")}
            currency={cur}
          />
          <AlertSettingsCard companyId={companyId} currentPe={num("pe_calc")} currentComposite={s?.composite} />
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
  const tipTerm = tip === undefined ? label : tip;
  return (
    <div className="rounded-md border border-line bg-panel px-3 py-2">
      <div className="flex items-center justify-between font-mono text-[9px] uppercase tracking-widest text-dim">
        <span className="truncate">{label}</span>
        {tipTerm && <InfoTip term={tipTerm} />}
      </div>
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

function SwotCard({ companyId }: { companyId: string }) {
  const [swot, setSwot] = useState<SwotOut | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const draft = () => {
    setLoading(true);
    setError(null);
    api
      .swotResearch(companyId)
      .then(setSwot)
      .catch((e: ApiError) => setError(e.message))
      .finally(() => setLoading(false));
  };

  return (
    <div className="rounded-md border border-line bg-panel p-4 space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line pb-2">
        <div>
          <h3 className="font-display text-base">Moat &amp; SWOT Draft</h3>
          <p className="text-[11px] text-dim">LLM draft from our facts. Not a 10-K.</p>
        </div>
        {!swot && !loading && (
          <button
            onClick={draft}
            className="rounded border border-gold/60 bg-gold/10 px-3 py-1 font-mono text-xs text-gold hover:bg-gold/20 transition-colors"
          >
            Draft SWOT from numbers (not AI score)
          </button>
        )}
      </div>

      {loading && <Spinner label="Drafting SWOT from numbers JSON (free model)..." />}
      {error && <ErrorBanner message={error} onRetry={draft} />}

      {swot && (
        <div className="space-y-3 text-xs leading-relaxed">
          <div className="flex items-center justify-between text-[10px] text-dim">
            <span className="font-mono">{swot.model} {swot.cached && "(cached)"}</span>
            <span className="text-gold font-medium">{swot.label}</span>
          </div>
          <div className="whitespace-pre-line rounded bg-ink/70 p-3 font-mono text-xs text-paper border border-line/50">
            {swot.swot}
          </div>
          <p className="text-[10px] text-dim">{swot.disclaimer}</p>
        </div>
      )}
    </div>
  );
}

function ThesisNotepad({ companyId }: { companyId: string }) {
  const [thesis, setThesis] = useState(() => getThesis(companyId));
  const [draft, setDraft] = useState(thesis.text);
  const [savedAt, setSavedAt] = useState<string | null>(thesis.savedAt);

  useEffect(() => {
    const t = getThesis(companyId);
    setThesis(t);
    setDraft(t.text);
    setSavedAt(t.savedAt);
  }, [companyId]);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value.slice(0, 1000);
    setDraft(val);
    const updated = saveThesis(companyId, val);
    setSavedAt(updated.savedAt);
  };

  return (
    <div className="rounded-md border border-line bg-panel p-4 space-y-2">
      <div className="flex items-center justify-between border-b border-line pb-2">
        <h3 className="font-display text-base">5-Line Thesis</h3>
        <span className="font-mono text-[10px] text-dim">
          {savedAt ? `Saved ${new Date(savedAt).toLocaleTimeString()}` : "Not saved"} · {draft.length}/1000
        </span>
      </div>
      <p className="text-[11px] text-dim">Your notes stay on this browser.</p>
      <textarea
        value={draft}
        onChange={handleChange}
        maxLength={1000}
        rows={4}
        placeholder="Write your 5-line thesis: 1) What they do, 2) Growth catalyst, 3) Valuation vs peers, 4) Major risk, 5) Target entry price..."
        className="w-full rounded border border-line bg-ink p-2.5 font-mono text-xs text-paper placeholder:text-dim focus:border-gold focus:outline-none"
      />
    </div>
  );
}

function computeToyDcf(fcfStr: string, gStr: string, waccStr: string, yearsStr: string) {
  const fcf = parseFloat(fcfStr);
  const g = parseFloat(gStr) / 100;
  const wacc = parseFloat(waccStr) / 100;
  const years = parseInt(yearsStr, 10);

  if (isNaN(fcf) || isNaN(g) || isNaN(wacc) || isNaN(years) || years <= 0 || wacc <= 0.02) {
    return null;
  }

  let pvSum = 0;
  let currentFcf = fcf;
  for (let i = 1; i <= years; i++) {
    currentFcf *= (1 + g);
    pvSum += currentFcf / Math.pow(1 + wacc, i);
  }
  const terminalVal = (currentFcf * 1.02) / (wacc - 0.02);
  const pvTerminal = terminalVal / Math.pow(1 + wacc, years);
  const enterpriseValue = pvSum + pvTerminal;

  return { pvSum, pvTerminal, enterpriseValue };
}

function ToyDcfCard({ isBank, latestFcf, currency }: { isBank: boolean; latestFcf?: number | null; currency: string }) {
  const [fcf, setFcf] = useState("");
  const [growth, setGrowth] = useState("");
  const [wacc, setWacc] = useState("");
  const [years, setYears] = useState("5");

  const result = useMemo(() => computeToyDcf(fcf, growth, wacc, years), [fcf, growth, wacc, years]);

  return (
    <div className="rounded-md border border-line bg-panel p-4 space-y-3">
      <div className="border-b border-line pb-2">
        <h3 className="font-display text-base">Toy DCF Calculator</h3>
        <p className="text-[11px] text-dim">
          Output is not stored as truth. Default empty. Exploratory scratchpad only.
        </p>
      </div>

      {isBank ? (
        <p className="text-xs text-fog italic">
          Banks and insurers do not report standard operating cash flow or FCF. DCF calculator disabled for financial institutions.
        </p>
      ) : (
        <div className="space-y-3 text-xs">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <div>
              <label className="block font-mono text-[10px] uppercase text-dim mb-1">Base FCF ({currency})</label>
              <input
                type="number"
                placeholder={latestFcf ? `Latest: ${(latestFcf / 1e6).toFixed(0)}M` : "e.g. 1000000000"}
                value={fcf}
                onChange={(e) => setFcf(e.target.value)}
                className="w-full rounded border border-line bg-ink px-2 py-1 font-mono text-xs text-paper"
              />
            </div>
            <div>
              <label className="block font-mono text-[10px] uppercase text-dim mb-1">Growth (g %)</label>
              <input
                type="number"
                placeholder="e.g. 6"
                value={growth}
                onChange={(e) => setGrowth(e.target.value)}
                className="w-full rounded border border-line bg-ink px-2 py-1 font-mono text-xs text-paper"
              />
            </div>
            <div>
              <label className="block font-mono text-[10px] uppercase text-dim mb-1">Discount (WACC %)</label>
              <input
                type="number"
                placeholder="e.g. 9"
                value={wacc}
                onChange={(e) => setWacc(e.target.value)}
                className="w-full rounded border border-line bg-ink px-2 py-1 font-mono text-xs text-paper"
              />
            </div>
            <div>
              <label className="block font-mono text-[10px] uppercase text-dim mb-1">Years</label>
              <input
                type="number"
                min="1"
                max="20"
                value={years}
                onChange={(e) => setYears(e.target.value)}
                className="w-full rounded border border-line bg-ink px-2 py-1 font-mono text-xs text-paper"
              />
            </div>
          </div>

          {result && (
            <div className="rounded bg-ink/70 p-3 font-mono text-xs border border-line/50 space-y-1">
              <div className="flex justify-between text-fog">
                <span>PV of Projection Period:</span>
                <span className="text-paper">{money(result.pvSum, currency)}</span>
              </div>
              <div className="flex justify-between text-fog">
                <span>PV of Terminal Value (2% perp):</span>
                <span className="text-paper">{money(result.pvTerminal, currency)}</span>
              </div>
              <div className="flex justify-between font-semibold text-gold pt-1 border-t border-line/40">
                <span>Implied Value:</span>
                <span>{money(result.enterpriseValue, currency)}</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function AlertSettingsCard({ companyId, currentPe, currentComposite }: { companyId: string; currentPe?: number | null; currentComposite?: number | null }) {
  const [alert, setAlertState] = useState(() => getAlertForCompany(companyId));
  const [peAbove, setPeAbove] = useState(alert?.pe_above?.toString() ?? "");
  const [compBelow, setCompBelow] = useState(alert?.composite_below?.toString() ?? "");
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    const updated = saveAlert({
      id: companyId,
      pe_above: peAbove ? parseFloat(peAbove) : null,
      composite_below: compBelow ? parseFloat(compBelow) : null,
    });
    setAlertState(updated.find((a) => a.id === companyId) ?? null);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <form onSubmit={handleSave} className="rounded-md border border-line bg-panel p-4 space-y-3">
      <div className="border-b border-line pb-2">
        <h3 className="font-display text-base">Local Alert Rule</h3>
        <p className="text-[11px] text-dim">
          Evaluated locally on page load. No push notifications.
        </p>
      </div>
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div>
          <label className="block font-mono text-[10px] uppercase text-dim mb-1">Alert if PE &gt;</label>
          <input
            type="number"
            step="1"
            placeholder={currentPe ? `Current: ${currentPe.toFixed(1)}` : "e.g. 25"}
            value={peAbove}
            onChange={(e) => setPeAbove(e.target.value)}
            className="w-full rounded border border-line bg-ink px-2.5 py-1 font-mono text-xs text-paper"
          />
        </div>
        <div>
          <label className="block font-mono text-[10px] uppercase text-dim mb-1">Alert if Composite &lt;</label>
          <input
            type="number"
            step="0.5"
            placeholder={currentComposite ? `Current: ${currentComposite.toFixed(1)}` : "e.g. 5.0"}
            value={compBelow}
            onChange={(e) => setCompBelow(e.target.value)}
            className="w-full rounded border border-line bg-ink px-2.5 py-1 font-mono text-xs text-paper"
          />
        </div>
      </div>
      <div className="flex items-center justify-between pt-1">
        <button
          type="submit"
          className="rounded border border-gold/60 bg-gold/15 px-3 py-1 font-mono text-xs text-gold hover:bg-gold/25 transition-colors"
        >
          {saved ? "Saved!" : "Save Alert"}
        </button>
        {alert && (
          <span className="font-mono text-[10px] text-dim">
            Active: {alert.pe_above ? `PE > ${alert.pe_above}` : ""} {alert.composite_below ? `Comp < ${alert.composite_below}` : ""}
          </span>
        )}
      </div>
    </form>
  );
}

function NotFound({ companyId }: { companyId: string }) {
  const [ingesting, setIngesting] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const parts = companyId.split(":");
  const ticker = parts.length >= 2 ? parts[1] : companyId;

  const handleFetch = () => {
    setIngesting(true);
    setMsg(null);
    api
      .ingest(ticker)
      .then((res) => {
        setMsg(`Ingest job queued (${res.job_id}). Reloading in 5s...`);
        setTimeout(() => window.location.reload(), 5000);
      })
      .catch((e: ApiError) => {
        setMsg(`Fetch failed: ${e.message}`);
        setIngesting(false);
      });
  };

  return (
    <div className="space-y-4">
      <h1 className="font-display text-3xl tracking-tight">Company not found</h1>
      <p className="text-sm text-fog">
        No company with ID <span className="font-mono text-paper">{companyId}</span> in the database.
      </p>

      <div className="rounded-md border border-line bg-panel p-4 max-w-md space-y-3">
        <p className="text-xs text-paper font-medium">Would you like to fetch this ticker into the universe?</p>
        <button
          onClick={handleFetch}
          disabled={ingesting}
          className="rounded border border-gold/60 bg-gold/15 px-3 py-1.5 font-mono text-xs text-gold hover:bg-gold/25 transition-colors disabled:opacity-50"
        >
          {ingesting ? "Queueing fetch..." : `Fetch ${ticker} from SEC / Yahoo`}
        </button>
        {msg && <p className="font-mono text-[11px] text-fog">{msg}</p>}
      </div>

      <div className="flex gap-4 text-sm">
        <Link to="/screen" className="text-gold hover:underline">Go to screener →</Link>
        <Link to="/sectors" className="text-gold hover:underline">Browse sectors →</Link>
        <Link to="/" className="text-gold hover:underline">Back to the desk →</Link>
      </div>
    </div>
  );
}

