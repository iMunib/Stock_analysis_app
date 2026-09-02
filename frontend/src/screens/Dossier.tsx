import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
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
import { ForensicCard } from "../components/ForensicCard";
import { ReverseDCFCard } from "../components/ReverseDCFCard";
import { Card, Chip, Page, StatTile } from "../components/layout";
import { CompositeGauge, PillarRadar } from "../components/viz";

export default function Dossier() {
  const { companyId = "" } = useParams();
  const [data, setData] = useState<DossierOut | null>(null);
  const [similar, setSimilar] = useState<SimilarOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const [compareSet, setCompareSet] = useState<string[]>(getCompareSelection());
  const [watched, setWatched] = useState(getWatchlist().includes(companyId));
  const [gapActionMsg, setGapActionMsg] = useState<string | null>(null);
  const [fetchingGap, setFetchingGap] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const handleRemoveCompany = async () => {
    setDeleting(true);
    try {
      await api.deleteCompany(companyId);
      if (getWatchlist().includes(companyId)) {
        toggleWatch(companyId);
      }
      const currentCompare = getCompareSelection();
      if (currentCompare.includes(companyId)) {
        toggleCompareSelection(companyId);
      }
      navigate("/", { replace: true });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to remove stock";
      setError(msg);
      setDeleting(false);
      setConfirmDelete(false);
    }
  };

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
  const snap = data.latest_snapshot ?? {};
  const cur = data.identity.currency;
  const num = (k: string): number | null => (typeof snap[k] === "number" ? (snap[k] as number) : null);

  const pillars = {
    quality: s?.pillars.quality ?? null,
    value: s?.pillars.value ?? null,
    growth: s?.pillars.growth ?? null,
    risk: s?.pillars.risk ?? null,
  };

  const penaltyNote = coveragePenaltyCopy(s?.coverage ?? null, s?.penalty ?? null);
  const bankNote = bankPathCopy(data.identity.custom_industry_sheet === "Banks" || data.identity.gics_sector === "Financials");

  const history = [...data.history_annual].sort((a, b) => b.fiscal_year - a.fiscal_year);
  const prevOf = (yr: number) => history.find((h) => h.fiscal_year === yr - 1);
  const sanitized = history.filter((h) => !h.quality_flag).reverse();
  const hasTrend = sanitized.length >= 3;
  const revHeights = columnHeights(sanitized.map((h) => h.revenue ?? null), 80);

  const triggerGapFetch = async (target: "shares" | "edgar") => {
    setFetchingGap(true);
    setGapActionMsg(`Queueing fetch for ${target}…`);
    try {
      const parts = companyId.split(":");
      const t = parts.length >= 2 ? parts[1] : companyId;
      const res = await api.ingest(t);
      if (res.job_id) {
        setGapActionMsg(`Job queued (${res.job_id}). Polling…`);
        const interval = setInterval(async () => {
          try {
            const j = await api.job(res.job_id!);
            if (j.status === "succeeded" || j.step === "done") {
              clearInterval(interval);
              setFetchingGap(false);
              setGapActionMsg("Done! Reloading numbers…");
              load();
            } else if (j.status === "failed") {
              clearInterval(interval);
              setFetchingGap(false);
              setGapActionMsg(`Failed: ${j.message}`);
            }
          } catch {
            clearInterval(interval);
            setFetchingGap(false);
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
  // EDGAR link: precise CIK link when the refresh worker has resolved one; otherwise a
  // ticker/name search that always works (cik is NULL until the first refresh_universe run).
  const edgarFallback = `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company=${encodeURIComponent(data.identity.ticker || data.identity.name || "")}&type=10-K&owner=exclude&count=10`;
  const edgarLink = data.identity.cik
    ? `https://www.sec.gov/edgar/browse/?CIK=${data.identity.cik}`
    : data.identity.country === "US"
      ? edgarFallback
      : null;
  const filingType = data.identity.filing_type ?? "10-K";

  const breadcrumb = (
    <div className="flex items-center text-xs text-ink-2 no-print">
      <Link to="/" className="hover:text-accent">Desk</Link>
      <span className="mx-1.5">/</span>
      <Link to="/screen" className="hover:text-accent">Screen</Link>
      <span className="mx-1.5">/</span>
      <Link to="/sectors" className="hover:text-accent">Sectors</Link>
      {data.identity.custom_industry_sheet && (
        <>
          <span className="mx-1.5">/</span>
          <Link to={`/sectors/${enc(data.identity.custom_industry_sheet)}`} className="hover:text-accent">
            {data.identity.custom_industry_sheet}
          </Link>
        </>
      )}
      <span className="mx-1.5">/</span>
      <span className="font-mono text-ink-0">{data.identity.name ?? companyId}</span>
    </div>
  );

  return (
    <Page breadcrumb={breadcrumb} className="print:space-y-3">
      {alertMsg && (
        <div role="alert" className="rounded-card border border-accent/60 bg-accent-weak px-4 py-2.5 text-xs text-accent flex items-center justify-between no-print">
          <span>{alertMsg}</span>
          <span className="font-mono text-[10px] uppercase text-ink-2">Local Alert</span>
        </div>
      )}

      {/* Status Ribbon (12-col) */}
      <section
        aria-label="Coverage status ribbon"
        className="flex flex-wrap items-center justify-between gap-3 rounded-card border border-border bg-bg-1 px-4 py-2.5 text-xs text-ink-1 shadow-card"
      >
        <div className="flex flex-wrap items-center gap-3">
          <span>
            <strong className="font-mono text-ink-2 uppercase tracking-wider">Source:</strong>{" "}
            <span className="font-mono text-ink-0">{String(snap.source ?? "Seed")}</span>
          </span>
          <span>·</span>
          <span>
            <strong className="font-mono text-ink-2 uppercase tracking-wider">As of:</strong>{" "}
            <span className="font-mono text-ink-0">{String(snap.as_of_date ?? snap.price_asof ?? "Latest FY")}</span>
          </span>
          <span>·</span>
          <span>
            <strong className="font-mono text-ink-2 uppercase tracking-wider">Currency:</strong>{" "}
            <span className="font-mono text-accent">
              {data.identity.reporting_currency && data.identity.reporting_currency !== cur
                ? `Revenue ${data.identity.reporting_currency} ${typeof snap.revenue === "number" ? (snap.revenue / 1e9).toFixed(2) + "B" : "—"} · trading ${cur}`
                : `Trading & reporting in ${cur}`}
            </span>
          </span>
          <span>·</span>
          <span>
            <strong className="font-mono text-ink-2 uppercase tracking-wider">Coverage:</strong>{" "}
            <span className="font-mono text-ink-0">{s?.coverage != null ? `${s.coverage}/4 pillars` : "—"}</span>
          </span>
        </div>
        <div>
          <span className="rounded-chip border border-border px-2 py-0.5 font-mono text-[11px] text-ink-0 bg-bg-2/50">
            {s?.peer_set_type === "broad_peer_set"
              ? `broad peer set (n=${s?.peer_n ?? 1})`
              : s?.peer_set_type === "custom_industry_currency"
              ? `${data.identity.custom_industry_sheet || "Custom industry"} (n=${s?.peer_n ?? 1})`
              : `${data.identity.gics_sector || "Sector"} (n=${s?.peer_n ?? 1})`}
          </span>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
        {/* Hero: Identity (lg:col-span-8) */}
        <Card className="lg:col-span-8" padding="lg">
          <h1 className="font-display text-3xl sm:text-4xl tracking-tight text-ink-0">{data.identity.name ?? companyId}</h1>
          <p className="mt-2 text-xs text-ink-1 leading-relaxed max-w-2xl">
            {data.profile?.summary || "No summary."}
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
            <span className="font-mono text-ink-2 text-xs">{companyId}</span>
            {cur && <Chip tone="info" size="sm">{cur}</Chip>}
            {data.identity.gics_sector && <span className="text-xs text-ink-1">{data.identity.gics_sector}</span>}
            {data.identity.custom_industry_sheet && <span className="text-xs text-ink-1">· {data.identity.custom_industry_sheet}</span>}
            {(data.identity.indexes ?? []).map((idx) => (
              <span key={idx} className="rounded-chip border border-border px-2 py-0.5 font-mono text-[10px] text-ink-2">{idx}</span>
            ))}
          </div>
          <div className="mt-4 flex flex-wrap items-center gap-3 text-xs no-print">
            {edgarLink && (
              <a href={edgarLink} target="_blank" rel="noreferrer" className="text-accent hover:underline font-mono">
                {filingType} filings on EDGAR ↗
              </a>
            )}
            {data.identity.country === "CA" && (
              <a href="https://www.sedarplus.ca/csa-party/records/document.html" target="_blank" rel="noreferrer" className="text-accent hover:underline font-mono">
                Canadian filings: SEDAR+ ↗
              </a>
            )}
            <button
              onClick={() => setWatched(toggleWatch(companyId).includes(companyId))}
              className={`rounded-card border px-2.5 py-1 font-mono text-xs transition-colors ${watched ? "border-accent text-accent bg-accent-weak" : "border-border text-ink-1 hover:border-accent"}`}
              aria-pressed={watched}
            >
              {watched ? "★ Watching" : "☆ Watch"}
            </button>
            <button
              onClick={() => window.print()}
              className="rounded-card border border-border px-2.5 py-1 text-xs font-mono text-ink-1 hover:border-accent hover:text-ink-0 transition-colors"
              title="Print clean summary"
            >
              Print / Save PDF
            </button>
            {confirmDelete ? (
              <span className="flex items-center gap-1.5 bg-neg-weak border border-neg/40 rounded-card px-2.5 py-1 text-neg text-xs font-mono">
                <span>Remove from desk?</span>
                <button
                  onClick={handleRemoveCompany}
                  disabled={deleting}
                  className="font-bold text-neg hover:underline px-1"
                >
                  {deleting ? "Removing..." : "Yes, remove"}
                </button>
                <button
                  onClick={() => setConfirmDelete(false)}
                  disabled={deleting}
                  className="text-ink-2 hover:underline px-1"
                >
                  Cancel
                </button>
              </span>
            ) : (
              <button
                onClick={() => setConfirmDelete(true)}
                className="rounded-card border border-border px-2.5 py-1 text-xs font-mono text-ink-1 hover:border-neg hover:text-neg transition-colors"
                title="Remove stock from desk and screener"
              >
                ✕ Remove from Desk
              </button>
            )}
          </div>
        </Card>

        {/* Verdict Card (lg:col-span-4) */}
        <Card
          className="lg:col-span-4"
          tone={s?.signal === "strong_candidate" || s?.signal === "constructive" ? "positive" : s?.signal === "weak" || s?.signal === "avoid" ? "negative" : "warning"}
          padding="lg"
        >
          <div className="flex items-center justify-between gap-3">
            <SignalBadge signal={s?.signal ?? "insufficient_data"} />
            {s?.peer_rank != null && s?.peer_n != null && (
              <span className="font-mono text-xs text-ink-1">
                #{s.peer_rank} of {s.peer_n} ({cur})
              </span>
            )}
          </div>
          <div className="my-3 flex justify-center">
            <CompositeGauge value={s?.composite} signal={s?.signal} size="md" />
          </div>
          <p className="mt-1 text-xs text-ink-1 leading-relaxed">{s === null ? "Not scored yet." : signalCopy(s.signal)}</p>
          <p className="mt-2 font-mono text-[10px] uppercase tracking-wider text-ink-2 border-t border-border pt-2">{provenanceSentence(data)}</p>
          <div className="mt-2 flex flex-wrap gap-1.5" aria-label="Flags">
            {dossierFlags(data).map((f) => (
              <Chip
                key={f.key}
                size="sm"
                tone={f.tone === "good" ? "positive" : f.tone === "bad" ? "negative" : f.tone === "mid" ? "warning" : "info"}
              >
                {f.label}
              </Chip>
            ))}
          </div>
        </Card>

        {/* Score Pillars: Radar Chart + 4 StatTiles */}
        <section aria-label="Score pillars" id="pillars" className="lg:col-span-12">
          <Card
            title="How it scores"
            subtitle="Deterministic mathematical decomposition across 4 core pillars"
            action={<span className="font-mono text-xs text-accent">Math v1 (Q30/V25/G25/R20)</span>}
          >
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
              <div className="lg:col-span-5 flex justify-center py-2">
                <PillarRadar
                  quality={s ? pillars.quality : null}
                  value={s ? pillars.value : null}
                  growth={s ? pillars.growth : null}
                  risk={s ? pillars.risk : null}
                  size={240}
                />
              </div>
              <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-2 gap-3">
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
                      className="rounded-card border border-border bg-bg-2/50 p-3.5 text-left hover:border-accent/60 hover:bg-bg-2 transition-all cursor-pointer"
                    >
                      <div className="flex items-baseline justify-between">
                        <span className="font-mono text-[10px] uppercase tracking-widest text-ink-2 flex items-center gap-1">
                          {name}
                          <InfoTip term={name.charAt(0).toUpperCase() + name.slice(1)} />
                        </span>
                        <span className="font-mono text-base tabular-nums font-semibold text-ink-0">{score1(v)}</span>
                      </div>
                      <div className="mt-2"><ScoreBar value={v} label={name} /></div>
                      <p className="mt-2 text-[11px] text-ink-1 leading-relaxed">
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
            </div>
          </Card>
        </section>

        {/* Mid: Why + Flags (lg:col-span-7) | Similar (lg:col-span-5) */}
        <Card title="Why this score" className="lg:col-span-7" padding="md">
          {bullets.length === 0 ? (
            <p className="text-sm text-ink-1">Not enough fields on file.</p>
          ) : (
            <ul className="list-inside list-disc space-y-1.5 text-xs text-ink-0 leading-relaxed">
              {bullets.map((b, i) => <li key={i}>{b}</li>)}
            </ul>
          )}
          {data.data_gaps.length > 0 && (
            <div className="mt-4 border-t border-border pt-3">
              <p className="font-mono text-[10px] uppercase tracking-widest text-ink-2 font-semibold">What is missing</p>
              <ul className="mt-1.5 list-inside list-disc space-y-0.5 text-xs text-ink-1">
                {data.data_gaps.map((g) => <li key={g}>{gapLabel(g)}</li>)}
              </ul>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                {(data.data_gaps.includes("shares") || data.data_gaps.includes("market_cap") || data.data_gaps.includes("price")) && (
                  <button
                    disabled={fetchingGap}
                    onClick={() => triggerGapFetch("shares")}
                    className="inline-flex items-center gap-1.5 rounded-card border border-accent/60 bg-accent-weak px-2.5 py-1 text-xs font-mono text-accent hover:bg-accent/20 disabled:opacity-50 transition-colors"
                  >
                    Fetch shares from Yahoo
                  </button>
                )}
                {(data.data_gaps.includes("history_short") || data.data_gaps.includes("revenue") || data.data_gaps.includes("net_income")) && (
                  <button
                    disabled={fetchingGap}
                    onClick={() => triggerGapFetch("edgar")}
                    className="inline-flex items-center gap-1.5 rounded-card border border-border bg-bg-2 px-2.5 py-1 text-xs font-mono text-ink-0 hover:bg-bg-3 disabled:opacity-50 transition-colors"
                  >
                    Retry EDGAR filings
                  </button>
                )}
              </div>
              {gapActionMsg && (
                <p className="mt-2 font-mono text-xs text-accent animate-pulse">{gapActionMsg}</p>
              )}
            </div>
          )}
          {penaltyNote && <p className="mt-3 text-xs text-ink-2 italic">{penaltyNote}</p>}
          {bankNote && <p className="mt-1 text-xs text-ink-2 italic">{bankNote}</p>}
        </Card>

        <Card title="Similar names" className="lg:col-span-5" padding="md">
          {!similar || similar.items.length === 0 ? (
            <p className="text-xs text-ink-2">No scored peers yet.</p>
          ) : (
            <table className="w-full text-xs">
              <tbody className="divide-y divide-border">
                {similar.items.map((it) => (
                  <tr key={it.company_id} className="hover:bg-bg-2/50 transition-colors">
                    <td className="py-2 pr-2">
                      <CompanyLink companyId={it.company_id}>{it.name ?? it.company_id}</CompanyLink>
                    </td>
                    <td className="py-2 text-right font-mono tabular-nums font-semibold">{score1(it.composite)}</td>
                    <td className="py-2 pl-2"><SignalBadge signal={it.signal} small /></td>
                    <td className="py-2 pl-2 text-right">
                      <Link to={`/compare?ids=${[companyId, it.company_id].map(enc).join(",")}`} className="text-xs font-mono text-accent hover:underline">
                        vs
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>

        {/* Snapshot Section */}
        <section aria-label="Latest snapshot" className="lg:col-span-12">
          <Card
            title="Latest snapshot"
            subtitle={`Money in ${cur || "native currency"} — never converted. Source: ${String(snap.source ?? "—")}`}
            action={
              edgarLink ? (
                <a href={edgarLink} target="_blank" rel="noreferrer" className="text-accent hover:underline font-mono text-xs">
                  {filingType} on EDGAR ↗
                </a>
              ) : null
            }
          >
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
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
          </Card>
        </section>

        {/* History: Annual & Quarterly */}
        <section aria-label="Annual history" className="lg:col-span-7">
          <Card title="Annual history" subtitle="Audited fiscal year filings" infoTip={data.history_warnings?.length ? data.history_warnings.join(" · ") : undefined}>
            {data.history_warnings && data.history_warnings.length > 0 && (
              <div role="alert" className="mb-3 rounded-card border border-warn/40 bg-warn-weak px-3 py-2 text-xs text-ink-1">
                <span className="font-semibold">Data trust warning:</span> {data.history_warnings.length} filing
                year{data.history_warnings.length > 1 ? "s" : ""} look mis-scaled or mis-tagged and
                {data.history_warnings.length > 1 ? " were" : " was"} excluded from growth math. See chips below.
              </div>
            )}
            {history.length === 0 ? (
              <p className="text-xs text-ink-2">No annual history on file.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-border text-left font-mono text-[9px] uppercase tracking-widest text-ink-2">
                      <th scope="col" className="px-2 py-1.5">FY</th>
                      <th scope="col" className="px-2 py-1.5 text-right">Revenue</th>
                      <th scope="col" className="px-2 py-1.5 text-right">YoY</th>
                      <th scope="col" className="px-2 py-1.5 text-right">NI</th>
                      <th scope="col" className="px-2 py-1.5 text-right">EPS</th>
                      <th scope="col" className="px-2 py-1.5">Flag</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {history.map((h) => {
                      const yoy = yoyPct(h.revenue ?? null, prevOf(h.fiscal_year)?.revenue ?? null);
                      const suspect = Boolean(h.quality_flag);
                      return (
                        <tr key={h.fiscal_year} className={suspect ? "italic text-ink-2" : "hover:bg-bg-2/40 transition-colors"}>
                          <td className="px-2 py-1.5 font-mono text-ink-0 font-medium">{h.fiscal_year}</td>
                          <td className="px-2 py-1.5 text-right font-mono tabular-nums text-ink-1">{money(h.revenue ?? null, null)}</td>
                          <td className={`px-2 py-1.5 text-right font-mono tabular-nums ${yoy == null ? "text-ink-2" : yoy >= 0 ? "text-pos" : "text-neg"}`}>
                            {yoy == null ? "—" : `${yoy > 0 ? "+" : ""}${yoy.toFixed(1)}%`}
                          </td>
                          <td className="px-2 py-1.5 text-right font-mono tabular-nums text-ink-1">{money(h.net_income ?? null, null)}</td>
                          <td className="px-2 py-1.5 text-right font-mono tabular-nums text-ink-1">{h.diluted_eps ?? "—"}</td>
                          <td className="px-2 py-1.5">
                            {suspect ? (
                              <Chip tone="warning" size="sm" title={h.warning ?? undefined}>
                                excluded from growth
                              </Chip>
                            ) : h.used_for_growth ? (
                              <span className="font-mono text-[8px] text-ink-2 uppercase">growth</span>
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
              <div className="mt-5 border-t border-border pt-4">
                <h3 className="font-heading text-xs font-semibold text-ink-0 mb-2">Quarterly history (last 4 quarters)</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-border text-left font-mono text-[9px] uppercase tracking-widest text-ink-2">
                        <th scope="col" className="px-2 py-1.5">Quarter</th>
                        <th scope="col" className="px-2 py-1.5 text-right">Revenue</th>
                        <th scope="col" className="px-2 py-1.5 text-right">NI</th>
                        <th scope="col" className="px-2 py-1.5 text-right">EPS</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border font-mono tabular-nums text-ink-1">
                      {data.quarterly.map((q) => (
                        <tr key={q.date} className="hover:bg-bg-2/40 transition-colors">
                          <td className="px-2 py-1.5 text-ink-0 font-medium">{q.date}</td>
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
          </Card>
        </section>

        {/* Revenue Trend Bars */}
        <section aria-label="History bars" className="lg:col-span-5">
          <Card title="Revenue trend" subtitle="Sanitized years only — suspect filings excluded">
            {!hasTrend ? (
              <p className="rounded-card border border-border bg-bg-2/50 p-3 text-xs text-ink-1 leading-relaxed">
                {growthCopy(s?.pillars.growth ?? null)} A trend line would be guesswork, so we show the raw rows instead.
              </p>
            ) : (
              <div>
                <svg viewBox={`0 0 ${sanitized.length * 40} 100`} className="h-28 w-full" role="img" aria-label="Revenue by fiscal year (sanitized)">
                  {sanitized.map((h, i) => {
                    const hh = revHeights[i] ?? 0;
                    return (
                      <rect
                        key={h.fiscal_year}
                        x={i * 40 + 8}
                        y={100 - hh}
                        width={24}
                        height={Math.max(hh, 0)}
                        rx="3"
                        fill="var(--accent)"
                        className="transition-all duration-300 hover:opacity-80"
                      />
                    );
                  })}
                </svg>
                <div className="mt-2 flex justify-between font-mono text-[9px] text-ink-2">
                  <span>{sanitized[0]?.fiscal_year}</span>
                  <span>{sanitized[sanitized.length - 1]?.fiscal_year}</span>
                </div>
              </div>
            )}
          </Card>
        </section>

        {/* Plain-English Narration */}
        <section className="lg:col-span-12">
          <NarrationPanel endpoint={`/api/v1/companies/${enc(companyId)}/narrate`} label="Plain-English explanation" />
        </section>

        {/* Research Pack: Moat / SWOT, Thesis */}
        <section aria-label="Research pack" className="grid grid-cols-1 gap-4 lg:col-span-12 lg:grid-cols-2">
          <SwotCard companyId={companyId} />
          <ThesisNotepad companyId={companyId} />
        </section>

        {/* Institutional Forensic Suite and Reverse DCF */}
        <section aria-label="Forensic and Valuation Suite" className="grid grid-cols-1 gap-4 lg:col-span-12">
          <ForensicCard companyId={companyId} />
          <ReverseDCFCard companyId={companyId} />
        </section>

        {/* Toy DCF and Alerts */}
        <section aria-label="Valuation and Alerts" className="grid grid-cols-1 gap-4 lg:col-span-12 lg:grid-cols-2">
          <ToyDcfCard
            isBank={data.identity.custom_industry_sheet === "Banks" || data.identity.gics_sector === "Financials"}
            latestFcf={num("fcf_calc")}
            currency={cur ?? "USD"}
          />
          <AlertSettingsCard companyId={companyId} currentPe={num("pe_calc")} currentComposite={s?.composite} />
        </section>

        {/* Halal + Actions */}
        <section aria-label="Halal flag" className="lg:col-span-7 flex items-center">
          {data.halal && (
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <HalalBadge status={data.halal.status ?? "unknown"} />
              <span className="text-ink-1">{halalCopy(data.halal.status)}</span>
            </div>
          )}
        </section>
        <section aria-label="Actions" className="flex flex-wrap items-center justify-end gap-4 lg:col-span-5 text-xs font-mono">
          <label className="flex cursor-pointer items-center gap-2 text-ink-1 hover:text-ink-0 transition-colors">
            <input
              type="checkbox"
              checked={compareSet.includes(companyId)}
              onChange={() => setCompareSet(toggleCompareSelection(companyId))}
              className="h-4 w-4 rounded border-border bg-bg-0 accent-accent"
            />
            <span>Add to compare</span>
          </label>
          {similar && similar.items.length > 0 && (
            <Link
              to={`/compare?ids=${[companyId, ...similar.items.slice(0, 3).map((i) => i.company_id)].map(enc).join(",")}`}
              className="text-accent hover:underline"
            >
              Compare with similar →
            </Link>
          )}
          {compareSet.length >= 2 && (
            <Link to={`/compare?ids=${compareSet.map(enc).join(",")}`} className="text-accent hover:underline font-semibold">
              Go to compare ({compareSet.length}) →
            </Link>
          )}
        </section>
      </div>
    </Page>
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
    <StatTile
      label={label}
      value={value}
      delta={yoy}
      infoTip={tipTerm ? <InfoTip term={tipTerm} /> : null}
    />
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
    <Card
      title="Moat & SWOT Draft"
      subtitle="LLM draft from our facts JSON. Not a 10-K."
      action={
        !swot && !loading ? (
          <button
            onClick={draft}
            className="rounded-card border border-accent/60 bg-accent-weak px-3 py-1 font-mono text-xs text-accent hover:bg-accent/20 transition-colors"
          >
            Draft SWOT from numbers (not AI score)
          </button>
        ) : null
      }
    >
      {loading && <Spinner label="Drafting SWOT from numbers JSON (free model)..." />}
      {error && <ErrorBanner message={error} onRetry={draft} />}

      {swot && (
        <div className="space-y-3 text-xs leading-relaxed">
          <div className="flex items-center justify-between text-[10px] text-ink-2 font-mono">
            <span>{swot.model} {swot.cached && "(cached)"}</span>
            <span className="text-accent font-medium">{swot.label}</span>
          </div>
          <div className="whitespace-pre-line rounded-card bg-bg-2/50 p-3.5 font-mono text-xs text-ink-0 border border-border">
            {swot.swot}
          </div>
          <p className="text-[10px] text-ink-2">{swot.disclaimer}</p>
        </div>
      )}
    </Card>
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
    <Card
      title="5-Line Thesis"
      subtitle="Your notes stay on this browser."
      action={
        <span className="font-mono text-[10px] text-ink-2">
          {savedAt ? `Saved ${new Date(savedAt).toLocaleTimeString()}` : "Not saved"} · {draft.length}/1000
        </span>
      }
    >
      <textarea
        value={draft}
        onChange={handleChange}
        maxLength={1000}
        rows={4}
        placeholder="Write your 5-line thesis: 1) What they do, 2) Growth catalyst, 3) Valuation vs peers, 4) Major risk, 5) Target entry price..."
        className="w-full rounded-card border border-border bg-bg-0 p-3 font-mono text-xs text-ink-0 placeholder:text-ink-2 focus:border-accent focus:outline-none"
      />
    </Card>
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
    <Card
      title="Toy DCF Calculator"
      subtitle="Output is not stored as truth. Default empty. Exploratory scratchpad only."
    >
      {isBank ? (
        <p className="text-xs text-ink-2 italic py-2">
          Banks and insurers do not report standard operating cash flow or FCF. DCF calculator disabled for financial institutions.
        </p>
      ) : (
        <div className="space-y-3 text-xs">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <div>
              <label className="block font-mono text-[10px] uppercase text-ink-2 mb-1">Base FCF ({currency})</label>
              <input
                type="number"
                placeholder={latestFcf ? `Latest: ${(latestFcf / 1e6).toFixed(0)}M` : "e.g. 1000000000"}
                value={fcf}
                onChange={(e) => setFcf(e.target.value)}
                className="w-full rounded-card border border-border bg-bg-0 px-2 py-1 font-mono text-xs text-ink-0"
              />
            </div>
            <div>
              <label className="block font-mono text-[10px] uppercase text-ink-2 mb-1">Growth (g %)</label>
              <input
                type="number"
                placeholder="e.g. 6"
                value={growth}
                onChange={(e) => setGrowth(e.target.value)}
                className="w-full rounded-card border border-border bg-bg-0 px-2 py-1 font-mono text-xs text-ink-0"
              />
            </div>
            <div>
              <label className="block font-mono text-[10px] uppercase text-ink-2 mb-1">Discount (WACC %)</label>
              <input
                type="number"
                placeholder="e.g. 9"
                value={wacc}
                onChange={(e) => setWacc(e.target.value)}
                className="w-full rounded-card border border-border bg-bg-0 px-2 py-1 font-mono text-xs text-ink-0"
              />
            </div>
            <div>
              <label className="block font-mono text-[10px] uppercase text-ink-2 mb-1">Years</label>
              <input
                type="number"
                min="1"
                max="20"
                value={years}
                onChange={(e) => setYears(e.target.value)}
                className="w-full rounded-card border border-border bg-bg-0 px-2 py-1 font-mono text-xs text-ink-0"
              />
            </div>
          </div>

          {result && (
            <div className="rounded-card bg-bg-2/60 p-3 font-mono text-xs border border-border space-y-1">
              <div className="flex justify-between text-ink-1">
                <span>PV of Projection Period:</span>
                <span className="text-ink-0">{money(result.pvSum, currency)}</span>
              </div>
              <div className="flex justify-between text-ink-1">
                <span>PV of Terminal Value (2% perp):</span>
                <span className="text-ink-0">{money(result.pvTerminal, currency)}</span>
              </div>
              <div className="flex justify-between font-semibold text-accent pt-1 border-t border-border">
                <span>Implied Value:</span>
                <span>{money(result.enterpriseValue, currency)}</span>
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
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
    <Card
      title="Local Alert Rule"
      subtitle="Evaluated locally on page load. No push notifications."
    >
      <form onSubmit={handleSave} className="space-y-3">
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div>
            <label className="block font-mono text-[10px] uppercase text-ink-2 mb-1">Alert if PE &gt;</label>
            <input
              type="number"
              step="1"
              placeholder={currentPe ? `Current: ${currentPe.toFixed(1)}` : "e.g. 25"}
              value={peAbove}
              onChange={(e) => setPeAbove(e.target.value)}
              className="w-full rounded-card border border-border bg-bg-0 px-2.5 py-1 font-mono text-xs text-ink-0"
            />
          </div>
          <div>
            <label className="block font-mono text-[10px] uppercase text-ink-2 mb-1">Alert if Composite &lt;</label>
            <input
              type="number"
              step="0.5"
              placeholder={currentComposite ? `Current: ${currentComposite.toFixed(1)}` : "e.g. 5.0"}
              value={compBelow}
              onChange={(e) => setCompBelow(e.target.value)}
              className="w-full rounded-card border border-border bg-bg-0 px-2.5 py-1 font-mono text-xs text-ink-0"
            />
          </div>
        </div>
        <div className="flex items-center justify-between pt-1">
          <button
            type="submit"
            className="rounded-card border border-accent/60 bg-accent-weak px-3 py-1 font-mono text-xs text-accent hover:bg-accent/20 transition-colors"
          >
            {saved ? "Saved!" : "Save Alert"}
          </button>
          {alert && (
            <span className="font-mono text-[10px] text-ink-2">
              Active: {alert.pe_above ? `PE > ${alert.pe_above}` : ""} {alert.composite_below ? `Comp < ${alert.composite_below}` : ""}
            </span>
          )}
        </div>
      </form>
    </Card>
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
    <Page>
      <div className="space-y-4">
        <h1 className="font-display text-3xl tracking-tight text-ink-0">Company not found</h1>
        <p className="text-sm text-ink-1">
          No company with ID <span className="font-mono text-ink-0">{companyId}</span> in the database.
        </p>

        <Card className="max-w-md" padding="md">
          <p className="text-xs text-ink-0 font-medium mb-3">Would you like to fetch this ticker into the universe?</p>
          <button
            onClick={handleFetch}
            disabled={ingesting}
            className="rounded-card border border-accent/60 bg-accent-weak px-3 py-1.5 font-mono text-xs text-accent hover:bg-accent/20 transition-colors disabled:opacity-50"
          >
            {ingesting ? "Queueing fetch..." : `Fetch ${ticker} from SEC / Yahoo`}
          </button>
          {msg && <p className="mt-2 font-mono text-[11px] text-ink-1">{msg}</p>}
        </Card>

        <div className="flex gap-4 text-xs font-mono">
          <Link to="/screen" className="text-accent hover:underline">Go to screener →</Link>
          <Link to="/sectors" className="text-accent hover:underline">Browse sectors →</Link>
          <Link to="/" className="text-accent hover:underline">Back to the desk →</Link>
        </div>
      </div>
    </Page>
  );
}
