import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, ApiError, enc } from "../api/client";
import type { RankingsOut, ResearchMetaOut } from "../api/types";
import { CompanyLink, ErrorBanner, Score, SignalBadge, Spinner } from "../components/ui";
import { SIGNAL_ORDER, signalTone } from "../api/visuals";
import { signalLabel } from "../api/copy";

const LEGEND =
  "Scores lean low on purpose: most companies (713 of 720) have less than three years of history in the database, so their Growth pillar is not scored and the composite is reduced. Valuation is a strict percentile versus same-currency peers — average companies land mid-pack, not at 8.";

export default function Home() {
  const [meta, setMeta] = useState<ResearchMetaOut | null>(null);
  const [metaError, setMetaError] = useState<string | null>(null);
  const [rankUsd, setRankUsd] = useState<RankingsOut | null>(null);
  const [rankCad, setRankCad] = useState<RankingsOut | null>(null);
  const [ticker, setTicker] = useState("");
  const [ingesting, setIngesting] = useState(false);
  const [ingestMsg, setIngestMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const nav = useNavigate();

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

  const addTicker = useCallback(async () => {
    const t = ticker.trim();
    if (!t) return;
    setIngesting(true);
    setIngestMsg(null);
    try {
      const out = await api.ingest(t);
      await api.recomputeCompany(out.company_id);
      setIngestMsg({ ok: true, text: `${out.company_id} added and scored (${out.year_count} years on file). Opening…` });
      setTimeout(() => nav(`/c/${enc(out.company_id)}`), 900);
    } catch (e) {
      setIngestMsg({ ok: false, text: e instanceof ApiError ? e.message : String(e) });
    } finally {
      setIngesting(false);
    }
  }, [ticker, nav]);

  return (
    <div className="space-y-10">
      <section aria-label="Desk overview" className="space-y-2">
        <h1 className="font-display text-3xl tracking-tight">The desk</h1>
        <p className="max-w-2xl text-sm text-fog">
          A local equity-research desk for the S&amp;P 500 and S&amp;P/TSX Composite. Search a name up top, or
          browse by sector.
        </p>
      </section>

      {metaError && <ErrorBanner message={metaError} onRetry={loadMeta} />}
      {!meta && !metaError && <Spinner label="Reading research status…" />}

      {meta && (
        <section aria-label="Database status" className="space-y-3">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <Stat label="Companies" value={meta.companies} />
            <Stat label="Scored" value={meta.scored} />
            <Stat label="Insufficient data" value={meta.insufficient_data} />
            <Stat label="Growth not scored" value={meta.growth_null} />
          </div>
          {meta.scored === 0 && (
            <div className="rounded-md border border-warn/50 bg-warn/10 px-4 py-3 text-sm text-paper">
              No scores yet — run a recompute (POST /api/v1/scores/recompute) or add a ticker below.
            </div>
          )}
          <div className="rounded-md border border-line bg-panel p-4 text-sm text-fog">
            <span className="font-mono text-xs uppercase tracking-widest text-dim">Needs history · </span>
            {meta.growth_null} of {meta.scored} scored names lack the 3+ years of history needed to compute growth,
            so their composite is reduced. That is the honest state of the data, not a bug.
          </div>
          <div className="space-y-2">
            <p className="font-mono text-xs uppercase tracking-widest text-dim">Signal histogram</p>
            <ul className="space-y-1.5">
              {SIGNAL_ORDER.map((sig) => {
                const n = meta.signal_histogram[sig] ?? 0;
                if (!n) return null;
                const tone = signalTone(sig === "score_missing" ? null : sig);
                const color = tone === "good" ? "bg-good" : tone === "mid" ? "bg-mid" : tone === "bad" ? "bg-bad" : "bg-info";
                return (
                  <li key={sig} className="flex items-center gap-3 text-sm">
                    <span className="w-36 shrink-0 text-fog">{signalLabel(sig === "score_missing" ? null : sig)}</span>
                    <span className="h-3 rounded-sm" style={{ width: `${Math.max(4, (n / meta.companies) * 420)}px` }}>
                      <span className={`block h-3 rounded-sm ${color}`} />
                    </span>
                    <span className="font-mono tabular-nums text-paper">{n}</span>
                  </li>
                );
              })}
            </ul>
          </div>
          <p className="max-w-3xl text-sm leading-relaxed text-fog">{LEGEND}</p>
        </section>
      )}

      <div className="grid gap-8 lg:grid-cols-2">
        <TopTable title="Top 10 — USD" rows={rankUsd?.items ?? []} />
        <TopTable title="Top 10 — CAD" rows={rankCad?.items ?? []} />
      </div>

      <section aria-label="Add a ticker" className="space-y-3 rounded-md border border-line bg-panel p-5">
        <h2 className="font-display text-lg">Add a ticker to the database</h2>
        <p className="text-sm text-fog">
          Pull annual history for any US or Canadian ticker (e.g. <code className="font-mono text-goldsoft">AAPL</code> or{" "}
          <code className="font-mono text-goldsoft">RY.TO</code>), then score it. Free public sources only.
        </p>
        <form
          className="flex gap-3"
          onSubmit={(e) => {
            e.preventDefault();
            addTicker();
          }}
        >
          <input
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            placeholder="AAPL or RY.TO"
            aria-label="Ticker to add"
            className="w-64 rounded-md border border-line bg-ink px-3 py-2 font-mono text-sm placeholder:text-dim"
          />
          <button
            type="submit"
            disabled={ingesting || !ticker.trim()}
            className="rounded-md border border-gold/60 bg-gold/10 px-4 py-2 text-sm font-medium text-gold hover:bg-gold/20 disabled:opacity-40"
          >
            {ingesting ? "Fetching…" : "Add & score"}
          </button>
        </form>
        {ingestMsg && (
          <p role="status" className={ingestMsg.ok ? "text-sm text-good" : "text-sm text-bad"}>
            {ingestMsg.text}
          </p>
        )}
      </section>

      <section aria-label="Browse" className="flex flex-wrap gap-4 text-sm">
        <Link to="/sectors" className="text-gold hover:underline">Browse all sectors →</Link>
      </section>
    </div>
  );
}

function TopTable({ title, rows }: { title: string; rows: RankingsOut["items"] }) {
  return (
    <section aria-label={title} className="space-y-3">
      <h2 className="font-display text-xl">{title}</h2>
      {rows.length === 0 ? (
        <p className="text-sm text-fog">No scored names yet.</p>
      ) : (
        <ul className="divide-y divide-line rounded-md border border-line bg-panel">
          {rows.map((r) => (
            <li key={r.company_id} className="flex items-center justify-between gap-4 px-4 py-2.5">
              <div>
                <CompanyLink companyId={r.company_id}>{r.name ?? r.company_id}</CompanyLink>
                <span className="ml-2 font-mono text-[10px] text-dim">#{r.rank}</span>
              </div>
              <div className="flex items-center gap-3">
                <Score value={r.composite} />
                <SignalBadge signal={r.signal} small />
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-line bg-panel px-4 py-3">
      <p className="font-mono text-[10px] uppercase tracking-widest text-dim">{label}</p>
      <p className="mt-1 font-mono text-2xl tabular-nums text-paper">{value}</p>
    </div>
  );
}
