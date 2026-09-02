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
        setComposed(ua && ca ? composeAll(ua, ca) : null);
        setSnapshot(ua); // not used for stats in ALL
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

  return (
    <div className="space-y-8 animate-fade-in">
      <nav className="text-xs text-dim" aria-label="Breadcrumb">
        <Link to="/" className="hover:text-gold">Desk</Link>
        <span className="mx-1.5">/</span>
        <Link to="/sectors" className="hover:text-gold">Sectors</Link>
        <span className="mx-1.5">/</span>
        <span className="font-mono">{sheet}</span>
      </nav>

      <header className="space-y-3">
        <h1 className="font-display text-3xl tracking-tight">{sheet.replace(/^GICS_/, "").replace(/_/g, " ")}</h1>
        <p className="max-w-2xl text-sm leading-relaxed text-fog">{sectorBlurb(sheet)}</p>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2" role="group" aria-label="Currency view (required)">
            <span className="font-mono text-[10px] uppercase tracking-widest text-dim">View</span>
            {VIEWS.map((v) => (
              <button
                key={v}
                onClick={() => setParams({ currency: v })}
                aria-pressed={view === v}
                className={`rounded border px-3 py-1 font-mono text-xs transition-colors ${
                  view === v ? "border-gold bg-gold/15 text-gold" : "border-line text-fog hover:border-line2 hover:text-paper"
                }`}
              >
                {v}
              </button>
            ))}
            {view === "ALL" && (
              <span className="ml-2 text-xs text-dim">
                scores + ratios only (per-row currency) — money panels below stay split
              </span>
            )}
          </div>
          <Link
            to={`/screen?${sheet.startsWith("GICS_") ? `sector=${enc(sheet.replace(/^GICS_/, "").replace(/_/g, " "))}` : `industry=${enc(sheet)}`}`}
            className="text-xs text-gold hover:underline flex items-center gap-1 font-medium"
          >
            Screen this sector →
          </Link>
        </div>
      </header>

      {loading && <Spinner label="Loading sector…" />}
      {error && <ErrorBanner message={error} onRetry={load} />}

      {view === "ALL" && composed && !loading && (
        <section aria-label="All-currency stats" className="space-y-4">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <Stat label="Companies" value={composed.companies} />
            <Stat label="Scored" value={composed.scored} />
            <Stat label="Median score (both)" value={composed.median_composite?.toFixed(1) ?? "—"} />
            <Stat label="USD / CAD names" value={`${composed.money_by_currency.USD?.companies ?? 0} / ${composed.money_by_currency.CAD?.companies ?? 0}`} />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <MoneyPanel label="USD money medians" panel={composed.money_by_currency.USD} />
            <MoneyPanel label="CAD money medians" panel={composed.money_by_currency.CAD} />
          </div>
          <div className="flex flex-wrap gap-2" aria-label="Constructive vs avoid counts">
            <span className="rounded border border-good/50 px-2 py-0.5 font-mono text-xs text-good">
              Constructive+: {countSignals(composed.signal_histogram, ["strong_candidate", "constructive"])}
            </span>
            <span className="rounded border border-bad/50 px-2 py-0.5 font-mono text-xs text-bad">
              Weak+Avoid: {countSignals(composed.signal_histogram, ["weak", "avoid"])}
            </span>
          </div>
          <SignalHistogram histogram={composed.signal_histogram} total={composed.companies} />
        </section>
      )}

      {view !== "ALL" && snapshot && !loading && (
        <section aria-label="Sector stats" className="space-y-4">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
            <Stat label="Companies" value={snapshot.companies} />
            <Stat label="Scored" value={snapshot.scored} />
            <Stat label="Median PE" value={snapshot.median_pe?.toFixed(1) ?? "—"} />
            <Stat label="Median PB" value={snapshot.median_pb?.toFixed(1) ?? "—"} />
            <Stat label="Median ROE" value={snapshot.median_roe != null ? `${(snapshot.median_roe * 100).toFixed(1)}%` : "—"} />
          </div>
          <SignalHistogram histogram={snapshot.signal_histogram} total={snapshot.companies} />
        </section>
      )}

      {rankings && !loading && (
        <section aria-label="Ranked companies" className="space-y-3">
          <div className="flex items-center justify-between gap-4">
            <h2 className="font-display text-xl">
              Ranked companies
              {view === "ALL" && <span className="ml-2 font-mono text-xs text-dim">(score-only, both currencies)</span>}
            </h2>
            <button
              onClick={goCompare}
              disabled={selected.length < 2}
              className={`rounded-md border px-4 py-2 text-sm transition-colors ${
                selected.length >= 2
                  ? "border-gold/60 bg-gold/10 text-gold hover:bg-gold/20"
                  : "border-line text-dim cursor-not-allowed"
              }`}
            >
              Compare selected ({selected.length})
            </button>
          </div>
          <div className="overflow-x-auto rounded-md border border-line">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line bg-panel text-left font-mono text-[10px] uppercase tracking-widest text-dim">
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
              <tbody className="divide-y divide-line">
                {rankings.items.map((r) => (
                  <tr key={r.company_id} className="hover:bg-panel2/50">
                    <td className="px-3 py-2">
                      <input
                        type="checkbox"
                        checked={selected.includes(r.company_id)}
                        onChange={() => toggle(r.company_id)}
                        aria-label={`Select ${r.name ?? r.company_id} for comparison`}
                        className="h-4 w-4 accent-[#e0a84f]"
                      />
                    </td>
                    <td className="px-3 py-2 text-right font-mono tabular-nums text-dim">{r.rank}</td>
                    <td className="px-3 py-2">
                      <CompanyLink companyId={r.company_id}>{r.name ?? r.company_id}</CompanyLink>
                    </td>
                    <td className="px-3 py-2 font-mono text-xs text-info">{r.currency ?? "—"}</td>
                    <td className="px-3 py-2 text-right font-mono tabular-nums"><Score value={r.composite} /></td>
                    <td className="px-3 py-2"><SignalBadge signal={r.signal} small /></td>
                    <td className="px-3 py-2 text-right font-mono tabular-nums text-fog">{r.pe_calc?.toFixed(1) ?? "—"}</td>
                    <td className="px-3 py-2 text-right font-mono tabular-nums text-fog">{r.pb_calc?.toFixed(1) ?? "—"}</td>
                    <td className="px-3 py-2 text-right font-mono tabular-nums text-fog">
                      {r.roe_calc != null ? `${(r.roe_calc * 100).toFixed(1)}%` : "—"}
                    </td>
                    <td className="px-3 py-2 text-right font-mono tabular-nums text-fog">{r.peer_rank ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {view === "ALL" && (
            <p className="text-xs text-dim">
              Ratios are unitless and comparable across currencies; every company's PE/PB/ROE comes from its own
              currency snapshot. Revenue/market-cap money columns are intentionally omitted here — see the split
              money panels above.
            </p>
          )}
        </section>
      )}

      <NarrationPanel
        endpoint={`/api/v1/sectors/${enc(sheet)}/narrate?currency=${view}`}
        label="What this sector looks like"
      />
    </div>
  );
}

function countSignals(histogram: Record<string, number>, signals: string[]): number {
  return signals.reduce((acc, s) => acc + (histogram[s] ?? 0), 0);
}

function MoneyPanel({ label, panel }: { label: string; panel: { median_pe: number | null; median_pb: number | null; median_roe: number | null; companies: number } | null }) {
  return (
    <div className="rounded-md border border-line bg-panel px-4 py-3">
      <p className="font-mono text-[10px] uppercase tracking-widest text-dim">{label}</p>
      {panel == null || panel.companies === 0 ? (
        <p className="mt-1 text-sm text-fog">No companies.</p>
      ) : (
        <div className="mt-1 grid grid-cols-3 gap-2 font-mono text-sm tabular-nums">
          <span className="text-paper">PE {panel.median_pe?.toFixed(1) ?? "—"}</span>
          <span className="text-paper">PB {panel.median_pb?.toFixed(1) ?? "—"}</span>
          <span className="text-paper">ROE {panel.median_roe != null ? `${(panel.median_roe * 100).toFixed(1)}%` : "—"}</span>
        </div>
      )}
    </div>
  );
}

function SignalHistogram({ histogram, total }: { histogram: Record<string, number>; total: number }) {
  return (
    <div className="space-y-2">
      <p className="font-mono text-xs uppercase tracking-widest text-dim">Signal histogram</p>
      <ul className="space-y-1.5 text-sm">
        {SIGNAL_ORDER.map((sig) => {
          const n = histogram[sig] ?? 0;
          if (!n) return null;
          const tone = signalTone(sig === "score_missing" ? null : sig);
          const color = tone === "good" ? "bg-good" : tone === "mid" ? "bg-mid" : tone === "bad" ? "bg-bad" : "bg-info";
          return (
            <li key={sig} className="flex items-center gap-3">
              <span className="w-36 shrink-0 text-fog">{signalLabel(sig === "score_missing" ? null : sig)}</span>
              <span className="h-3 rounded-sm transition-all" style={{ width: `${Math.max(4, (n / total) * 380)}px` }}>
                <span className={`block h-3 rounded-sm ${color}`} />
              </span>
              <span className="font-mono tabular-nums">{n}</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-md border border-line bg-panel px-4 py-3">
      <p className="font-mono text-[10px] uppercase tracking-widest text-dim">{label}</p>
      <p className="mt-1 font-mono text-2xl tabular-nums text-paper">{value}</p>
    </div>
  );
}
