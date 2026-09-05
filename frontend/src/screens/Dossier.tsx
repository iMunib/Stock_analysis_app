import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { api, ApiError, enc } from "../api/client";
import type { CommonSizeOut, DossierOut, PractitionerOut, SimilarOut, SwotOut } from "../api/types";
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
import { PenmanCard } from "../components/PenmanCard";
import { GrahamCard } from "../components/GrahamCard";
import CashFlowWaterfall from "../components/dossier/CashFlowWaterfall";
import TradingViewChart from "../components/viz/TradingViewChart";
import StockChatDrawer from "../components/StockChatDrawer";
import { Card, Chip, Page, StatTile } from "../components/layout";
import { AltmanZGauge, CompositeGauge, PercentileMatrix, PillarRadar } from "../components/viz";
import CommonSizeTable from "../components/financials/CommonSizeTable";
import CapitalReturnCard from "../components/financials/CapitalReturnCard";
import { BeneishCard } from "../components/forensics/BeneishCard";
import { FactsheetPrintView } from "../components/dossier/FactsheetPrintView";
import ExecutiveCockpit from "../components/dossier/ExecutiveCockpit";
import FlightDeck from "../components/dossier/FlightDeck";
import EngineRoom from "../components/dossier/EngineRoom";

type DossierTab =
  | "overview"
  | "financials"
  | "valuation"
  | "forensics"
  | "capital"
  | "technicals"
  | "sources"
  | "thesis";

interface TabMeta {
  id: DossierTab;
  label: string;
  icon: string;
}

const DOSSIER_TABS: TabMeta[] = [
  { id: "overview", label: "Overview", icon: "📊" },
  { id: "financials", label: "Financials", icon: "📑" },
  { id: "valuation", label: "Valuation & Expectations", icon: "⚖️" },
  { id: "forensics", label: "Forensics & Solvency", icon: "🔍" },
  { id: "capital", label: "Capital Allocation", icon: "💵" },
  { id: "technicals", label: "Technicals & Chart", icon: "📈" },
  { id: "sources", label: "Filings & Sources", icon: "🏛️" },
  { id: "thesis", label: "Thesis & Notes", icon: "📝" },
];

export default function Dossier() {
  const { companyId = "" } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const tabParam = searchParams.get("tab") as DossierTab | null;
  const activeTab: DossierTab = DOSSIER_TABS.some((t) => t.id === tabParam)
    ? (tabParam as DossierTab)
    : "overview";

  const handleTabChange = (nextTab: DossierTab) => {
    setSearchParams(
      (prev) => {
        const p = new URLSearchParams(prev);
        p.set("tab", nextTab);
        return p;
      },
      { replace: false }
    );
  };

  const [data, setData] = useState<DossierOut | null>(null);
  const [similar, setSimilar] = useState<SimilarOut | null>(null);
  const [practitioner, setPractitioner] = useState<PractitionerOut | null>(null);
  const [commonSize, setCommonSize] = useState<CommonSizeOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const [compareSet, setCompareSet] = useState<string[]>(getCompareSelection());
  const [watched, setWatched] = useState(getWatchlist().includes(companyId));
  const [chatOpen, setChatOpen] = useState(false);
  const [showFactsheet, setShowFactsheet] = useState(false);
  const [gapActionMsg, setGapActionMsg] = useState<string | null>(null);
  const [fetchingGap, setFetchingGap] = useState(false);
  const [disclosureTier, setDisclosureTier] = useState<"level1" | "level2" | "level3">("level1");

  // Trust sprint E1: data quality & provenance
  const [dq, setDq] = useState<{
    price_freshness?: string;
    price_as_of?: string;
    statement_as_of?: string | null;
    source_count?: number;
    denominator_confidence?: string | null;
    warning_count?: number;
  } | null>(null);

  useEffect(() => {
    let cancelled = false;
    api.dossierQuality(companyId)
      .then((d) => { if (!cancelled) setDq(d); })
      .catch(() => {});
    api.practitioner(companyId)
      .then((res) => { if (!cancelled) setPractitioner(res); })
      .catch(() => {});
    api.commonSize(companyId, 5)
      .then((res) => { if (!cancelled) setCommonSize(res); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [companyId]);

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
  const isFinancialSector = (d: DossierOut) => d.identity.gics_sector === "Financials" || d.identity.custom_industry_sheet === "Banks";
  const bankNote = bankPathCopy(isFinancialSector(data));

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
    <>
    <Page breadcrumb={breadcrumb} className="!max-w-[1600px] w-full print:space-y-3">
      {alertMsg && (
        <div role="alert" className="rounded-card border border-accent/60 bg-accent-weak px-4 py-2.5 text-xs text-accent flex items-center justify-between no-print">
          <span>{alertMsg}</span>
          <span className="font-mono text-[10px] uppercase text-ink-2">Local Alert</span>
        </div>
      )}
      {gapActionMsg && (
        <div role="status" className="rounded-card border border-sky-500/40 bg-sky-500/10 px-4 py-3 text-xs text-sky-300 flex items-center justify-between no-print shadow-sm">
          <div className="flex items-center gap-2.5">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-sky-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-sky-500"></span>
            </span>
            <span className="font-medium">{gapActionMsg}</span>
          </div>
          <span className="font-mono text-[10px] uppercase text-sky-400 tracking-wider font-semibold">Background Pipeline</span>
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
            {s?.peer_rank != null && s?.peer_n != null ? `#${s.peer_rank} of ${s.peer_n} in ` : ""}
            {s?.peer_set_type === "broad_peer_set"
              ? `broad peer set (n=${s?.peer_n ?? 1})`
              : s?.peer_set_type === "custom_industry_currency"
              ? `${data.identity.custom_industry_sheet || "Custom industry"} (n=${s?.peer_n ?? 1})`
              : `${data.identity.gics_sector || "Sector"} (n=${s?.peer_n ?? 1})`}
          </span>
        </div>
      </section>

      {/* Identity Hero Split Grid: Company Identity & Metrics (Left) + Interactive Technical Chart (Right) */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
        {/* Left Col: Identity, Live Fundamentals, Rating & Action Bar (lg:col-span-6 xl:col-span-5) */}
        <Card className="lg:col-span-6 xl:col-span-5 flex flex-col justify-between" padding="lg">
          <div>
            {/* Top row: Name, ticker, and signal/score pill */}
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h1 className="font-display text-2xl sm:text-3xl font-bold tracking-tight text-ink-0">
                  {data.identity.name ?? companyId}
                </h1>
                <div className="mt-1 flex flex-wrap items-center gap-2 text-xs">
                  <span className="font-mono text-ink-2 font-semibold">{companyId}</span>
                  {cur && <Chip tone="info" size="sm">{cur}</Chip>}
                  {data.identity.gics_sector && (
                    <span className="text-ink-1 font-medium">{data.identity.gics_sector}</span>
                  )}
                  {data.identity.custom_industry_sheet && (
                    <span className="text-ink-2">· {data.identity.custom_industry_sheet}</span>
                  )}
                  {(data.identity.indexes ?? []).map((idx) => (
                    <span key={idx} className="rounded-chip border border-border px-1.5 py-0.5 font-mono text-[10px] text-ink-2 bg-bg-2/40">
                      {idx}
                    </span>
                  ))}
                </div>
              </div>

              {/* Compact Verdict & Score Badge */}
              <div className="flex items-center gap-3">
                <CompositeGauge value={s?.composite} signal={s?.signal} size="sm" />
                <div className="flex flex-col items-end gap-0.5">
                  <div className="flex items-center gap-2">
                    <SignalBadge signal={s?.signal ?? "insufficient_data"} />
                    {s?.composite != null && (
                      <span className="font-mono text-base font-bold text-accent bg-accent-weak px-2 py-0.5 rounded border border-accent/30">
                        {s.composite.toFixed(1)}/10
                      </span>
                    )}
                  </div>
                  {s?.peer_rank != null && s?.peer_n != null && (
                    <span className="font-mono text-[11px] text-ink-2">
                      #{s.peer_rank} of {s.peer_n} in {data.identity.custom_industry_sheet || data.identity.gics_sector || "peers"}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Quick Live Fundamental Metrics Bar */}
            <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-2 border-y border-border/70 py-2.5 bg-bg-2/30 px-3 rounded">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-ink-2 block">Price</span>
                <span className="font-mono text-sm font-semibold text-ink-0">
                  {typeof snap.price === "number" ? `$${snap.price.toFixed(2)}` : "—"}
                </span>
              </div>
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-ink-2 block">Market Cap</span>
                <span className="font-mono text-sm font-semibold text-ink-0">
                  {typeof snap.market_cap === "number" ? money(snap.market_cap, cur) : "—"}
                </span>
              </div>
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-ink-2 block">Trailing P/E</span>
                <span className="font-mono text-sm font-semibold text-ink-0">
                  {typeof snap.pe_calc === "number"
                    ? snap.pe_calc < 0
                      ? `Loss (${snap.pe_calc.toFixed(1)}x)`
                      : `${snap.pe_calc.toFixed(1)}x`
                    : "—"}
                </span>
              </div>
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-ink-2 block">ROIC</span>
                <span className={`font-mono text-sm font-semibold ${
                  typeof snap.roic === "number"
                    ? snap.roic < 0 ? "text-neg" : "text-pos"
                    : typeof snap.roic_calc === "number"
                    ? snap.roic_calc < 0 ? "text-neg" : "text-pos"
                    : "text-ink-0"
                }`}>
                  {typeof snap.roic === "number"
                    ? `${(snap.roic * (Math.abs(snap.roic) <= 1 ? 100 : 1)).toFixed(1)}%`
                    : typeof snap.roic_calc === "number"
                    ? `${(snap.roic_calc * (Math.abs(snap.roic_calc) <= 1 ? 100 : 1)).toFixed(1)}%`
                    : "—"}
                </span>
              </div>
            </div>

            {/* Profile summary with clamp */}
            <p className="mt-3 text-xs text-ink-1 leading-relaxed line-clamp-3">
              {data.profile?.summary || "No summary available."}
            </p>

            {/* Quality & Safety Flags */}
            <div className="mt-2.5 flex flex-wrap items-center justify-between gap-1" aria-label="Flags">
              <div className="flex flex-wrap gap-1">
                {dossierFlags(data).slice(0, 4).map((f) => (
                  <Chip
                    key={f.key}
                    size="sm"
                    tone={f.tone === "good" ? "positive" : f.tone === "bad" ? "negative" : f.tone === "mid" ? "warning" : "info"}
                  >
                    {f.label}
                  </Chip>
                ))}
              </div>
              {s?.signal && (
                <span className="text-[10px] font-mono text-ink-2 hidden sm:inline">
                  {signalCopy(s.signal)}
                </span>
              )}
            </div>
            <p className="mt-2 text-[10px] font-mono uppercase tracking-wider text-ink-2 border-t border-border/40 pt-1.5 truncate">
              {provenanceSentence(data)}
            </p>
          </div>

          {/* Action Toolbar */}
          <div className="mt-4 pt-3 border-t border-border flex flex-wrap items-center gap-2 text-xs no-print">
            {edgarLink && (
              <a href={edgarLink} target="_blank" rel="noreferrer" className="text-accent hover:underline font-mono text-xs">
                {filingType} filings on EDGAR ↗
              </a>
            )}
            {data.identity.country === "CA" && (
              <a href="https://www.sedarplus.ca/csa-party/records/document.html" target="_blank" rel="noreferrer" className="text-accent hover:underline font-mono text-xs">
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
              onClick={() => setShowFactsheet(true)}
              className="rounded-card border border-accent/60 bg-accent-weak px-2.5 py-1 text-xs font-mono text-accent hover:bg-accent/20 transition-colors flex items-center gap-1.5"
              title="Open 2-page institutional research factsheet"
            >
              <span>🖨️</span> Factsheet Memo
            </button>
            <button
              onClick={() => window.print()}
              className="rounded-card border border-border px-2.5 py-1 text-xs font-mono text-ink-1 hover:border-accent hover:text-ink-0 transition-colors"
              title="Print clean summary"
            >
              Print / Save PDF
            </button>
            <button
              onClick={() => setChatOpen(true)}
              className="rounded-card border border-accent/60 bg-accent-weak px-2.5 py-1 text-xs font-mono text-accent hover:bg-accent/20 transition-colors"
              title="Open fact-grounded research assistant"
            >
              💬 Ask Analyst AI
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

        {/* Right Col: Interactive Live Technical Price Chart (lg:col-span-6 xl:col-span-7) */}
        <Card className="lg:col-span-6 xl:col-span-7 flex flex-col p-2 sm:p-3 overflow-hidden shadow-card" padding="none">
          <div className="flex items-center justify-between px-3 py-2 border-b border-border/60 bg-bg-2/30">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-ink-0 flex items-center gap-1.5">
                <span>📈</span> Live Technical Chart
              </span>
              <span className="text-[11px] font-mono text-ink-2">
                ({data.identity.ticker || companyId} · Weekly Candlesticks)
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] font-mono font-medium text-pos bg-pos-weak border border-pos/30">
                <span className="w-1.5 h-1.5 rounded-full bg-pos animate-pulse" /> Live
              </span>
              <button
                onClick={() => handleTabChange("technicals")}
                className="text-[11px] font-mono text-accent hover:underline flex items-center gap-1"
                title="Expand to full technical analysis workbench"
              >
                <span>Full Screen</span> ↗
              </button>
            </div>
          </div>
          <div className="w-full flex-1 min-h-[360px] sm:min-h-[400px]">
            <TradingViewChart
              companyId={companyId}
              ticker={data.identity.ticker ?? undefined}
              currency={cur ?? undefined}
              tradingviewSymbol={data.identity.tradingview_symbol ?? undefined}
              height={400}
              className="w-full h-full rounded"
            />
          </div>
        </Card>
      </div>

      {/* 3-Tier Progressive Disclosure Switcher Bar */}
      <div className="rounded-card border border-border bg-bg-1 p-3 shadow-card flex flex-wrap items-center justify-between gap-3 no-print">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold uppercase tracking-wider text-ink-2 font-heading">
            Disclosure Tier:
          </span>
          <div className="inline-flex rounded-card p-1 bg-bg-0 border border-border" role="group" aria-label="Progressive disclosure tier">
            <button
              type="button"
              onClick={() => setDisclosureTier("level1")}
              className={`px-3 py-1 rounded text-xs font-mono font-semibold transition-all ${
                disclosureTier === "level1"
                  ? "bg-accent text-bg-0 shadow-xs font-bold"
                  : "text-ink-1 hover:text-ink-0 hover:bg-bg-2"
              }`}
            >
              ⚡ Level 1: 60s Cockpit
            </button>
            <button
              type="button"
              onClick={() => setDisclosureTier("level2")}
              className={`px-3 py-1 rounded text-xs font-mono font-semibold transition-all ${
                disclosureTier === "level2"
                  ? "bg-accent text-bg-0 shadow-xs font-bold"
                  : "text-ink-1 hover:text-ink-0 hover:bg-bg-2"
              }`}
            >
              ✈ Level 2: Flight Deck
            </button>
            <button
              type="button"
              onClick={() => setDisclosureTier("level3")}
              className={`px-3 py-1 rounded text-xs font-mono font-semibold transition-all ${
                disclosureTier === "level3"
                  ? "bg-accent text-bg-0 shadow-xs font-bold"
                  : "text-ink-1 hover:text-ink-0 hover:bg-bg-2"
              }`}
            >
              ⚙ Level 3: Engine Room
            </button>
          </div>
        </div>
        <div className="text-[11px] font-mono text-ink-2 hidden sm:flex items-center gap-1.5">
          <span>Focus:</span>
          <span className="text-accent font-semibold">
            {disclosureTier === "level1"
              ? "Safety Verdict & Plain-English Market Expectation"
              : disclosureTier === "level2"
              ? "4-Pillar Radar & SBC Dilution Shareholder Yield"
              : "8-Variable Beneish Matrix & Penman Spread"}
          </span>
        </div>
      </div>

      {/* Institutional Workspace Tab Navigation Bar */}
      <nav
        role="tablist"
        aria-label="Research terminal workspace navigation"
        className="flex items-center gap-1.5 border-b border-border bg-bg-1 p-1.5 rounded-card shadow-sm no-print overflow-x-auto no-scrollbar scrollbar-none flex-nowrap sm:flex-wrap"
      >
        {DOSSIER_TABS.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              role="tab"
              id={`tab-${tab.id}`}
              aria-controls={`tabpanel-${tab.id}`}
              aria-selected={isActive}
              onClick={() => handleTabChange(tab.id)}
              className={`flex items-center gap-2 px-3 py-2 rounded text-xs font-medium whitespace-nowrap transition-all ${
                isActive
                  ? "bg-accent-weak text-accent font-semibold shadow-sm border border-accent/40"
                  : "text-ink-1 hover:text-ink-0 hover:bg-bg-2/70 border border-transparent"
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          );
        })}
      </nav>

      {/* ========================================================================= */}
      {/* TAB 1: OVERVIEW                                                           */}
      {/* ========================================================================= */}
      {activeTab === "overview" && (
        <div role="tabpanel" id="tabpanel-overview" aria-labelledby="tab-overview" className="space-y-5">
          {/* Dynamic Progressive Disclosure Tier View */}
          {disclosureTier === "level1" && (
            <ExecutiveCockpit data={data} practitioner={practitioner} />
          )}
          {disclosureTier === "level2" && (
            <FlightDeck data={data} practitioner={practitioner} />
          )}
          {disclosureTier === "level3" && (
            <EngineRoom data={data} practitioner={practitioner} commonSize={commonSize} />
          )}
          {/* Executive Safety Verdict (Moat / Solvency / Safety) */}
          {practitioner?.behavioral?.executive_safety_verdict && (
            <Card
              title="60-Second Executive Safety Verdict"
              subtitle="Behavioral guardrails & structural solvency checklist (Housel & Sethi)"
              padding="md"
            >
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 rounded border border-border bg-surface-2">
                  <span className="text-[10px] uppercase font-mono text-ink-2">Moat Durability</span>
                  <div className={`text-base font-bold font-mono mt-1 ${
                    practitioner.behavioral.executive_safety_verdict.moat_durability === "Pass" ? "text-pos" : "text-warn"
                  }`}>
                    {practitioner.behavioral.executive_safety_verdict.moat_durability}
                  </div>
                </div>
                <div className="p-3 rounded border border-border bg-surface-2">
                  <span className="text-[10px] uppercase font-mono text-ink-2">Solvency Runway</span>
                  <div className={`text-base font-bold font-mono mt-1 ${
                    practitioner.behavioral.executive_safety_verdict.solvency_runway === "Pass" ? "text-pos" : "text-warn"
                  }`}>
                    {practitioner.behavioral.executive_safety_verdict.solvency_runway}
                  </div>
                </div>
                <div className="p-3 rounded border border-border bg-surface-2">
                  <span className="text-[10px] uppercase font-mono text-ink-2">Valuation Safety</span>
                  <div className={`text-base font-bold font-mono mt-1 ${
                    practitioner.behavioral.executive_safety_verdict.valuation_safety === "Pass" ? "text-pos" : "text-warn"
                  }`}>
                    {practitioner.behavioral.executive_safety_verdict.valuation_safety}
                  </div>
                </div>
                <div className={`p-3 rounded border ${
                  practitioner.behavioral.executive_safety_verdict.overall === "Pass"
                    ? "bg-pos-weak border-pos/30 text-pos"
                    : "bg-warn-weak border-warn/30 text-warn"
                }`}>
                  <span className="text-[10px] uppercase font-mono font-semibold">Overall Verdict</span>
                  <div className="text-base font-bold font-mono mt-1">
                    {practitioner.behavioral.executive_safety_verdict.overall}
                  </div>
                </div>
              </div>

              {practitioner.behavioral.fomo_risk && (
                <div className="mt-3 px-3 py-2 rounded bg-warn-weak border border-warn/40 text-xs text-ink-0 flex items-center gap-2">
                  <span className="inline-block w-2 h-2 rounded-full bg-warn" />
                  <span>
                    <strong>Anti-FOMO Guardrail:</strong> Valuation multiple is &gt;2 standard deviations above historical baseline. Exercise caution before market multiple contraction.
                  </span>
                </div>
              )}
            </Card>
          )}

          {/* Score Pillars: Radar Chart + 4 StatTiles */}
          <section aria-label="Score pillars" id="pillars">
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
                        className="rounded-card border border-border bg-bg-2/50 p-3.5 text-left hover:border-accent/60 hover:bg-bg-2 transition-all"
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

          {/* Key Valuation & Quality StatTiles */}
          <section aria-label="Latest snapshot">
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
                <Tile
                  label="Free cash flow"
                  tip="FCF margin"
                  value={
                    num("fcf_calc") != null
                      ? money(num("fcf_calc"), cur)
                      : isFinancialSector(data)
                      ? "N/A (Bank Model)"
                      : "—"
                  }
                  yoy={yoyOf(history, "fcf_calc")}
                />
                <Tile label="ROE" tip="ROE" value={percentish(num("roe_calc"))} />
                <Tile label="ROA" tip="ROA" value={percentish(num("roa_calc"))} />
                <Tile
                  label="FCF margin"
                  tip="FCF margin"
                  value={
                    num("fcfmargin_calc") != null
                      ? percentish(num("fcfmargin_calc"))
                      : isFinancialSector(data)
                      ? "N/A (Bank Model)"
                      : "—"
                  }
                />
                <Tile
                  label="Gross margin"
                  tip="Gross margin"
                  value={
                    num("grossmargin_calc") != null
                      ? percentish(num("grossmargin_calc"))
                      : isFinancialSector(data)
                      ? "N/A (Bank Model)"
                      : "—"
                  }
                />
                <Tile
                  label="PE"
                  tip="PE"
                  value={
                    num("pe_calc") != null
                      ? multiple(num("pe_calc"))
                      : (snap as any).pe_flag || (num("diluted_eps") != null && (num("diluted_eps") as number) < 0 ? `Loss (${multiple(num("diluted_eps"))})` : "—")
                  }
                />
                <Tile
                  label="PB"
                  tip="PB"
                  value={
                    num("pb_calc") != null
                      ? multiple(num("pb_calc"))
                      : (snap as any).pb_flag || (num("book_equity") != null && (num("book_equity") as number) <= 0 ? "Deficit (Buybacks)" : "—")
                  }
                />
                <Tile
                  label="EV/EBITDA"
                  tip="EV/EBITDA"
                  value={
                    num("ev_to_ebitda_calc") != null
                      ? multiple(num("ev_to_ebitda_calc"))
                      : (snap as any).ev_to_ebitda_flag || (isFinancialSector(data) ? "N/A (Bank Model)" : (num("ebitda") != null && (num("ebitda") as number) <= 0 ? "Negative EBITDA" : "—"))
                  }
                />
                <Tile label="Price" tip="Price" value={money(num("price"), (snap.price_currency as string) ?? cur)} />
                <Tile label="Market cap" tip="Market cap" value={money(num("market_cap"), (snap.price_currency as string) ?? cur)} />
                <Tile
                  label="Total debt"
                  tip="Total debt"
                  value={
                    num("total_debt") != null
                      ? money(num("total_debt"), cur)
                      : isFinancialSector(data)
                      ? "N/A (Bank Model)"
                      : "—"
                  }
                />
                <Tile label="Cash + ST inv." tip="Cash + ST inv." value={money(num("cash_st_investments"), cur)} />
                <Tile
                  label="Net debt"
                  tip="Net debt"
                  value={
                    num("netdebt_calc") != null
                      ? money(num("netdebt_calc"), cur)
                      : isFinancialSector(data)
                      ? "N/A (Bank Model)"
                      : "—"
                  }
                />
                <Tile label="Shares" tip="Shares" value={num("shares_snapshot") != null ? (snap.shares_snapshot as number).toLocaleString() : "—"} />
                <Tile label="Book equity" tip="Book equity" value={money(num("book_equity"), cur)} />
                <Tile
                  label="Dividend yield"
                  tip={null}
                  value={data.profile?.dividend_yield != null ? `${(data.profile.dividend_yield * (data.profile.dividend_yield <= 0.15 ? 100 : 1)).toFixed(2)}%` : "—"}
                />
                <Tile
                  label="Next earnings"
                  tip={null}
                  value={data.profile?.next_earnings_date || "—"}
                />
              </div>
            </Card>
          </section>

          {/* Why + Missing + Similar Peers */}
          <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
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
          </div>

          {/* Halal Screening Summary */}
          {data.halal && (
            <Card title="Halal Screening (AAOIFI)" subtitle="Informational compliance flag — never a filter" padding="sm">
              <div className="flex flex-wrap items-center gap-2 text-xs">
                <HalalBadge status={data.halal.status ?? "unknown"} />
                <span className="text-ink-1">{halalCopy(data.halal.status)}</span>
              </div>
            </Card>
          )}

          {/* Plain-English Narration Panel & SWOT */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
            <div className="lg:col-span-6">
              <SwotCard companyId={companyId} />
            </div>
            <div className="lg:col-span-6">
              <NarrationPanel endpoint={`/api/v1/companies/${enc(companyId)}/narrate`} label="Deterministic AI Narration" />
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: FINANCIALS                                                         */}
      {/* ========================================================================= */}
      {activeTab === "financials" && (
        <div role="tabpanel" id="tabpanel-financials" aria-labelledby="tab-financials" className="space-y-5">
          {/* Annual & Quarterly Statements */}
          <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
            <section aria-label="Annual history" className="lg:col-span-8">
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
            <section aria-label="History bars" className="lg:col-span-4">
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
          </div>

          {/* Common-Size Statements & Margin Drift */}
          <CommonSizeTable data={commonSize} currency={cur} />

          {/* Executive Cash Flow Waterfall (Ittelson Method) */}
          <section aria-label="Cash Flow Waterfall" className="space-y-4">
            <CashFlowWaterfall
              revenue={num("revenue")}
              grossProfit={num("gross_profit")}
              netIncome={num("net_income")}
              cfo={num("operating_cash_flow")}
              fcf={num("fcf_calc") ?? num("free_cash_flow")}
              currency={cur ?? undefined}
            />
          </section>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 3: VALUATION & EXPECTATIONS                                           */}
      {/* ========================================================================= */}
      {activeTab === "valuation" && (
        <div role="tabpanel" id="tabpanel-valuation" aria-labelledby="tab-valuation" className="space-y-5">
          {/* Reverse DCF Card */}
          <ReverseDCFCard companyId={companyId} />

          {/* Benjamin Graham Value Floors */}
          <GrahamCard companyId={companyId} />

          {/* Koyfin-Style Sector Percentile Matrix */}
          <PercentileMatrix
            percentiles={s?.percentiles}
            sectorName={data.identity.custom_industry_sheet || data.identity.gics_sector}
            currency={cur}
          />

          {/* Malkiel & Collins 8% Nominal Hurdle */}
          {practitioner?.malkiel && (() => {
            const m = practitioner.malkiel;
            const hurdle = m.index_hurdle_rate ?? m.index_nominal_hurdle_pct ?? 8.0;
            const reqGrowth = m.required_fcf_growth_10y ?? m.required_fcf_growth_pct;
            const interp = m.opportunity_cost_benchmark ?? m.interpretation;

            return (
              <Card
                title="Index Opportunity Cost Hurdle (Malkiel &amp; Collins)"
                subtitle="Comparison against a low-cost passive 8.0% nominal index return"
                padding="md"
              >
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-3">
                  <div className="p-3 rounded border border-border bg-surface-2">
                    <span className="text-[10px] uppercase font-mono text-ink-2">Long-Term Index Hurdle</span>
                    <div className="text-xl font-bold font-mono text-accent mt-1">
                      {hurdle != null ? `${hurdle.toFixed(1)}%` : "8.0%"}
                    </div>
                    <span className="text-[10px] text-ink-2">Nominal equity baseline</span>
                  </div>
                  <div className="p-3 rounded border border-border bg-surface-2">
                    <span className="text-[10px] uppercase font-mono text-ink-2">Current FCF Yield</span>
                    <div className="text-xl font-bold font-mono text-ink-0 mt-1">
                      {m.fcf_yield_pct != null
                        ? `${m.fcf_yield_pct.toFixed(2)}%`
                        : "—"}
                    </div>
                    <span className="text-[10px] text-ink-2">Cash return on enterprise</span>
                  </div>
                  <div className="p-3 rounded border border-border bg-surface-2">
                    <span className="text-[10px] uppercase font-mono text-ink-2">Required FCF Growth</span>
                    <div className={`text-xl font-bold font-mono mt-1 ${
                      (reqGrowth ?? 0) <= 5 ? "text-pos" : "text-warn"
                    }`}>
                      {reqGrowth != null
                        ? `${reqGrowth.toFixed(2)}%`
                        : "—"}
                    </div>
                    <span className="text-[10px] text-ink-2">To beat index over 10Y</span>
                  </div>
                </div>
                {interp && (
                  <p className="text-xs text-ink-1 leading-relaxed border-t border-border pt-2">
                    {interp}
                  </p>
                )}
              </Card>
            );
          })()}

          {/* Toy DCF Calculator */}
          <ToyDcfCard
            isBank={data.identity.custom_industry_sheet === "Banks" || data.identity.gics_sector === "Financials"}
            latestFcf={num("fcf_calc")}
            currency={cur ?? "USD"}
          />
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 4: FORENSICS & SOLVENCY                                               */}
      {/* ========================================================================= */}
      {activeTab === "forensics" && (
        <div role="tabpanel" id="tabpanel-forensics" aria-labelledby="tab-forensics" className="space-y-5">
          {/* Stephen Penman Operating vs Financing Decomposition */}
          <PenmanCard companyId={companyId} />

          {/* Howard Schilit Forensic Accounting Suite */}
          <ForensicCard companyId={companyId} />

          {/* Beneish M-Score 8-Variable Manipulation Engine */}
          <BeneishCard analysis={practitioner?.beneish_analysis} />

          {/* Martin Fridson Reality Spread */}
          {practitioner?.fridson && (
            <Card
              title="Martin Fridson Reality Check"
              subtitle="EBITDA vs Cash Flow Reality Spread &amp; Fixed-Charge Solvency"
              padding="md"
            >
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-3">
                <div className="p-3 rounded border border-border bg-surface-2">
                  <span className="text-[10px] uppercase font-mono text-ink-2">EBITDA Reality Spread</span>
                  <div className={`text-xl font-bold font-mono mt-1 ${
                    (practitioner.fridson.reality_spread ?? 0) > 0 ? "text-warn" : "text-pos"
                  }`}>
                    {practitioner.fridson.reality_spread != null
                      ? money(practitioner.fridson.reality_spread, cur)
                      : "—"}
                  </div>
                  <span className="text-[10px] text-ink-2">EBITDA − CFO divergence</span>
                </div>
                <div className="p-3 rounded border border-border bg-surface-2">
                  <span className="text-[10px] uppercase font-mono text-ink-2">Fixed-Charge Coverage</span>
                  <div className={`text-xl font-bold font-mono mt-1 ${
                    (practitioner.fridson.fixed_charge_coverage ?? 0) >= 3 ? "text-pos" : "text-warn"
                  }`}>
                    {practitioner.fridson.fixed_charge_coverage != null
                      ? `${practitioner.fridson.fixed_charge_coverage.toFixed(2)}x`
                      : "—"}
                  </div>
                  <span className="text-[10px] text-ink-2">(EBIT + Lease) / (Int + Lease)</span>
                </div>
                <div className="p-3 rounded border border-border bg-surface-2">
                  <span className="text-[10px] uppercase font-mono text-ink-2">Accounting Signal</span>
                  <div className="text-sm font-semibold font-mono mt-1 text-ink-0">
                    {practitioner.fridson.flag || "Accruals Normal"}
                  </div>
                </div>
              </div>
              {practitioner.fridson.interpretation && (
                <p className="text-xs text-ink-1 leading-relaxed border-t border-border pt-2">
                  {practitioner.fridson.interpretation}
                </p>
              )}
            </Card>
          )}

          {/* GuruFocus-Style Altman Solvency & Distress Gauge */}
          <AltmanZGauge distress={practitioner?.distress_analysis} />
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 5: CAPITAL ALLOCATION                                                 */}
      {/* ========================================================================= */}
      {activeTab === "capital" && (
        <div role="tabpanel" id="tabpanel-capital" aria-labelledby="tab-capital" className="space-y-5">
          <CapitalReturnCard data={practitioner?.shareholder_yield} />
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 6: TECHNICALS & CHART                                                 */}
      {/* ========================================================================= */}
      {activeTab === "technicals" && (
        <div role="tabpanel" id="tabpanel-technicals" aria-labelledby="tab-technicals" className="space-y-5">
          <Card
            title="Interactive Technical Chart"
            subtitle={`${data.identity.ticker ?? companyId} · Official TradingView embed · reference only`}
          >
            <TradingViewChart
              companyId={companyId}
              ticker={data.identity.ticker ?? undefined}
              currency={data.identity.currency ?? undefined}
              tradingviewSymbol={data.identity.tradingview_symbol ?? undefined}
              height={520}
            />
          </Card>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 7: FILINGS & SOURCES                                                  */}
      {/* ========================================================================= */}
      {activeTab === "sources" && (
        <div role="tabpanel" id="tabpanel-sources" aria-labelledby="tab-sources" className="space-y-5">
          <Card title="Data Quality &amp; Provenance" subtitle="Audited filings registry and snapshot freshness">
            {dq ? (
              <dl className="grid grid-cols-2 gap-4 text-xs sm:grid-cols-3 lg:grid-cols-6">
                <div>
                  <dt className="font-mono uppercase text-ink-2">Price freshness</dt>
                  <dd className="mt-1 font-mono text-ink-0 font-semibold">
                    {dq.price_freshness ?? "unknown"}
                    {dq.price_as_of ? ` · ${dq.price_as_of.slice(0, 10)}` : ""}
                  </dd>
                </div>
                <div>
                  <dt className="font-mono uppercase text-ink-2">Statement date</dt>
                  <dd className="mt-1 font-mono text-ink-0 font-semibold">{dq.statement_as_of ?? "—"}</dd>
                </div>
                <div>
                  <dt className="font-mono uppercase text-ink-2">Source count</dt>
                  <dd className="mt-1 font-mono text-ink-0 font-semibold">{dq.source_count ?? 0}</dd>
                </div>
                <div>
                  <dt className="font-mono uppercase text-ink-2">History warnings</dt>
                  <dd className="mt-1 font-mono text-ink-0 font-semibold">{dq.warning_count ?? 0}</dd>
                </div>
                <div>
                  <dt className="font-mono uppercase text-ink-2">Denominator confidence</dt>
                  <dd className="mt-1 font-mono text-ink-0 font-semibold">{dq.denominator_confidence ?? "—"}</dd>
                </div>
                <div>
                  <dt className="font-mono uppercase text-ink-2">Schema Migration</dt>
                  <dd className="mt-1 font-mono text-ink-0 font-semibold">Alembic head</dd>
                </div>
              </dl>
            ) : (
              <p className="text-xs text-ink-2">Provenance data unavailable.</p>
            )}
          </Card>

          <Card title="Direct Regulatory Filings" subtitle="Official regulatory portals">
            <div className="space-y-3 text-xs">
              {edgarLink && (
                <div className="p-3 rounded border border-border bg-surface-2 flex items-center justify-between">
                  <div>
                    <strong className="text-ink-0">SEC EDGAR System:</strong>
                    <p className="text-ink-2 mt-0.5">Verified CIK: {data.identity.cik || "Resolved by ticker"}</p>
                  </div>
                  <a
                    href={edgarLink}
                    target="_blank"
                    rel="noreferrer"
                    className="px-3 py-1 rounded bg-accent text-bg-0 font-semibold hover:opacity-90 transition-opacity"
                  >
                    View {filingType} on EDGAR ↗
                  </a>
                </div>
              )}

              {data.identity.country === "CA" && (
                <div className="p-3 rounded border border-border bg-surface-2 flex items-center justify-between">
                  <div>
                    <strong className="text-ink-0">SEDAR+ Canadian System:</strong>
                    <p className="text-ink-2 mt-0.5">Official Canadian securities filings repository</p>
                  </div>
                  <a
                    href="https://www.sedarplus.ca/csa-party/records/document.html"
                    target="_blank"
                    rel="noreferrer"
                    className="px-3 py-1 rounded bg-accent text-bg-0 font-semibold hover:opacity-90 transition-opacity"
                  >
                    View on SEDAR+ ↗
                  </a>
                </div>
              )}
            </div>
          </Card>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 8: THESIS & NOTES                                                     */}
      {/* ========================================================================= */}
      {activeTab === "thesis" && (
        <div role="tabpanel" id="tabpanel-thesis" aria-labelledby="tab-thesis" className="space-y-5">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
            <div className="lg:col-span-8">
              <ThesisNotepad companyId={companyId} />
            </div>
            <div className="lg:col-span-4 space-y-5">
              <AlertSettingsCard companyId={companyId} currentPe={num("pe_calc")} currentComposite={s?.composite} />
              <div className="p-4 rounded-card border border-border bg-surface-1">
                <span className="font-mono text-[10px] uppercase text-ink-2 font-semibold block mb-2">
                  Institutional Export
                </span>
                <button
                  onClick={() => setShowFactsheet(true)}
                  className="w-full rounded-card border border-accent/60 bg-accent-weak p-2.5 font-mono text-xs text-accent hover:bg-accent/20 transition-colors flex items-center justify-center gap-2"
                >
                  <span>🖨️</span> Open 2-Page Factsheet Memo
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Sticky Bottom Actions Bar */}
      <section aria-label="Actions" className="mt-6 pt-4 border-t border-border flex flex-wrap items-center justify-between gap-4 text-xs font-mono no-print">
        <label className="flex cursor-pointer items-center gap-2 text-ink-1 hover:text-ink-0 transition-colors">
          <input
            type="checkbox"
            checked={compareSet.includes(companyId)}
            onChange={() => setCompareSet(toggleCompareSelection(companyId))}
            className="h-4 w-4 rounded border-border bg-bg-0 accent-accent"
          />
          <span>Add to compare selection</span>
        </label>

        <div className="flex items-center gap-4">
          {similar && similar.items.length > 0 && (
            <Link
              to={`/compare?ids=${[companyId, ...similar.items.slice(0, 3).map((i) => i.company_id)].map(enc).join(",")}`}
              className="text-accent hover:underline"
            >
              Compare with top 3 peers →
            </Link>
          )}
          {compareSet.length >= 2 && (
            <Link to={`/compare?ids=${compareSet.map(enc).join(",")}`} className="text-accent hover:underline font-semibold">
              Open Compare Desk ({compareSet.length}) →
            </Link>
          )}
        </div>
      </section>
    </Page>

    {/* 2-Page Institutional Research Factsheet Modal */}
    {showFactsheet && data && (
      <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm overflow-y-auto p-4 sm:p-8 flex justify-center no-print">
        <div className="relative w-full max-w-4xl bg-white rounded-xl shadow-2xl overflow-hidden my-auto border border-slate-300">
          <FactsheetPrintView
            dossier={data}
            practitioner={practitioner}
            commonSize={commonSize}
            onClose={() => setShowFactsheet(false)}
          />
        </div>
      </div>
    )}

    {/* Slide-over Fact-Grounded AI Research Assistant */}
    <StockChatDrawer
      companyId={companyId}
      companyName={data.identity.name ?? undefined}
      isOpen={chatOpen}
      onClose={() => setChatOpen(false)}
    />
    </>
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
      title="Moat &amp; SWOT Draft"
      subtitle="LLM draft from our facts JSON. Not a 10-K."
      action={
        !swot && !loading ? (
          <button
            onClick={draft}
            className="rounded-card border border-accent/60 bg-accent-weak px-3 py-1 font-mono text-xs text-accent hover:bg-accent/20 transition-colors"
          >
            Draft SWOT from numbers
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
        rows={6}
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
  const [jobId, setJobId] = useState<string | null>(null);
  const [stepText, setStepText] = useState<string>("Initializing ingestion pipeline…");
  const [activeStep, setActiveStep] = useState<number>(0);
  const [secondsElapsed, setSecondsElapsed] = useState<number>(0);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  const parts = companyId.split(":");
  const ticker = (parts.length >= 2 ? parts[1] : companyId).toUpperCase();

  const steps = [
    "Connecting to SEC EDGAR & Yahoo Finance API",
    "Extracting multi-year 10-K / 10-Q financial statements",
    "Computing 3NF financial ratios, Altman Z, Beneish M-Score & ROIC",
    "Calibrating peer percentiles and composite scores",
  ];

  // Auto-tick elapsed timer while ingesting
  useEffect(() => {
    let timer: any;
    if (ingesting && !done) {
      timer = setInterval(() => {
        setSecondsElapsed((s) => s + 1);
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [ingesting, done]);

  // Advance step animation while job is running
  useEffect(() => {
    let stepTimer: any;
    if (ingesting && !done) {
      stepTimer = setInterval(() => {
        setActiveStep((prev) => (prev < steps.length - 1 ? prev + 1 : prev));
      }, 3500);
    }
    return () => clearInterval(stepTimer);
  }, [ingesting, done, steps.length]);

  const handleFetch = () => {
    setIngesting(true);
    setErrorMsg(null);
    setDone(false);
    setSecondsElapsed(0);
    setActiveStep(0);
    setStepText("Contacting ingest queue…");

    api
      .ingest(ticker)
      .then((res) => {
        if (res.job_id) {
          setJobId(res.job_id);
          setStepText("Pipeline running in background…");
          const interval = setInterval(async () => {
            try {
              const j = await api.job(res.job_id!);
              if (j.status === "succeeded" || j.step === "done") {
                clearInterval(interval);
                setDone(true);
                setActiveStep(steps.length);
                setStepText("Enrichment complete! Loading complete fundamentals…");
                setTimeout(() => window.location.reload(), 1500);
              } else if (j.status === "failed") {
                clearInterval(interval);
                setIngesting(false);
                setErrorMsg(j.message || "Ingestion pipeline encountered an error.");
              } else if (j.step) {
                setStepText(`Step: ${j.step}`);
              }
            } catch {
              // Fallback reload if job completed and was cleared
              clearInterval(interval);
              setTimeout(() => window.location.reload(), 2000);
            }
          }, 1500);
        } else {
          setDone(true);
          setTimeout(() => window.location.reload(), 1200);
        }
      })
      .catch((e: ApiError) => {
        setErrorMsg(e.message || "Network error queueing ingestion.");
        setIngesting(false);
      });
  };

  return (
    <Page>
      <div className="max-w-2xl mx-auto py-8 space-y-6">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-accent-weak text-accent border border-accent/40">
              {ticker}
            </span>
            <span className="font-mono text-xs text-ink-2">{companyId}</span>
          </div>
          <h1 className="font-display text-3xl font-bold tracking-tight text-ink-0">
            {ingesting ? `Enriching ${ticker} Fundamentals…` : `${ticker} Not Yet in Library`}
          </h1>
          <p className="text-sm text-ink-1">
            {ingesting
              ? "The automated Python ingestion and calculation pipeline is running in the background. Multi-year SEC filings and financial ratios are being computed."
              : "This stock is not currently indexed in the local 720-company universe. You can dynamically ingest and calculate all fundamentals right now."}
          </p>
        </div>

        {ingesting ? (
          <Card padding="lg" className="border-accent/40 bg-bg-1 shadow-card space-y-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-accent"></span>
                </span>
                <span className="font-mono text-xs font-semibold text-ink-0">
                  {done ? "Completed!" : stepText}
                </span>
              </div>
              <span className="font-mono text-xs text-ink-2">
                {secondsElapsed}s elapsed
              </span>
            </div>

            {/* Stepper */}
            <div className="space-y-3">
              {steps.map((s, idx) => {
                const isPassed = activeStep > idx || done;
                const isCurrent = activeStep === idx && !done;
                return (
                  <div key={s} className="flex items-center gap-3 text-xs">
                    <div
                      className={`h-5 w-5 rounded-full flex items-center justify-center font-mono text-[10px] font-bold shrink-0 transition-colors ${
                        isPassed
                          ? "bg-pos/20 text-pos border border-pos/40"
                          : isCurrent
                          ? "bg-accent text-bg-0 animate-pulse font-bold"
                          : "bg-bg-2 text-ink-2 border border-border"
                      }`}
                    >
                      {isPassed ? "✓" : idx + 1}
                    </div>
                    <span
                      className={`font-medium transition-colors ${
                        isPassed
                          ? "text-ink-0"
                          : isCurrent
                          ? "text-accent font-semibold"
                          : "text-ink-2"
                      }`}
                    >
                      {s}
                    </span>
                  </div>
                );
              })}
            </div>

            {jobId && (
              <div className="pt-2 border-t border-border flex items-center justify-between text-[11px] font-mono text-ink-2">
                <span>Job ID: {jobId}</span>
                <span>Auto-refreshing on completion…</span>
              </div>
            )}
          </Card>
        ) : (
          <Card padding="lg" className="space-y-4">
            <div className="space-y-1">
              <h3 className="text-sm font-semibold text-ink-0">
                1-Click Python Ingestion Pipeline
              </h3>
              <p className="text-xs text-ink-1 leading-relaxed">
                Will extract multi-year financials from SEC EDGAR (or Yahoo Finance for TSX), compute 3NF ratios (Altman Z, Beneish M-Score, ROIC, CAGRs), calibrate peer percentiles, and generate the full 7-tab institutional dossier.
              </p>
            </div>

            {errorMsg && (
              <div className="rounded-card border border-neg/40 bg-neg/10 p-3 text-xs text-neg font-mono">
                {errorMsg}
              </div>
            )}

            <div className="flex items-center gap-3 pt-2">
              <button
                onClick={handleFetch}
                className="inline-flex items-center gap-2 rounded-card border border-accent/60 bg-accent px-4 py-2 text-xs font-semibold text-bg-0 hover:bg-accent/90 transition-colors shadow-sm"
              >
                <span>⚡</span>
                <span>Fetch & Enrich {ticker}</span>
              </button>
              <Link
                to="/"
                className="rounded-card border border-border bg-bg-2 px-3 py-2 text-xs font-medium text-ink-1 hover:text-ink-0 transition-colors"
              >
                Return to Desk
              </Link>
            </div>
          </Card>
        )}

        <div className="flex gap-4 text-xs font-mono pt-2">
          <Link to="/screen" className="text-accent hover:underline">Go to screener →</Link>
          <Link to="/sectors" className="text-accent hover:underline">Browse sectors →</Link>
          <Link to="/" className="text-accent hover:underline">Back to desk →</Link>
        </div>
      </div>
    </Page>
  );
}
