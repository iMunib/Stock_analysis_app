import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { api, ApiError, enc } from "../api/client";
import type { SectorRankingsOut, SectorSnapshotOut } from "../api/types";
import { CompanyLink, ErrorBanner, Score, SignalBadge, Spinner } from "../components/ui";
import { SIGNAL_ORDER, signalTone } from "../api/visuals";
import { signalLabel } from "../api/copy";
import { MAX_COMPARE, toggleCompareId } from "../lib/compare";

export default function Sector() {
  const { sheet = "" } = useParams();
  const [params, setParams] = useSearchParams();
  const currency = params.get("currency") === "CAD" ? "CAD" : "USD";
  const nav = useNavigate();
  const [snapshot, setSnapshot] = useState<SectorSnapshotOut | null>(null);
  const [rankings, setRankings] = useState<SectorRankingsOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<string[]>([]);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    Promise.allSettled([
      api.sectorSnapshot(sheet, currency),
      api.sectorRankings(sheet, currency, 500),
    ]).then(([snap, rank]) => {
      if (snap.status === "fulfilled") setSnapshot(snap.value);
      else setError((snap.reason as ApiError).message);
      if (rank.status === "fulfilled") setRankings(rank.value);
      else if (snap.status === "rejected") setError((rank.reason as ApiError).message);
      setLoading(false);
    });
  }, [sheet, currency]);

  useEffect(() => {
    setSelected([]);
    load();
  }, [load]);

  const toggle = (cid: string) => setSelected((cur) => toggleCompareId(cur, cid));

  const goCompare = () => {
    if (selected.length >= 2) nav(`/compare?ids=${selected.map(enc).join(",")}`);
  };

  return (
    <div className="space-y-8">
      <nav className="text-xs text-dim" aria-label="Breadcrumb">
        <Link to="/" className="hover:text-gold">Desk</Link>
        <span className="mx-1.5">/</span>
        <Link to="/sectors" className="hover:text-gold">Sectors</Link>
        <span className="mx-1.5">/</span>
        <span className="font-mono">{sheet}</span>
      </nav>

      <header className="space-y-3">
        <h1 className="font-display text-3xl tracking-tight">{sheet.replace(/^GICS_/, "").replace(/_/g, " ")}</h1>
        <div className="flex items-center gap-3" role="group" aria-label="Currency toggle (required)">
          <span className="font-mono text-[10px] uppercase tracking-widest text-dim">Currency</span>
          {(["USD", "CAD"] as const).map((c) => (
            <button
              key={c}
              onClick={() => setParams({ currency: c })}
              aria-pressed={currency === c}
              className={`rounded border px-3 py-1 font-mono text-xs ${
                currency === c ? "border-gold bg-gold/15 text-gold" : "border-line text-fog hover:border-line2 hover:text-paper"
              }`}
            >
              {c}
            </button>
          ))}
        </div>
      </header>

      {loading && <Spinner label="Loading sector…" />}
      {error && <ErrorBanner message={error} onRetry={load} />}

      {snapshot && !loading && (
        <section aria-label="Sector stats" className="grid grid-cols-2 gap-4 sm:grid-cols-5">
          <Stat label="Companies" value={snapshot.companies} />
          <Stat label="Scored" value={snapshot.scored} />
          <Stat label="Median score" value={snapshot.median_composite?.toFixed(1) ?? "—"} />
          <Stat label="Median PE" value={snapshot.median_pe?.toFixed(1) ?? "—"} />
          <Stat label="Median ROE" value={snapshot.median_roe != null ? `${(snapshot.median_roe * 100).toFixed(1)}%` : "—"} />
        </section>
      )}

      {snapshot && !loading && (
        <section aria-label="Signal histogram" className="space-y-2">
          <p className="font-mono text-xs uppercase tracking-widest text-dim">Signal histogram</p>
          <ul className="space-y-1.5 text-sm">
            {SIGNAL_ORDER.map((sig) => {
              const n = snapshot.signal_histogram[sig] ?? 0;
              if (!n) return null;
              const tone = signalTone(sig === "score_missing" ? null : sig);
              const color = tone === "good" ? "bg-good" : tone === "mid" ? "bg-mid" : tone === "bad" ? "bg-bad" : "bg-info";
              return (
                <li key={sig} className="flex items-center gap-3">
                  <span className="w-36 shrink-0 text-fog">{signalLabel(sig === "score_missing" ? null : sig)}</span>
                  <span className="h-3 rounded-sm" style={{ width: `${Math.max(4, (n / snapshot.companies) * 380)}px` }}>
                    <span className={`block h-3 rounded-sm ${color}`} />
                  </span>
                  <span className="font-mono tabular-nums">{n}</span>
                </li>
              );
            })}
          </ul>
        </section>
      )}

      {rankings && !loading && (
        <section aria-label="Ranked companies" className="space-y-3">
          <div className="flex items-center justify-between gap-4">
            <h2 className="font-display text-xl">Ranked companies</h2>
            <button
              onClick={goCompare}
              disabled={selected.length < 2}
              className={`rounded-md border px-4 py-2 text-sm ${
                selected.length >= 2
                  ? "border-gold/60 bg-gold/10 text-gold hover:bg-gold/20"
                  : "border-line text-dim cursor-not-allowed"
              }`}
            >
              Compare selected ({selected.length})
            </button>
          </div>
          {selected.length > 0 && selected.length > MAX_COMPARE && (
            <p className="text-xs text-warn">Maximum {MAX_COMPARE} companies per comparison.</p>
          )}
          <div className="overflow-x-auto rounded-md border border-line">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line bg-panel text-left font-mono text-[10px] uppercase tracking-widest text-dim">
                  <th scope="col" className="px-3 py-2 w-8"></th>
                  <th scope="col" className="px-3 py-2 w-12 text-right">#</th>
                  <th scope="col" className="px-3 py-2">Company</th>
                  <th scope="col" className="px-3 py-2 text-right">Score</th>
                  <th scope="col" className="px-3 py-2">Signal</th>
                  <th scope="col" className="px-3 py-2 text-right">Peer rank</th>
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
                    <td className="px-3 py-2 text-right font-mono tabular-nums"><Score value={r.composite} /></td>
                    <td className="px-3 py-2"><SignalBadge signal={r.signal} small /></td>
                    <td className="px-3 py-2 text-right font-mono tabular-nums text-fog">
                      {r.peer_rank != null ? `${r.peer_rank}` : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
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
