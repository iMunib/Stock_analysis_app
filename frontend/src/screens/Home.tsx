import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api, ApiError, enc } from "../api/client";
import type { DossierOut, RankingsOut, ResearchMetaOut } from "../api/types";
import { CompanyLink, ErrorBanner, Score, SignalBadge, Spinner } from "../components/ui";
import { SIGNAL_ORDER, signalTone } from "../api/visuals";
import { errorCatalogCopy, signalLabel } from "../api/copy";
import { getOpenedAt, getWatchlist } from "../lib/watchlist";
import { Card, Grid, Page } from "../components/layout";
import { CompositeGauge } from "../components/viz";
import { EmptyState } from "../components/feedback";
import TickerTypeahead from "../components/common/TickerTypeahead";

const LEGEND =
  "Scores lean low on purpose: most companies (713 of 720) have less than three years of history in the database, so their Growth pillar is not scored and the composite is reduced. Valuation is a strict percentile versus same-currency peers — average companies land mid-pack, not at 8.";

const INGEST_STEPS: { key: string; label: string }[] = [
  { key: "resolve", label: "Resolve" },
  { key: "filings", label: "Filings" },
  { key: "prices_shares", label: "Price & Shares" },
  { key: "sector_peers", label: "Sector & Peers" },
  { key: "score", label: "Score" },
  { key: "done", label: "Done" },
];

export default function Home() {
  const [meta, setMeta] = useState<ResearchMetaOut | null>(null);
  const [metaError, setMetaError] = useState<string | null>(null);
  const [rankUsd, setRankUsd] = useState<RankingsOut | null>(null);
  const [rankCad, setRankCad] = useState<RankingsOut | null>(null);
  const [ticker, setTicker] = useState("");
  const [ingesting, setIngesting] = useState(false);
  const [activeStep, setActiveStep] = useState<string | null>(null);
  const [stepMessage, setStepMessage] = useState<string | null>(null);
  const [errorCode, setErrorCode] = useState<string | null>(null);
  const [ingestMsg, setIngestMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const nav = useNavigate();
  const [searchParams] = useSearchParams();

  const loadMeta = useCallback(() => {
    api.researchMeta().then(setMeta).catch((e: ApiError) => setMetaError(e.message));
  }, []);
  const loadRanks = useCallback(() => {
    api.rankings("USD", 10).then(setRankUsd).catch(() => setRankUsd(null));
    api.rankings("CAD", 10).then(setRankCad).catch(() => setRankCad(null));
  }, []);

  useEffect(() => {
    loadMeta();
    loadRanks();
  }, [loadMeta, loadRanks]);

  const addTicker = useCallback(
    async (customTicker?: string) => {
      const t = (customTicker ?? ticker).trim();
      if (!t) return;
      setIngesting(true);
      setIngestMsg(null);
      setErrorCode(null);
      setActiveStep("resolve");
      setStepMessage(`Starting ingest for ${t.toUpperCase()}…`);

      try {
        const init = await api.ingest(t);
        if (init.job_id) {
          let attempts = 0;
          const interval = setInterval(async () => {
            attempts++;
            try {
              const j = await api.job(init.job_id);
              if (j.step) setActiveStep(j.step);
              if (j.message) setStepMessage(j.message);

              if (j.status === "succeeded" || j.step === "done") {
                clearInterval(interval);
                setIngesting(false);
                if (j.error_code === "SCORE_PARTIAL") {
                  setErrorCode("SCORE_PARTIAL");
                  setIngestMsg({
                    ok: true,
                    text: errorCatalogCopy("SCORE_PARTIAL", j.message),
                  });
                  setTimeout(() => nav(`/c/${enc(j.company_id || t)}`), 1200);
                } else {
                  setIngestMsg({
                    ok: true,
                    text: j.message || `${j.company_id || t} added and scored. Opening dossier…`,
                  });
                  setTimeout(() => nav(`/c/${enc(j.company_id || t)}`), 800);
                }
              } else if (j.status === "failed" || j.step === "failed") {
                clearInterval(interval);
                setIngesting(false);
                const errTxt = errorCatalogCopy(j.error_code, j.message || j.error || "Ingest failed.");
                setErrorCode(j.error_code || "INTERNAL");
                setIngestMsg({ ok: false, text: errTxt });
              } else if (attempts >= 90) {
                clearInterval(interval);
                setIngesting(false);
                setIngestMsg({ ok: false, text: errorCatalogCopy("PROVIDER_TIMEOUT") });
              }
            } catch (err) {
              clearInterval(interval);
              setIngesting(false);
              setIngestMsg({ ok: false, text: err instanceof ApiError ? err.message : String(err) });
            }
          }, 1000);
        } else {
          setIngesting(false);
          setIngestMsg({ ok: true, text: "Ingest completed. Opening…" });
          setTimeout(() => nav(`/c/${enc(init.company_id || t)}`), 800);
        }
      } catch (e) {
        setIngesting(false);
        const msg = e instanceof ApiError ? e.message : String(e);
        let code = "INTERNAL";
        if (msg.includes("LISTING_AMBIGUOUS")) code = "LISTING_AMBIGUOUS";
        else if (msg.includes("SYMBOL_NOT_FOUND")) code = "SYMBOL_NOT_FOUND";
        setErrorCode(code);
        setIngestMsg({ ok: false, text: errorCatalogCopy(code, msg) });
      }
    },
    [ticker, nav]
  );

  useEffect(() => {
    const q = searchParams.get("ingest");
    if (q && !ingesting) {
      setTicker(q);
      addTicker(q);
    }
  }, [searchParams]);

  return (
    <Page
      title={<h1 className="font-display text-3xl tracking-tight text-ink-0">The desk</h1>}
      description="A local equity-research desk for the S&P 500 and S&P/TSX Composite. Search a name up top, or browse by sector."
    >
      {metaError && <ErrorBanner message={metaError} onRetry={loadMeta} />}
      {!meta && !metaError && <Spinner label="Reading research status…" />}

      {meta && (
        <section aria-label="Database status" className="space-y-4">
          <Grid cols={4}>
            <div className="rounded-card border border-border bg-bg-1 p-4 shadow-card">
              <div className="text-[10px] font-mono uppercase tracking-wider text-ink-2">Total Universe</div>
              <div className="mt-1 flex items-baseline justify-between">
                <span className="font-mono text-2xl font-bold text-ink-0">{meta.companies}</span>
                <span className="font-mono text-[10px] text-accent">US + CA</span>
              </div>
              <div className="mt-2 text-[11px] font-mono text-ink-2">S&P 500 & TSX Composite</div>
            </div>

            <div className="rounded-card border border-border bg-bg-1 p-4 shadow-card">
              <div className="text-[10px] font-mono uppercase tracking-wider text-ink-2">Scored Coverage</div>
              <div className="mt-1 flex items-baseline justify-between">
                <span className="font-mono text-2xl font-bold text-pos">{meta.scored}</span>
                <span className="font-mono text-[10px] text-pos font-semibold">
                  {Math.round((meta.scored / (meta.companies || 1)) * 100)}%
                </span>
              </div>
              <div className="mt-2 h-1.5 w-full rounded-full bg-bg-2 overflow-hidden">
                <div
                  className="h-full bg-pos rounded-full transition-all duration-500"
                  style={{ width: `${(meta.scored / (meta.companies || 1)) * 100}%` }}
                />
              </div>
            </div>

            <div className="rounded-card border border-border bg-bg-1 p-4 shadow-card">
              <div className="text-[10px] font-mono uppercase tracking-wider text-ink-2">Data Integrity Gaps</div>
              <div className="mt-1 flex items-baseline justify-between">
                <span className="font-mono text-2xl font-bold text-warn">{meta.insufficient_data}</span>
                <span className="font-mono text-[10px] text-warn">
                  {((meta.insufficient_data / (meta.companies || 1)) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="mt-2 text-[11px] font-mono text-ink-2">Filing ingestion pending</div>
            </div>

            <div className="rounded-card border border-border bg-bg-1 p-4 shadow-card">
              <div className="text-[10px] font-mono uppercase tracking-wider text-ink-2">3Y+ Statement Depth</div>
              <div className="mt-1 flex items-baseline justify-between">
                <span className="font-mono text-2xl font-bold text-ink-0">{meta.scored - meta.growth_null}</span>
                <span className="font-mono text-[10px] text-ink-2">
                  {Math.round(((meta.scored - meta.growth_null) / (meta.scored || 1)) * 100)}%
                </span>
              </div>
              <div className="mt-2 h-1.5 w-full rounded-full bg-bg-2 overflow-hidden">
                <div
                  className="h-full bg-accent rounded-full transition-all duration-500"
                  style={{ width: `${((meta.scored - meta.growth_null) / (meta.scored || 1)) * 100}%` }}
                />
              </div>
            </div>
          </Grid>

          {meta.scored === 0 && (
            <div className="rounded-card border border-warn/50 bg-warn-weak px-4 py-3 text-sm text-ink-0">
              No scores yet — run a recompute (POST /api/v1/scores/recompute) or add a ticker below.
            </div>
          )}

          <Card padding="sm">
            <p className="text-xs text-ink-1 leading-relaxed">
              {meta.growth_null <= meta.scored * 0.15 ? (
                <>
                  <span className="font-mono text-[10px] uppercase tracking-widest text-pos font-semibold">Universe History Active · </span>
                  {meta.scored - meta.growth_null} of {meta.scored} scored companies ({Math.round(((meta.scored - meta.growth_null) / (meta.scored || 1)) * 100)}%) have multi-year statement history with active growth scoring.
                </>
              ) : (
                <>
                  <span className="font-mono text-[10px] uppercase tracking-widest text-ink-2 font-semibold">Needs history · </span>
                  {meta.growth_null} of {meta.scored} scored names lack the 3+ years of history needed to compute growth,
                  so their composite is reduced. That is the honest state of the data, not a bug.
                </>
              )}
            </p>
          </Card>

          <Card title="Signal Distribution & Market Breadth" subtitle="System-wide classification histogram across the active universe (Click any row to view screener cohort)">
            <ul className="space-y-2.5">
              {SIGNAL_ORDER.map((sig) => {
                const n = meta.signal_histogram[sig] ?? 0;
                if (!n) return null;
                const tone = signalTone(sig === "score_missing" ? null : sig);
                const color =
                  tone === "good"
                    ? "bg-pos"
                    : tone === "mid"
                      ? "bg-warn"
                      : tone === "bad"
                        ? "bg-neg"
                        : "bg-info";
                const pct = ((n / (meta.companies || 1)) * 100).toFixed(1);
                const sigParam = sig === "score_missing" ? "insufficient_data" : sig;
                return (
                  <li key={sig}>
                    <Link
                      to={`/screen?signal=${sigParam}`}
                      className="group flex items-center gap-3 text-xs p-1 rounded hover:bg-bg-2/60 transition-colors"
                      title={`Filter screener by ${signalLabel(sig === "score_missing" ? null : sig)}`}
                    >
                      <span className="w-36 shrink-0 text-ink-1 font-medium group-hover:text-accent transition-colors flex items-center justify-between">
                        <span>{signalLabel(sig === "score_missing" ? null : sig)}</span>
                        <span className="font-mono text-[10px] text-ink-2 mr-2">({pct}%)</span>
                      </span>
                      <span className="h-2 rounded-sm bg-bg-2 overflow-hidden flex-1 max-w-md">
                        <span
                          className={`block h-full rounded-sm ${color} transition-all duration-300 group-hover:brightness-110`}
                          style={{ width: `${Math.max(2, (n / meta.companies) * 100)}%` }}
                        />
                      </span>
                      <span className="font-mono tabular-nums font-semibold text-ink-0 text-right w-12 group-hover:text-accent transition-colors">
                        {n}
                      </span>
                    </Link>
                  </li>
                );
              })}
            </ul>
            <p className="mt-4 text-xs leading-relaxed text-ink-2 border-t border-border pt-3">{LEGEND}</p>
          </Card>
        </section>
      )}

      {/* Hero Add Ticker Card */}
      <Card
        title="Add a ticker to the database"
        subtitle="Pull annual history for any US or Canadian ticker (e.g. AAPL or KITS.TO), then score it. Free public sources only."
        className="border-accent/40 bg-gradient-to-b from-bg-1 to-bg-1/90"
      >
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-2 text-xs text-ink-1">
            <span className="font-mono text-[10px] uppercase tracking-widest text-ink-2">Quick try:</span>
            {["AMD", "BABA", "SHOP.TO", "KITS.TO"].map((sample) => (
              <button
                key={sample}
                type="button"
                disabled={ingesting}
                onClick={() => {
                  setTicker(sample);
                  addTicker(sample);
                }}
                className="rounded-chip border border-border bg-bg-2 px-2.5 py-1 font-mono text-xs text-ink-0 hover:border-accent/60 hover:text-accent disabled:opacity-40 transition-colors"
              >
                {sample}
              </button>
            ))}
          </div>

          <form
            className="flex flex-wrap gap-3 items-center"
            onSubmit={(e) => {
              e.preventDefault();
              addTicker();
            }}
          >
            <div className="w-full sm:w-80">
              <TickerTypeahead
                value={ticker}
                onChange={setTicker}
                ariaLabel="Ticker to add"
                onSelect={(item) => {
                  setTicker(item.ticker);
                  if (item.in_database) {
                    nav(`/c/${enc(item.company_id)}`);
                  } else {
                    addTicker(item.ticker);
                  }
                }}
                placeholder="Search ticker, name, or exchange…"
              />
            </div>
            <button
              type="submit"
              disabled={ingesting || !ticker.trim()}
              className="rounded-card border border-accent/60 bg-accent-weak px-4 py-2 text-xs font-semibold font-mono text-accent hover:bg-accent/20 disabled:opacity-40 transition-colors"
            >
              {ingesting ? "Fetching…" : "Add & score"}
            </button>
          </form>

          {ingesting && (
            <div className="space-y-3 rounded-card border border-accent/40 bg-accent-weak/20 p-4 text-xs animate-in fade-in duration-200">
              <div className="flex items-center gap-2.5 font-mono text-accent font-medium text-sm">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-accent"></span>
                </span>
                <span>
                  {stepMessage || "Enriching multi-year SEC/Yahoo statements and computing 3NF financial ratios in background…"}
                </span>
              </div>
              <p className="text-[11px] text-ink-1">
                Fetching filings, pulling market quotes, computing 3NF ratios (ROIC, Altman Z, Beneish M, Reverse DCF), and updating peer percentiles.
              </p>
              <div className="flex flex-wrap gap-1.5 pt-1">
                {INGEST_STEPS.map((s) => {
                  const isCurrent = activeStep === s.key;
                  return (
                    <span
                      key={s.key}
                      className={`rounded-chip px-2.5 py-1 font-mono text-[11px] transition-all ${
                        isCurrent
                          ? "border border-accent bg-accent/20 text-accent font-bold shadow-xs"
                          : "border border-border bg-bg-0/60 text-ink-2"
                      }`}
                    >
                      {s.label}
                    </span>
                  );
                })}
              </div>
            </div>
          )}

          {ingestMsg && (
            <p
              role="status"
              className={`rounded-card border px-3 py-2 text-xs font-mono ${
                ingestMsg.ok
                  ? errorCode === "SCORE_PARTIAL"
                    ? "border-warn/50 bg-warn-weak text-warn"
                    : "border-pos/50 bg-pos-weak text-pos"
                  : "border-neg/50 bg-neg-weak text-neg"
              }`}
            >
              {ingestMsg.text}
            </p>
          )}
        </div>
      </Card>

      <Grid cols={2}>
        <TopTable title="Top 10 — USD" rows={rankUsd?.items ?? []} />
        <TopTable title="Top 10 — CAD" rows={rankCad?.items ?? []} />
      </Grid>

      <TopTableAll />

      <ETFCohortsSection />

      <section aria-label="Watchlist" className="space-y-3">
        <div className="flex items-center justify-between border-b border-border pb-2">
          <h2 className="font-heading text-xl font-semibold text-ink-0">Watchlist</h2>
          <span className="text-xs text-ink-2 font-mono">Starred companies</span>
        </div>
        <WatchGrid />
      </section>

      <section aria-label="Browse" className="flex flex-wrap gap-4 text-xs font-mono">
        <Link to="/sectors" className="text-accent hover:underline flex items-center gap-1">
          <span>Browse all sectors</span>
          <span aria-hidden="true">→</span>
        </Link>
      </section>
    </Page>
  );
}

function WatchGrid() {
  const [watched] = useState<string[]>(() => getWatchlist());
  const [dossiers, setDossiers] = useState<DossierOut[]>([]);

  useEffect(() => {
    if (watched.length === 0) return;
    Promise.allSettled(watched.map((id) => api.dossier(id))).then((results) => {
      setDossiers(
        results
          .filter((r): r is PromiseFulfilledResult<DossierOut> => r.status === "fulfilled")
          .map((r) => r.value),
      );
    });
  }, [watched]);

  if (watched.length === 0) {
    return (
      <EmptyState
        title="Nothing watched yet"
        body="Open any company dossier and click ☆ Watch to track conviction names right here on your desk."
      />
    );
  }
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {dossiers.map((d) => {
        const openedAt = getOpenedAt(d.identity.company_id);
        const openedStr = openedAt
          ? new Date(openedAt).toLocaleDateString(undefined, { month: "short", day: "numeric" })
          : null;
        return (
          <Link
            key={d.identity.company_id}
            to={`/c/${enc(d.identity.company_id)}`}
            className="group rounded-card border border-border bg-bg-1 p-3.5 hover:border-accent/60 hover:bg-bg-2 transition-all shadow-card flex items-center justify-between gap-3"
          >
            <div className="min-w-0 flex-1">
              <div className="flex items-baseline gap-2">
                <span className="text-sm font-semibold text-ink-0 truncate group-hover:text-accent transition-colors">
                  {d.identity.name ?? d.identity.company_id}
                </span>
                <span className="font-mono text-[10px] text-ink-2 shrink-0">{d.identity.currency}</span>
              </div>
              <div className="mt-1.5 flex items-center gap-2 font-mono text-[10px] text-ink-2">
                <SignalBadge signal={d.score?.signal} small />
                <span>{openedStr ? `Opened ${openedStr}` : d.identity.company_id}</span>
              </div>
            </div>
            <div className="shrink-0">
              <CompositeGauge value={d.score?.composite} size="sm" showLabel={false} />
            </div>
          </Link>
        );
      })}
    </div>
  );
}

function TopTable({ title, rows }: { title: string; rows: RankingsOut["items"] }) {
  return (
    <Card title={title} subtitle="Deterministic math score rank">
      {rows.length === 0 ? (
        <p className="text-xs text-ink-2 py-4 text-center">No scored names yet.</p>
      ) : (
        <ul className="divide-y divide-border">
          {rows.map((r) => (
            <li key={r.company_id} className="flex items-center justify-between gap-4 py-2 text-xs">
              <div className="flex items-center gap-2 min-w-0">
                <span className="font-mono text-[10px] text-ink-2 w-5 shrink-0">#{r.rank}</span>
                <CompanyLink companyId={r.company_id} className="font-medium truncate">
                  {r.name ?? r.company_id}
                </CompanyLink>
              </div>
              <div className="flex items-center gap-2.5 shrink-0">
                <Score value={r.composite} />
                <SignalBadge signal={r.signal} small />
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

function TopTableAll() {
  const [rows, setRows] = useState<RankingsOut | null>(null);
  useEffect(() => {
    fetch("/api/v1/rankings?scope=seed&limit=10")
      .then((r) => r.json())
      .then(setRows)
      .catch(() => setRows(null));
  }, []);
  return (
    <Card
      title="Top 10 — All Universe"
      subtitle="Score-only top 10 across both USD & CAD (strictly ratio/math signals, no FX conversion)"
    >
      {!rows || rows.items.length === 0 ? (
        <p className="text-xs text-ink-2 py-4 text-center">No scored names yet.</p>
      ) : (
        <ul className="divide-y divide-border">
          {rows.items.map((r) => (
            <li key={r.company_id} className="flex items-center justify-between gap-4 py-2 text-xs">
              <div className="flex items-center gap-2 min-w-0">
                <span className="font-mono text-[10px] text-ink-2 w-5 shrink-0">#{r.rank}</span>
                <CompanyLink companyId={r.company_id} className="font-medium truncate">
                  {r.name ?? r.company_id}
                </CompanyLink>
                <span className="font-mono text-[10px] text-info shrink-0">
                  {(r as unknown as { currency?: string }).currency ?? ""}
                </span>
              </div>
              <div className="flex items-center gap-2.5 shrink-0">
                <Score value={r.composite} />
                <SignalBadge signal={r.signal} small />
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

function ETFCohortsSection() {
  const [cohorts, setCohorts] = useState<import("../api/types").ETFCohortsOut | null>(null);

  useEffect(() => {
    api.etfTopCohorts().then(setCohorts).catch(() => setCohorts(null));
  }, []);

  if (!cohorts) return null;

  const cohortsMeta = [
    {
      key: "SPUS",
      title: "SPUS — Sharia Core",
      subtitle: "Top 5 S&P 500 Halal Compounders",
      universe: "SPUS",
    },
    {
      key: "QQQ",
      title: "QQQ — Nasdaq 100",
      subtitle: "Top 5 Non-Financial Tech Leaders",
      universe: "QQQ",
    },
    {
      key: "VONV",
      title: "VONV — Value Floor",
      subtitle: "Top 5 Russell 1000 Deep Value",
      universe: "VONV",
    },
  ];

  return (
    <section aria-label="Active ETF Cohorts" className="space-y-3">
      <div className="flex items-center justify-between border-b border-border pb-2">
        <div>
          <h2 className="font-heading text-xl font-semibold text-ink-0">ETF Universe Leaders</h2>
          <p className="text-xs text-ink-2 mt-0.5">Top-ranked constituents across monitored index cohorts</p>
        </div>
        <Link to="/screen" className="text-xs font-mono text-accent hover:underline">
          Open screener →
        </Link>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {cohortsMeta.map((c) => {
          const items = cohorts[c.key] || [];
          return (
            <Card
              key={c.key}
              title={c.title}
              subtitle={c.subtitle}
              action={
                <Link
                  to={`/screen?universe=${c.universe}`}
                  className="text-xs font-mono text-accent hover:underline"
                >
                  Screen all →
                </Link>
              }
              padding="sm"
            >
              {items.length === 0 ? (
                <p className="text-xs text-ink-2 py-3 text-center">No constituents scored yet.</p>
              ) : (
                <ul className="divide-y divide-border">
                  {items.map((it, idx) => (
                    <li key={it.company_id} className="flex items-center justify-between gap-2 py-2 text-xs">
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="font-mono text-[10px] text-ink-2 w-4 shrink-0">#{idx + 1}</span>
                        <div className="min-w-0">
                          <CompanyLink companyId={it.company_id} className="font-medium truncate block">
                            {it.ticker}
                          </CompanyLink>
                          <span className="text-[10px] text-ink-2 truncate block">{it.name}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <Score value={it.composite} />
                        <SignalBadge signal={it.signal} small />
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          );
        })}
      </div>
    </section>
  );
}
