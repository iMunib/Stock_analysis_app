import { useEffect, useState } from "react";
import { getWatchlist, toggleWatch } from "../lib/watchlist";
import { api } from "../api/client";
import type { ScreenItem } from "../api/types";
import { CompanyLink, Score, SignalBadge, Spinner } from "../components/ui";
import { Card, Page, Chip } from "../components/layout";
import { EmptyState } from "../components/feedback";
import MorningBrief from "../components/watchlist/MorningBrief";
import RevenueSparkline from "../components/screener/RevenueSparkline";
import BookChecklists from "../components/screener/BookChecklists";

export default function Watchlist() {
  const [watchIds, setWatchIds] = useState<string[]>([]);
  const [companies, setCompanies] = useState<ScreenItem[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const list = getWatchlist();
    setWatchIds(list);
  }, []);

  useEffect(() => {
    if (watchIds.length === 0) {
      setCompanies([]);
      return;
    }
    setLoading(true);
    // Screen to fetch rich data for watched names
    api
      .screen({ limit: 1000 })
      .then((res) => {
        const matched = res.items.filter((it) => watchIds.includes(it.company_id));
        setCompanies(matched);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [watchIds]);

  const handleRemove = (id: string) => {
    const updated = toggleWatch(id);
    setWatchIds(updated);
  };

  return (
    <Page
      title="Watchlist & Morning Brief"
      description="1-page fundamental brief, historical deltas, re-ratings, post-earnings actuals, and direct SEDAR+/EDGAR links."
    >
      {/* Morning Brief Component (Epic 5: US-0084, US-0092, US-0351, US-0367, US-0377) */}
      <MorningBrief companyIds={watchIds} />

      {/* Watched Companies Table */}
      <Card padding="md" className="space-y-4">
        <div className="flex items-center justify-between border-b border-border pb-3">
          <div>
            <h3 className="font-heading font-semibold text-sm text-ink-0">
              Monitored Universe ({watchIds.length} companies)
            </h3>
            <p className="text-xs text-ink-2 mt-0.5">
              Strict currency segregation: Canadian (CAD) names route to SEDAR+, US (USD) names route to SEC EDGAR.
            </p>
          </div>
        </div>

        {loading ? (
          <div className="py-6 flex justify-center">
            <Spinner label="Loading watchlist details…" />
          </div>
        ) : watchIds.length === 0 ? (
          <EmptyState
            title="Your Watchlist is Empty"
            body="Add companies from the Screener, Desk rankings, or individual company Dossiers using the Star/Watch button."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border bg-bg-0 text-left font-mono text-[10px] uppercase tracking-wider text-ink-2">
                  <th scope="col" className="px-3 py-2.5">Ticker / Company</th>
                  <th scope="col" className="px-2 py-2.5">Ccy</th>
                  <th scope="col" className="px-3 py-2.5">Sector</th>
                  <th scope="col" className="px-3 py-2.5 text-right">Composite</th>
                  <th scope="col" className="px-3 py-2.5">Signal</th>
                  <th scope="col" className="px-3 py-2.5 text-right">P/E</th>
                  <th scope="col" className="px-3 py-2.5 text-right">FCF Margin</th>
                  <th scope="col" className="px-3 py-2.5 text-center">5Y Rev Trajectory</th>
                  <th scope="col" className="px-3 py-2.5 text-center">Checklists</th>
                  <th scope="col" className="px-3 py-2.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {companies.map((c) => (
                  <tr key={c.company_id} className="hover:bg-bg-0/50 transition-colors">
                    <td className="px-3 py-2.5 font-medium">
                      <CompanyLink companyId={c.company_id}>{c.name || c.company_id}</CompanyLink>
                      <span className="ml-2 font-mono text-[10px] text-ink-2">{c.ticker}</span>
                    </td>
                    <td className="px-2 py-2.5">
                      <Chip tone={c.currency === "USD" ? "info" : "warning"} size="sm">
                        {c.currency}
                      </Chip>
                    </td>
                    <td className="px-3 py-2.5 text-ink-1 truncate max-w-[140px]">
                      {c.gics_sector || "Not reported in filing"}
                    </td>
                    <td className="px-3 py-2.5 text-right font-mono">
                      <Score value={c.composite} />
                    </td>
                    <td className="px-3 py-2.5">
                      <SignalBadge signal={c.signal} small />
                    </td>
                    <td className="px-3 py-2.5 text-right font-mono tabular-nums text-ink-1">
                      {c.pe_calc !== null && c.pe_calc !== undefined ? c.pe_calc.toFixed(1) : "0.00"}
                    </td>
                    <td className="px-3 py-2.5 text-right font-mono tabular-nums text-ink-1">
                      {c.fcfmargin_calc !== null && c.fcfmargin_calc !== undefined
                        ? `${(c.fcfmargin_calc * 100).toFixed(1)}%`
                        : "Not reported in filing"}
                    </td>
                    <td className="px-3 py-2.5 text-center">
                      <RevenueSparkline values={c.revenue_sparkline} />
                    </td>
                    <td className="px-3 py-2.5 text-center">
                      <BookChecklists checklists={c.checklists} />
                    </td>
                    <td className="px-3 py-2.5 text-right">
                      <button
                        type="button"
                        onClick={() => handleRemove(c.company_id)}
                        className="font-mono text-[11px] text-neg hover:underline"
                        title="Remove from watchlist"
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </Page>
  );
}