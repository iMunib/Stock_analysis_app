import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, ApiError, enc } from "../api/client";
import type { ResearchMetaOut, SearchOut } from "../api/types";
import { ErrorBanner, CompanyLink, Score, SignalBadge, Spinner, useDebounced } from "../components/ui";
import { SIGNAL_ORDER, signalTone } from "../api/visuals";
import { signalLabel } from "../api/copy";

const LEGEND =
  "Scores lean low on purpose: most companies (713 of 720) have less than three years of history in the database, so their Growth pillar is not scored and the composite is reduced. The remaining pillars are graded against same-currency peers, and valuation is a strict percentile â€” average companies land mid-pack, not at 8.";

export default function Home() {
  const [meta, setMeta] = useState<ResearchMetaOut | null>(null);
  const [metaError, setMetaError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const debounced = useDebounced(query, 250);
  const [results, setResults] = useState<SearchOut | null>(null);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [ticker, setTicker] = useState("");
  const [ingesting, setIngesting] = useState(false);
  const [ingestMsg, setIngestMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const nav = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api
      .researchMeta()
      .then(setMeta)
      .catch((e: ApiError) => setMetaError(e.message));
  }, []);

  useEffect(() => {
    const q = debounced.trim();
    if (!q) {
      setResults(null);
      setSearchError(null);
      return;
    }
    setSearching(true);
    setSearchError(null);
    api
      .search(q, 20)
      .then(setResults)
      .catch((e: ApiError) => setSearchError(e.message))
      .finally(() => setSearching(false));
  }, [debounced]);

  const addTicker = useCallback(async () => {
    const t = ticker.trim();
    if (!t) return;
    setIngesting(true);
    setIngestMsg(null);
    try {
      const out = await api.ingest(t);
      const cid = out.company_id;
      await api.recomputeCompany(cid);
      setIngestMsg({ ok: true, text: `${cid} added and scored (${out.year_count} years on file). Openingâ€¦` });
      setTimeout(() => nav(`/c/${enc(cid)}`), 900);
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : String(e);
      setIngestMsg({ ok: false, text: msg });
    } finally {
      setIngesting(false);
    }
  }, [ticker, nav]);

  return (
    <div className="space-y-10">
      <section aria-label="Search" className="space-y-4">
        <h1 className="font-display text-3xl tracking-tight">Look up a company</h1>
        <input
          ref={inputRef}
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search name, ticker, or ID â€” e.g. Apple, RY.TO, US:MMM:US"
          aria-label="Search companies by name, ticker, or company ID"
          className="w-full rounded-md border border-line bg-panel px-4 py-3 text-lg placeholder:text-dim focus:border-line2"
        />
        {searching && <Spinner label="Searchingâ€¦" />}
        {searchError && <ErrorBanner message={searchError} onDismiss={() => setSearchError(null)} />}
        {results && !searching && (
          <div className="rounded-md border border-line bg-panel" role="list" aria-label="Search results">
            {results.items.length === 0 ? (
              <p className="px-4 py-3 text-sm text-fog">No matches for â€œ{results.q}â€.</p>
            ) : (
              <ul className="divide-y divide-line">
                {results.items.map((it) => (
                  <li key={it.company_id} className="flex items-center justify-between gap-4 px-4 py-3 hover:bg-panel2">
                    <div>
                      <CompanyLink companyId={it.company_id} className="font-medium">{it.name ?? it.company_id}</CompanyLink>
                      <span className="ml-2 font-mono text-xs text-dim">{it.company_id}</span>
                      {it.currency && <span className="ml-2 font-mono text-xs text-info">{it.currency}</span>}
                    </div>
                    <div className="flex items-center gap-3">
                      <Score value={it.composite} />
                      <SignalBadge signal={it.signal} small />
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </section>

      <section aria-label="Add a ticker" className="space-y-3 rounded-md border border-line bg-panel p-5">
        <h2 className="font-display text-lg">Add a ticker to the database</h2>
        <p className="text-sm text-fog">
          Pull annual history for any US or Canadian ticker (e.g. <code className="font-mono text-goldsoft">AAPL</code> or{" "}
          <code className="font-mono text-goldsoft">RY.TO</code>), then score it. Uses free public sources only.
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
            {ingesting ? "Fetchingâ€¦" : "Add & score"}
          </button>
        </form>
        {ingestMsg && (
          <p role="status" className={ingestMsg.ok ? "text-sm text-good" : "text-sm text-bad"}>
            {ingestMsg.text}
          </p>
        )}
      </section>

      <section aria-label="Research database status" className="space-y-3">
        <h2 className="font-display text-lg">What the database looks like today</h2>
        {metaError && <ErrorBanner message={metaError} />}
        {!meta && !metaError && <Spinner label="Reading research statusâ€¦" />}
        {meta && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <Stat label="Companies" value={meta.companies} />
              <Stat label="Scored" value={meta.scored} />
              <Stat label="Insufficient data" value={meta.insufficient_data} />
              <Stat label="Growth not scored" value={meta.growth_null} />
            </div>
            <div className="space-y-2">
              <p className="font-mono text-xs uppercase tracking-widest text-dim">Signal histogram</p>
              <ul className="space-y-1.5" aria-label="Signal histogram as counts">
                {SIGNAL_ORDER.map((sig) => {
                  const n = meta.signal_histogram[sig] ?? 0;
                  if (!n) return null;
                  const tone = signalTone(sig === "score_missing" ? null : sig);
                  const color =
                    tone === "good" ? "bg-good" : tone === "mid" ? "bg-mid" : tone === "bad" ? "bg-bad" : "bg-info";
                  return (
                    <li key={sig} className="flex items-center gap-3 text-sm">
                      <span className="w-36 shrink-0 text-fog">{signalLabel(sig === "score_missing" ? null : sig)}</span>
                      <span className="h-3 rounded-sm" style={{ width: `${Math.max(4, (n / meta.companies) * 420)}px` }}>
                        <span className={`block h-3 rounded-sm ${color}`} style={{ width: "100%" }} />
                      </span>
                      <span className="font-mono tabular-nums text-paper">{n}</span>
                    </li>
                  );
                })}
              </ul>
            </div>
            <p className="max-w-3xl text-sm leading-relaxed text-fog">{LEGEND}</p>
          </div>
        )}
      </section>

      <section aria-label="Browse" className="flex flex-wrap gap-4 text-sm">
        <Link to="/compare" className="text-gold hover:underline">
          Compare companies â†’
        </Link>
        <Link to="/sectors/Software" className="text-gold hover:underline">
          Software (USD) â†’
        </Link>
        <Link to="/sectors/Banks" className="text-gold hover:underline">
          Banks (CAD) â†’
        </Link>
      </section>
    </div>
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

