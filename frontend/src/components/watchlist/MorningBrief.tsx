import React, { useEffect, useState } from "react";
import { api, ApiError } from "../../api/client";
import type {
  WatchlistDigestAlert,
  WatchlistDigestResponse,
  WatchlistDeltaItem,
  WatchlistDeltasResponse,
} from "../../api/types";
import { getWatchlist } from "../../lib/watchlist";
import { CompanyLink, ErrorBanner, Score, SignalBadge, Spinner } from "../ui";
import { Card, Chip } from "../layout";

interface MorningBriefProps {
  companyIds?: string[];
  className?: string;
}

export const MorningBrief: React.FC<MorningBriefProps> = ({
  companyIds,
  className = "",
}) => {
  const [activeTab, setActiveTab] = useState<"digest" | "deltas">("digest");
  const [digest, setDigest] = useState<WatchlistDigestResponse | null>(null);
  const [deltas, setDeltas] = useState<WatchlistDeltasResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const watched = companyIds ?? getWatchlist();

  const loadData = () => {
    setLoading(true);
    setError(null);
    Promise.all([
      api.watchlistDigest(watched.length ? watched : undefined),
      api.watchlistDeltas(watched.length ? watched : undefined),
    ])
      .then(([dig, del]) => {
        setDigest(dig);
        setDeltas(del);
      })
      .catch((err: ApiError) => {
        setError(err.message || "Failed to load morning brief.");
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, [watched.length]);

  const severityTone = (sev: string): "negative" | "warning" | "info" => {
    if (sev === "high") return "negative";
    if (sev === "medium") return "warning";
    return "info";
  };

  return (
    <div className={`space-y-4 ${className}`} aria-label="Watchlist Morning Brief">
      {/* 1-Page Morning Brief Header Card (US-0084) */}
      <Card padding="md" className="border-border bg-bg-1">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl">🌅</span>
              <h2 className="font-heading text-lg font-bold text-ink-0">
                Morning Brief & Watchlist 'What Changed' Digest
              </h2>
            </div>
            <p className="text-xs text-ink-2 mt-0.5">
              Overnight fundamental deltas, signal re-ratings, post-earnings comparisons, and SEDAR+/EDGAR filings.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <div className="flex rounded-chip border border-border p-0.5 bg-bg-0 text-xs">
              <button
                type="button"
                onClick={() => setActiveTab("digest")}
                className={`rounded-chip px-3 py-1 font-mono transition-colors ${
                  activeTab === "digest"
                    ? "bg-bg-1 text-accent font-medium"
                    : "text-ink-1 hover:text-ink-0"
                }`}
              >
                Alerts & Filings ({digest?.alerts?.length ?? 0})
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("deltas")}
                className={`rounded-chip px-3 py-1 font-mono transition-colors ${
                  activeTab === "deltas"
                    ? "bg-bg-1 text-accent font-medium"
                    : "text-ink-1 hover:text-ink-0"
                }`}
              >
                Score Deltas ({deltas?.count ?? 0})
              </button>
            </div>

            <button
              type="button"
              onClick={loadData}
              className="rounded-card border border-border bg-bg-0 px-2.5 py-1 text-xs font-mono text-ink-1 hover:text-ink-0 hover:border-accent transition-colors"
              title="Refresh digest"
            >
              🔄 Refresh
            </button>
          </div>
        </div>

        {/* Overview Stats Strip (US-0084) */}
        {digest && (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 pt-3 text-xs">
            <div className="rounded-card border border-border/70 bg-bg-0 p-2.5">
              <span className="block font-mono text-[10px] uppercase text-ink-2">Watched Names</span>
              <span className="font-mono text-base font-bold text-ink-0 mt-0.5 block">
                {digest.stats.total_watched}
              </span>
              <span className="font-mono text-[10px] text-ink-2">
                {digest.cad_companies_count} CAD · {digest.usd_companies_count} USD
              </span>
            </div>

            <div className="rounded-card border border-border/70 bg-bg-0 p-2.5">
              <span className="block font-mono text-[10px] uppercase text-ink-2">High Severity</span>
              <span className={`font-mono text-base font-bold mt-0.5 block ${
                digest.stats.high_severity_count > 0 ? "text-neg" : "text-ink-0"
              }`}>
                {digest.stats.high_severity_count}
              </span>
              <span className="font-mono text-[10px] text-ink-2">Requires review</span>
            </div>

            <div className="rounded-card border border-border/70 bg-bg-0 p-2.5">
              <span className="block font-mono text-[10px] uppercase text-ink-2">Medium Severity</span>
              <span className="font-mono text-base font-bold text-warning mt-0.5 block">
                {digest.stats.medium_severity_count}
              </span>
              <span className="font-mono text-[10px] text-ink-2">Informational</span>
            </div>

            <div className="rounded-card border border-border/70 bg-bg-0 p-2.5">
              <span className="block font-mono text-[10px] uppercase text-ink-2">Signal Re-Ratings</span>
              <span className="font-mono text-base font-bold text-accent mt-0.5 block">
                {digest.stats.rerated_count}
              </span>
              <span className="font-mono text-[10px] text-ink-2">Signal shifts</span>
            </div>

            <div className="rounded-card border border-border/70 bg-bg-0 p-2.5">
              <span className="block font-mono text-[10px] uppercase text-ink-2">Post-Earnings</span>
              <span className="font-mono text-base font-bold text-pos mt-0.5 block">
                {digest.stats.earnings_count}
              </span>
              <span className="font-mono text-[10px] text-ink-2">Recent actuals</span>
            </div>

            <div className="rounded-card border border-border/70 bg-bg-0 p-2.5">
              <span className="block font-mono text-[10px] uppercase text-ink-2">Session</span>
              <span className="font-mono text-sm font-semibold text-ink-0 mt-1 block">
                {digest.market_session}
              </span>
              <span className="font-mono text-[10px] text-ink-2 truncate block">
                {digest.brief_date}
              </span>
            </div>
          </div>
        )}

        {/* Currency Isolation Banner (Contractual Guarantee) */}
        {digest && (
          <div className="mt-3 flex items-center justify-between rounded bg-bg-0 border border-border/60 px-3 py-1.5 text-[11px] font-mono text-ink-2">
            <span>🔒 {digest.currency_segregation_note}</span>
            <span className="text-[10px] text-ink-2 truncate max-w-xs">{digest.disclaimer}</span>
          </div>
        )}
      </Card>

      {/* Loading & Error States */}
      {loading && <Spinner label="Analyzing morning deltas & filings…" />}
      {error && <ErrorBanner message={error} onRetry={loadData} />}

      {/* TAB 1: Alert Feed & Regulatory Filings (US-0084, US-0351, US-0377) */}
      {activeTab === "digest" && digest && !loading && (
        <Card padding="none" className="overflow-hidden border-border bg-bg-1">
          <div className="px-4 py-3 border-b border-border bg-bg-0 flex items-center justify-between">
            <h3 className="font-heading font-semibold text-sm text-ink-0">
              Active Watchlist Alerts & Regulatory Filings ({digest.alerts.length})
            </h3>
            <span className="font-mono text-[11px] text-ink-2">
              Routing: High (Email+App) · Medium (In-App) · Low (Feed)
            </span>
          </div>

          {digest.alerts.length === 0 ? (
            <div className="p-8 text-center text-xs text-ink-2">
              <p>No critical overnight alerts for watched names.</p>
              <p className="mt-1 font-mono text-[11px]">All monitored tickers trade within normal fundamental parameters.</p>
            </div>
          ) : (
            <ul className="divide-y divide-border text-xs">
              {digest.alerts.map((al: WatchlistDigestAlert) => (
                <li key={al.id} className="p-4 hover:bg-bg-0/60 transition-colors">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Chip tone={severityTone(al.severity)} size="sm">
                          {al.severity.toUpperCase()}
                        </Chip>
                        <CompanyLink companyId={al.company_id} className="font-medium text-ink-0 font-mono">
                          {al.ticker} ({al.name})
                        </CompanyLink>
                        <span className="font-mono text-[10px] text-ink-2">
                          {al.alert_type.replace(/_/g, " ").toUpperCase()}
                        </span>
                      </div>
                      <h4 className="font-medium text-ink-0">{al.title}</h4>
                      <p className="text-xs text-ink-1 leading-relaxed">{al.detail}</p>
                    </div>

                    {/* Routing Badge & Regulatory Direct Filings Links (US-0351, US-0377) */}
                    <div className="flex flex-col items-end gap-1.5 shrink-0">
                      <div className="flex items-center gap-1 font-mono text-[10px] text-ink-2 bg-bg-0 px-2 py-0.5 rounded border border-border">
                        <span>Route:</span>
                        <span className="text-ink-0 font-medium">{al.routing.primary_channel}</span>
                        <span>({al.routing.urgency})</span>
                      </div>

                      <div className="flex items-center gap-2 mt-1">
                        {al.sedar_url && (
                          <a
                            href={al.sedar_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-mono text-[11px] text-accent hover:underline flex items-center gap-1"
                            title="SEDAR+ Canadian Regulatory Filings"
                          >
                            <span>🇨🇦 SEDAR+</span> ↗
                          </a>
                        )}
                        {al.edgar_url && (
                          <a
                            href={al.edgar_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-mono text-[11px] text-info hover:underline flex items-center gap-1"
                            title="SEC EDGAR US Regulatory Filings"
                          >
                            <span>🇺🇸 SEC EDGAR</span> ↗
                          </a>
                        )}
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}

      {/* TAB 2: Historical Score Deltas & Post-Earnings Actuals (US-0092, US-0367) */}
      {activeTab === "deltas" && deltas && !loading && (
        <Card padding="none" className="overflow-hidden border-border bg-bg-1">
          <div className="px-4 py-3 border-b border-border bg-bg-0 flex items-center justify-between">
            <h3 className="font-heading font-semibold text-sm text-ink-0">
              Pillar Score Changes & Signal Re-ratings ({deltas.count})
            </h3>
            <span className="font-mono text-[11px] text-ink-2">
              Locked weights: Quality 30% · Value 25% · Growth 25% · Risk 20%
            </span>
          </div>

          {deltas.deltas.length === 0 ? (
            <div className="p-8 text-center text-xs text-ink-2">
              <p>No historical scores available for comparison yet.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border bg-bg-0 text-left font-mono text-[10px] uppercase tracking-wider text-ink-2">
                    <th scope="col" className="px-3 py-2.5">Company</th>
                    <th scope="col" className="px-2 py-2.5">Ccy</th>
                    <th scope="col" className="px-3 py-2.5 text-right">Composite</th>
                    <th scope="col" className="px-3 py-2.5 text-right">Δ Score</th>
                    <th scope="col" className="px-3 py-2.5">Signal Status</th>
                    <th scope="col" className="px-3 py-2.5 text-right">Quality Δ</th>
                    <th scope="col" className="px-3 py-2.5 text-right">Value Δ</th>
                    <th scope="col" className="px-3 py-2.5 text-right">Risk Δ</th>
                    <th scope="col" className="px-3 py-2.5">Post-Earnings Actuals</th>
                    <th scope="col" className="px-3 py-2.5">Filings</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {deltas.deltas.map((d: WatchlistDeltaItem) => {
                    const deltaComp = d.delta_composite;
                    const isPositive = deltaComp !== null && deltaComp > 0;
                    const isNegative = deltaComp !== null && deltaComp < 0;

                    return (
                      <tr key={d.company_id} className="hover:bg-bg-0/50 transition-colors">
                        <td className="px-3 py-2 font-medium">
                          <CompanyLink companyId={d.company_id}>{d.name || d.company_id}</CompanyLink>
                          <span className="ml-2 font-mono text-[10px] text-ink-2">{d.ticker}</span>
                        </td>
                        <td className="px-2 py-2">
                          <Chip tone={d.currency === "USD" ? "info" : "warning"} size="sm">
                            {d.currency}
                          </Chip>
                        </td>
                        <td className="px-3 py-2 text-right font-mono">
                          <Score value={d.current_composite} />
                        </td>
                        <td className="px-3 py-2 text-right font-mono tabular-nums">
                          {deltaComp !== null ? (
                            <span className={`font-semibold ${isPositive ? "text-pos" : isNegative ? "text-neg" : "text-ink-2"}`}>
                              {isPositive ? "+" : ""}{deltaComp.toFixed(2)}
                            </span>
                          ) : (
                            "Not reported in filing"
                          )}
                        </td>
                        <td className="px-3 py-2">
                          <div className="flex items-center gap-1.5">
                            <SignalBadge signal={d.current_signal} small />
                            {d.is_rerated && (
                              <span className="font-mono text-[9px] bg-accent/20 text-accent border border-accent/40 rounded px-1 py-0.2 font-bold uppercase">
                                Re-Rated
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="px-3 py-2 text-right font-mono tabular-nums text-ink-1">
                          {d.pillar_deltas.quality !== undefined && d.pillar_deltas.quality !== null ? (
                            <span>{d.pillar_deltas.quality >= 0 ? "+" : ""}{d.pillar_deltas.quality.toFixed(1)}</span>
                          ) : (
                            "Not reported in filing"
                          )}
                        </td>
                        <td className="px-3 py-2 text-right font-mono tabular-nums text-ink-1">
                          {d.pillar_deltas.value !== undefined && d.pillar_deltas.value !== null ? (
                            <span>{d.pillar_deltas.value >= 0 ? "+" : ""}{d.pillar_deltas.value.toFixed(1)}</span>
                          ) : (
                            "Not reported in filing"
                          )}
                        </td>
                        <td className="px-3 py-2 text-right font-mono tabular-nums text-ink-1">
                          {d.pillar_deltas.risk !== undefined && d.pillar_deltas.risk !== null ? (
                            <span>{d.pillar_deltas.risk >= 0 ? "+" : ""}{d.pillar_deltas.risk.toFixed(1)}</span>
                          ) : (
                            "Not reported in filing"
                          )}
                        </td>
                        <td className="px-3 py-2">
                          {d.earnings_post_actual ? (
                            <div className="font-mono text-[10px] space-y-0.5">
                              <span className="text-ink-0 font-medium">
                                FY{d.earnings_post_actual.fiscal_year}: Rev Growth{" "}
                                {(() => {
                                  const raw = d.earnings_post_actual.revenue_growth_pct;
                                  if (raw == null) return <span className="text-ink-2">-</span>;
                                  const pct = Math.abs(raw) <= 1.0 && raw !== 0 ? raw * 100 : raw;
                                  const isPos = pct >= 0;
                                  return (
                                    <span className={isPos ? "text-pos" : "text-neg"}>
                                      {isPos ? "+" : ""}{pct.toFixed(1)}%
                                    </span>
                                  );
                                })()}
                              </span>
                            </div>
                          ) : (
                            <span className="font-mono text-[10px] text-ink-2">Annual filing pending</span>
                          )}
                        </td>
                        <td className="px-3 py-2">
                          <div className="flex items-center gap-1.5 font-mono text-[10px]">
                            {d.filing_links.sedar_plus && (
                              <a
                                href={d.filing_links.sedar_plus}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-accent hover:underline"
                                title="SEDAR+ Regulatory Disclosures"
                              >
                                🇨🇦 SEDAR+ ↗
                              </a>
                            )}
                            {d.filing_links.edgar && (
                              <a
                                href={d.filing_links.edgar}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-info hover:underline"
                                title="SEC EDGAR Regulatory Disclosures"
                              >
                                🇺🇸 EDGAR ↗
                              </a>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}
    </div>
  );
};

export default MorningBrief;