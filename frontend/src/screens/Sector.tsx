import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { api, ApiError, enc } from "../api/client";
import type { CurrencyView, SectorRankingsOut, SectorSnapshotOut } from "../api/types";
import { CompanyLink, ErrorBanner, Score, SignalBadge, Spinner } from "../components/ui";
import { SIGNAL_ORDER, signalTone } from "../api/visuals";
import { signalLabel } from "../api/copy";
import { toggleCompareId } from "../lib/compare";
import { composeAll } from "../lib/allCurrency";
import { sectorBlurb } from "../api/sectorCopy";
import InfoTip from "../components/InfoTip";
import NarrationPanel from "../components/NarrationPanel";
import { Card, Page, StatTile } from "../components/layout";

const VIEWS: CurrencyView[] = ["ALL", "USD", "CAD"];

export default function Sector() {
  const { sheet = "" } = useParams();
  const [params, setParams] = useSearchParams();
  const view = (["ALL", "USD", "CAD"].includes(params.get("currency") ?? "") ? params.get("currency") : "ALL") as CurrencyView;
  const nav = useNavigate();
  const [snapshot, setSnapshot] = useState<SectorSnapshotOut | null>(null);
  const [composed, setComposed] = useState<ReturnType<typeof composeAll> | null>(null);
  const [rankings, setRankings] = useState<SectorRankingsOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<string[]>([]);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    type Snap = SectorSnapshotOut;
    const work: Promise<SectorRankingsOut | Snap>[] = [api.sectorRankings(sheet, view, 500)];
    if (view === "ALL") {
      work.push(api.sectorSnapshot(sheet, "USD"), api.sectorSnapshot(sheet, "CAD"));
    } else {
      work.push(api.sectorSnapshot(sheet, view));
    }
    Promise.allSettled(work).then((settled) => {
      const rank = settled[0] as PromiseSettledResult<SectorRankingsOut>;
      const a = settled[1] as PromiseSettledResult<Snap> | undefined;
      const b = settled[2] as PromiseSettledResult<Snap> | undefined;
      if (rank.status === "fulfilled") setRankings(rank.value);
      else setError((rank.reason as ApiError).message);
      if (view === "ALL") {
        const ua = a && a.status === "fulfilled" ? a.value : null;
        const ca = b && b.status === "fulfilled" ? b.value : null;
        setComposed(composeAll(ua, ca));
        setSnapshot(ua || ca); // fallback snapshot if needed
      } else {
        setSnapshot(a && a.status === "fulfilled" ? a.value : null);
        setComposed(null);
      }
      setLoading(false);
    });
  }, [sheet, view]);

  useEffect(() => {
    setSelected([]);
    load();
  }, [load]);

  const toggle = (cid: string) => setSelected((cur) => toggleCompareId(cur, cid));

  const goCompare = () => {
    if (selected.length >= 2) nav(`/compare?ids=${selected.map(enc).join(",")}`);
  };

  const breadcrumb = (
    <div className="flex items-center text-xs text-ink-2 no-print" aria-label="Breadcrumb">
      <Link to="/" className="hover:text-accent">Desk</Link>
      <span className="mx-1.5">/</span>
      <Link to="/sectors" className="hover:text-accent">Sectors</Link>
      <span className="mx-1.5">/</span>
      <span className="font-mono text-ink-0">{sheet}</span>
    </div>
  );

  const headerActions = (
    <div className="flex flex-wrap items-center gap-4">
      <div className="flex items-center gap-2" role="group" aria-label="Currency view (required)">
        <span className="font-mono text-[10px] uppercase tracking-widest text-ink-2">View</span>
        <div className="flex rounded-chip border border-border bg-bg-0 p-0.5">
          {VIEWS.map((v) => (
            <button
              key={v}
              onClick={() => setParams({ currency: v })}
              aria-pressed={view === v}
              className={`rounded-chip px-3 py-1 font-mono text-xs transition-colors ${
                view === v ? "bg-bg-1 text-accent font-medium shadow-sm" : "text-ink-1 hover:text-ink-0"
              }`}
            >
              {v}
            </button>
          ))}
        </div>
      </div>
      <Link
        to={`/screen?${sheet.startsWith("GICS_") ? `sector=${enc(sheet.replace(/^GICS_/, "").replace(/_/g, " "))}` : `industry=${enc(sheet)}`}`}
        className="text-xs text-accent hover:underline flex items-center gap-1 font-medium font-mono"
      >
        Screen this sector →
      </Link>
    </div>
  );

  return (
    <Page
      breadcrumb={breadcrumb}
      title={sheet.replace(/^GICS_/, "").replace(/_/g, " ")}
      description={sectorBlurb(sheet)}
      actions={headerActions}
    >
      {view === "ALL" && (
        <p className="text-xs text-ink-2 font-mono">
          scores + ratios only (per-row currency) - money panels below stay split
        </p>
      )}

      {loading && <Spinner label="Loading sector…" />}
      {error && <ErrorBanner message={error} onRetry={load} />}

      {view === "ALL" && composed && !loading && (
        <section aria-label="All-currency stats" className="space-y-4">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <StatTile label="Companies" value={composed.companies} />
            <StatTile label="Scored" value={composed.scored} />
            <StatTile label="Median score (both)" value={composed.median_composite?.toFixed(1) ?? "0.00"} />
            <StatTile label="USD / CAD names" value={`${composed.money_by_currency.USD?.companies ?? 0} / ${composed.money_by_currency.CAD?.companies ?? 0}`} />
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <MoneyPanel label="USD money medians" panel={composed.money_by_currency.USD} />
            <MoneyPanel label="CAD money medians" panel={composed.money_by_currency.CAD} />
          </div>

          <Card title="Signal Distribution" subtitle="All scored companies across both currencies" padding="md">
            <SignalHistogram histogram={composed.signal_histogram} total={composed.scored} />
          </Card>
        </section>
      )}

      {view !== "ALL" && snapshot && !loading && (
        <section aria-label="Sector snapshot" className="space-y-4">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <StatTile label="Companies" value={snapshot.companies} />
            <StatTile label="Scored" value={snapshot.scored} />
            <StatTile label={`Median score (${view})`} value={snapshot.median_composite?.toFixed(1) ?? "0.00"} />
            <StatTile label={`Median PE (${view})`} value={snapshot.median_pe?.toFixed(1) ?? "0.00"} />
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <MoneyPanel label={`${view} money medians`} panel={snapshot} />
            <Card title="Signal Distribution" subtitle={`Scored ${view} companies in this sector`} padding="md">
              <SignalHistogram histogram={snapshot.signal_histogram} total={snapshot.scored} />
            </Card>
          </div>
        </section>
      )}

      {rankings && !loading && (
        <section aria-label="Ranked companies" className="space-y-3">
          <div className="flex items-center justify-between gap-4">
            <h2 className="font-heading text-lg font-semibold text-ink-0">
              Ranked companies
              {view === "ALL" && <span className="ml-2 font-mono text-xs text-ink-2 font-normal">(score-only, both currencies)</span>}
            </h2>
            <button
              onClick={goCompare}
              disabled={selected.length < 2}
              className={`rounded-card border px-3.5 py-1.5 font-mono text-xs transition-colors ${
                selected.length >= 2
                  ? "border-accent/60 bg-accent-weak text-accent hover:bg-accent/20"
                  : "border-border text-ink-2 cursor-not-allowed opacity-50"
              }`}
            >
              Compare selected ({selected.length})
            </button>
          </div>
          <Card padding="none" className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border bg-bg-2/70 text-left font-mono text-[10px] uppercase tracking-widest text-ink-2">
                    <th scope="col" className="px-3 py-2 w-8"></th>
                    <th scope="col" className="px-3 py-2 w-12 text-right">#</th>
                    <th scope="col" className="px-3 py-2">Company</th>
                    <th scope="col" className="px-3 py-2 whitespace-nowrap">
                      <span>Cur</span>
                      <InfoTip term="Cur" />
                    </th>
                    <th scope="col" className="px-3 py-2 text-right whitespace-nowrap">
                      <span>Score</span>
                      <InfoTip term="Composite" />
                    </th>
                    <th scope="col" className="px-3 py-2 whitespace-nowrap">
                      <span>Signal</span>
                      <InfoTip term="Signal" />
                    </th>
                    <th scope="col" className="px-3 py-2 text-right whitespace-nowrap">
                      <span>PE</span>
                      <InfoTip term="PE" />
                    </th>
                    <th scope="col" className="px-3 py-2 text-right whitespace-nowrap">
                      <span>PB</span>
                      <InfoTip term="PB" />
                    </th>
                    <th scope="col" className="px-3 py-2 text-right whitespace-nowrap">
                      <span>ROE</span>
                      <InfoTip term="ROE" />
                    </th>
                    <th scope="col" className="px-3 py-2 text-right whitespace-nowrap">
                      <span>Peer rank</span>
                      <InfoTip term="Peer rank" />
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {rankings.items.map((r) => (
                    <tr key={r.company_id} className="hover:bg-bg-2/50 transition-colors">
                      <td className="px-3 py-2">
                        <input
                          type="checkbox"
                          checked={selected.includes(r.company_id)}
                          onChange={() => toggle(r.company_id)}
                          aria-label={`Select ${r.name ?? r.company_id} for comparison`}
                          className="h-3.5 w-3.5 rounded-chip border-border bg-bg-0 accent-accent"
                        />
                      </td>
                      <td className="px-3 py-2 text-right font-mono tabular-nums text-ink-2">{r.rank}</td>
                      <td className="px-3 py-2">
                        <CompanyLink companyId={r.company_id}>{r.name ?? r.company_id}</CompanyLink>
                      </td>
                      <td className="px-3 py-2 font-mono text-xs text-info">{r.currency ?? "Not reported in filing"}</td>
                      <td className="px-3 py-2 text-right font-mono tabular-nums"><Score value={r.composite} /></td>
                      <td className="px-3 py-2"><SignalBadge signal={r.signal} small /></td>
                      <td className="px-3 py-2 text-right font-mono tabular-nums text-ink-1">{r.pe_calc?.toFixed(1) ?? "0.00"}</td>
                      <td className="px-3 py-2 text-right font-mono tabular-nums text-ink-1">{r.pb_calc?.toFixed(1) ?? "0.00"}</td>
                      <td className="px-3 py-2 text-right font-mono tabular-nums text-ink-1">
                        {r.roe_calc != null ? `${(r.roe_calc * 100).toFixed(1)}%` : "0.00"}
                      </td>
                      <td className="px-3 py-2 text-right font-mono tabular-nums text-ink-1">{r.peer_rank ?? "Not reported in filing"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
          {view === "ALL" && (
            <p className="text-xs text-ink-2">
              Ratios are unitless and comparable across currencies; every company's PE/PB/ROE comes from its own
              currency snapshot. Revenue/market-cap money columns are intentionally omitted here - see the split
              money panels above.
            </p>
          )}
        </section>
      )}

      <NarrationPanel
        endpoint={`/api/v1/sectors/${enc(sheet)}/narrate?currency=${view}`}
        label="What this sector looks like"
      />
    </Page>
  );
}

function MoneyPanel({ label, panel }: { label: string; panel: { median_pe: number | null; median_pb: number | null; median_roe: number | null; companies: number } | null }) {
  return (
    <Card title={label} padding="md">
      {panel == null || panel.companies === 0 ? (
        <p className="text-xs text-ink-2">No companies.</p>
      ) : (
        <div className="grid grid-cols-3 gap-2 font-mono text-xs tabular-nums">
          <div className="p-2 rounded-card bg-bg-2/50 border border-border text-center">
            <span className="block text-[10px] uppercase text-ink-2">Median PE</span>
            <span className="font-semibold text-ink-0 text-sm">{panel.median_pe?.toFixed(1) ?? "0.00"}</span>
          </div>
          <div className="p-2 rounded-card bg-bg-2/50 border border-border text-center">
            <span className="block text-[10px] uppercase text-ink-2">Median PB</span>
            <span className="font-semibold text-ink-0 text-sm">{panel.median_pb?.toFixed(1) ?? "0.00"}</span>
          </div>
          <div className="p-2 rounded-card bg-bg-2/50 border border-border text-center">
            <span className="block text-[10px] uppercase text-ink-2">Median ROE</span>
            <span className="font-semibold text-ink-0 text-sm">{panel.median_roe != null ? `${(panel.median_roe * 100).toFixed(1)}%` : "0.00"}</span>
          </div>
        </div>
      )}
    </Card>
  );
}

function SignalHistogram({ histogram, total }: { histogram: Record<string, number>; total: number }) {
  return (
    <div className="space-y-2">
      <ul className="space-y-1.5 text-xs">
        {SIGNAL_ORDER.map((sig) => {
          const n = histogram[sig] ?? 0;
          if (!n) return null;
          const tone = signalTone(sig === "score_missing" ? null : sig);
          const color = tone === "good" ? "bg-pos" : tone === "mid" ? "bg-warn" : tone === "bad" ? "bg-neg" : "bg-info";
          return (
            <li key={sig} className="flex items-center gap-3">
              <span className="w-36 shrink-0 text-ink-1 font-medium">{signalLabel(sig === "score_missing" ? null : sig)}</span>
              <div className="flex-1 max-w-xs h-3 bg-bg-2 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${color} transition-all duration-300`}
                  style={{ width: `${Math.max(4, (n / (total || 1)) * 100)}%` }}
                />
              </div>
              <span className="font-mono tabular-nums text-ink-0 font-semibold text-xs">{n}</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}