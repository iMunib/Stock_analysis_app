import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, ApiError, enc } from "../api/client";
import type { DossierOut, SimilarOut } from "../api/types";
import {
  bankPathCopy,
  coveragePenaltyCopy,
  gapLabel,
  growthCopy,
  halalCopy,
  money,
  pct,
  ratio,
  signalCopy,
  whyBullets,
} from "../api/copy";
import { CompanyLink, ErrorBanner, HalalBadge, Score, SignalBadge, Spinner } from "../components/ui";
import { ScoreBar } from "../components/bars";
import { columnHeights } from "../lib/bars";
import { getCompareSelection, toggleCompareSelection } from "../lib/sessionCompare";

export default function Dossier() {
  const { companyId = "" } = useParams();
  const [data, setData] = useState<DossierOut | null>(null);
  const [similar, setSimilar] = useState<SimilarOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [loading, setLoading] = useState(true);
  const [compareSet, setCompareSet] = useState<string[]>(getCompareSelection());

  const load = () => {
    setLoading(true);
    setError(null);
    setNotFound(false);
    api.dossier(companyId)
      .then(setData)
      .catch((e: ApiError) => {
        if (e.status === 404) setNotFound(true);
        else setError(e.message);
      })
      .finally(() => setLoading(false));
    api.similar(companyId, 5).then(setSimilar).catch(() => setSimilar(null));
  };

  useEffect(load, [companyId]);

  const inCompare = compareSet.includes(companyId);

  const bullets = useMemo(() => (data ? whyBullets(data) : []), [data]);

  if (loading) return <Spinner label={`Loading dossier for ${companyId}…`} />;
  if (notFound) return <NotFound companyId={companyId} />;
  if (error) return <ErrorBanner message={error} onRetry={load} />;
  if (!data) return null;

  const s = data.score;
  const snap = data.latest_snapshot ?? {};
  const cur = data.identity.currency ?? "";
  const isFinancial =
    (data.identity.gics_sector ?? "").toLowerCase() === "financials" ||
    ["banks", "insurance", "credit_services"].includes((data.identity.custom_industry_sheet ?? "").toLowerCase());
  const bankNote = bankPathCopy(isFinancial);
  const penaltyNote = coveragePenaltyCopy(s?.coverage ?? null, s?.penalty ?? null);
  const pillarNull = s === null;
  const pillars = s?.pillars ?? { quality: null, value: null, growth: null, risk: null };

  const history = data.history_annual;
  const revHeights = columnHeights(history.map((h) => h.revenue ?? null), 96);
  const niPresent = history.some((h) => h.net_income != null && h.net_income > 0);
  const niHeights = columnHeights(history.map((h) => h.net_income ?? null), 96);

  return (
    <div className="space-y-8">
      <nav className="text-xs text-dim" aria-label="Breadcrumb">
        <Link to="/" className="hover:text-gold">Desk</Link>
        <span className="mx-1.5">/</span>
        <Link to="/sectors" className="hover:text-gold">Sectors</Link>
        {data.identity.custom_industry_sheet && (
          <>
            <span className="mx-1.5">/</span>
            <Link to={`/sectors/${enc(data.identity.custom_industry_sheet)}?currency=${cur}`} className="hover:text-gold">
              {data.identity.custom_industry_sheet}
            </Link>
          </>
        )}
        <span className="mx-1.5">/</span>
        <span className="font-mono text-paper">{data.identity.name ?? companyId}</span>
      </nav>

      {/* Identity strip */}
      <section aria-label="Identity" className="border-b border-line pb-5">
        <h1 className="font-display text-4xl tracking-tight">{data.identity.name ?? companyId}</h1>
        <div className="mt-2 flex flex-wrap items-center gap-2 text-sm">
          <span className="font-mono text-dim">{companyId}</span>
          {cur && <span className="rounded border border-info/40 px-2 py-0.5 font-mono text-xs text-info">{cur}</span>}
          {data.identity.gics_sector && <span className="text-fog">{data.identity.gics_sector}</span>}
          {data.identity.custom_industry_sheet && (
            <span className="text-fog">· {data.identity.custom_industry_sheet}</span>
          )}
          {(data.identity.indexes ?? []).map((idx) => (
            <span key={idx} className="rounded border border-line2 px-2 py-0.5 font-mono text-[10px] text-fog">
              {idx}
            </span>
          ))}
        </div>
      </section>

      {/* Verdict strip — lead with signal + peer rank, not the 0-10 */}
      <section aria-label="Verdict" className="rounded-md border border-line bg-panel p-5">
        <div className="flex flex-wrap items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <SignalBadge signal={s?.signal ?? "insufficient_data"} />
            {s?.peer_rank != null && s?.peer_n != null && (
              <span className="font-mono text-sm text-paper">
                #{s.peer_rank} of {s.peer_n}{" "}
                <span className="text-fog">in {s.peer_set_type === "custom_industry_currency" ? "its industry" : "its sector"} ({cur})</span>
              </span>
            )}
          </div>
          <div className="text-right">
            <span className="font-mono text-[10px] uppercase tracking-widest text-dim">Research score</span>
            {s === null ? (
              <p className="font-display text-2xl text-fog">Score not computed</p>
            ) : (
              <Score value={s.composite} size="lg" />
            )}
            {s && <span className="ml-2 font-mono text-xs text-dim">{s.coverage}/4 pillars</span>}
          </div>
        </div>
        <p className="mt-3 text-sm text-fog">{s === null ? "This name has not been scored yet." : signalCopy(s.signal)}</p>
        {s && <p className="mt-1 text-sm text-fog">{growthCopy(s.pillars.growth ?? null)}</p>}
        {penaltyNote && <p className="mt-1 text-sm text-fog">{penaltyNote}</p>}
        {bankNote && <p className="mt-1 text-sm text-fog">{bankNote}</p>}
      </section>

      {/* Gaps (moved up, under verdict) */}
      {data.data_gaps.length > 0 && (
        <section aria-label="Data gaps" className="rounded-md border border-line bg-panel p-4 text-sm">
          <p className="font-mono text-xs uppercase tracking-widest text-dim">Data gaps on file</p>
          <ul className="mt-2 list-inside list-disc space-y-1 text-fog">
            {data.data_gaps.map((g) => (
              <li key={g}>{gapLabel(g)}</li>
            ))}
          </ul>
        </section>
      )}

      {/* Pillar board */}
      <section aria-label="Score pillars" id="pillars">
        <h2 className="font-display text-xl">How it scores</h2>
        <div className="mt-3 grid grid-cols-2 gap-4 lg:grid-cols-4">
          {(["quality", "value", "growth", "risk"] as const).map((name) => {
            const v = pillarNull ? null : pillars[name];
            return (
              <button
                key={name}
                onClick={() => document.getElementById("why")?.scrollIntoView({ behavior: "smooth" })}
                className="rounded-md border border-line bg-panel p-4 text-left hover:border-gold/60 transition-colors"
              >
                <div className="flex items-baseline justify-between">
                  <span className="font-mono text-xs uppercase tracking-widest text-dim">{name}</span>
                  <span className="font-mono text-sm tabular-nums text-paper">{v == null ? "—" : v.toFixed(1)}</span>
                </div>
                <div className="mt-2">
                  <ScoreBar value={v} label={name} />
                </div>
                <p className="mt-2 text-xs text-fog">
                  {v == null ? gapSentence(name) : pillarNote(name)}
                </p>
              </button>
            );
          })}
        </div>
      </section>

      {/* Why box */}
      <section aria-label="Why this score" id="why" className="rounded-md border border-line bg-panel p-5">
        <h2 className="font-display text-xl">Why this score</h2>
        {bullets.length === 0 ? (
          <p className="mt-2 text-sm text-fog">Not enough fields on file to explain a score.</p>
        ) : (
          <ul className="mt-2 list-inside list-disc space-y-1.5 text-sm text-paper">
            {bullets.map((b, i) => (
              <li key={i}>{b}</li>
            ))}
          </ul>
        )}
      </section>

      {/* Snapshot table */}
      <section aria-label="Latest snapshot">
        <h2 className="font-display text-xl">Latest snapshot</h2>
        <div className="mt-3 overflow-x-auto rounded-md border border-line">
          <table className="w-full text-sm">
            <tbody className="divide-y divide-line">
              <Row label="Revenue" value={money(snap.revenue as number, cur)} />
              <Row label="Net income" value={money(snap.net_income as number, cur)} />
              <Row label="Diluted EPS" value={ratio(snap.diluted_eps as number, 2)} />
              <Row label="Free cash flow" value={money(snap.fcf_calc as number, cur)} />
              <Row label="ROE" value={pct(snap.roe_calc as number)} />
              <Row label="ROA" value={pct(snap.roa_calc as number)} />
              <Row label="FCF margin" value={pct(snap.fcfmargin_calc as number)} />
              <Row label="PE" value={ratio(snap.pe_calc as number, 1)} />
              <Row label="PB" value={ratio(snap.pb_calc as number, 1)} />
              <Row label="EV/EBITDA" value={ratio(snap.ev_to_ebitda_calc as number, 1)} />
              <Row label="Price" value={snap.price != null ? money(snap.price as number, (snap.price_currency as string) ?? cur) : "—"} />
              <Row label="Market cap" value={money(snap.market_cap as number, (snap.price_currency as string) ?? cur)} />
              <Row label="As of" value={(snap.as_of_date as string) ?? "—"} />
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-xs text-dim">
          Money shown in {cur || "native currency"} — never converted. Source: {String(snap.source ?? "—")}
        </p>
      </section>

      {/* History */}
      <section aria-label="Annual history">
        <h2 className="font-display text-xl">Annual history</h2>
        {history.length === 0 ? (
          <p className="mt-2 text-sm text-fog">No annual history on file.</p>
        ) : history.length < 3 ? (
          <p className="mt-2 rounded-md border border-line bg-panel p-4 text-sm text-fog">
            {growthCopy(s?.pillars.growth ?? null)} A trend line would be guesswork, so we show the raw rows instead.
          </p>
        ) : (
          <div className="mt-3 grid gap-6 lg:grid-cols-[1fr_240px]">
            <div className="overflow-x-auto rounded-md border border-line">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-line bg-panel text-left font-mono text-[10px] uppercase tracking-widest text-dim">
                    <th scope="col" className="px-4 py-2">FY</th>
                    <th scope="col" className="px-4 py-2 text-right">Revenue</th>
                    <th scope="col" className="px-4 py-2 text-right">Net income</th>
                    <th scope="col" className="px-4 py-2 text-right">FCF</th>
                    <th scope="col" className="px-4 py-2 text-right">EPS</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {history.map((h) => (
                    <tr key={h.fiscal_year} className="font-mono tabular-nums">
                      <td className="px-4 py-2 text-paper">{h.fiscal_year}</td>
                      <td className="px-4 py-2 text-right text-fog">{money(h.revenue ?? null, null)}</td>
                      <td className="px-4 py-2 text-right text-fog">{money(h.net_income ?? null, null)}</td>
                      <td className="px-4 py-2 text-right text-fog">{money(h.fcf_calc ?? null, null)}</td>
                      <td className="px-4 py-2 text-right text-fog">{h.diluted_eps ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="space-y-4">
              <BarsColumn label="Revenue" rows={history} heights={revHeights} />
              {niPresent && <BarsColumn label="Net income" rows={history} heights={niHeights} />}
            </div>
          </div>
        )}
        {history.length > 0 && <p className="mt-2 text-xs text-dim">Values in {cur} as filed — no currency conversion.</p>}
      </section>

      {/* Similar */}
      {similar && similar.items.length > 0 && (
        <section aria-label="Similar names">
          <h2 className="font-display text-xl">
            Similar names{" "}
            <span className="font-mono text-xs text-dim">
              ({similar.peer_set_type === "custom_industry_currency" ? "same industry" : "same sector"}, same currency)
            </span>
          </h2>
          <ul className="mt-3 divide-y divide-line rounded-md border border-line bg-panel">
            {similar.items.map((it) => (
              <li key={it.company_id} className="flex items-center justify-between gap-4 px-4 py-3">
                <div>
                  <CompanyLink companyId={it.company_id}>{it.name ?? it.company_id}</CompanyLink>
                  <span className={`ml-2 font-mono text-[10px] uppercase tracking-wider ${it.better ? "text-good" : "text-dim"}`}>
                    {it.better ? "▲ scores higher" : "▼ scores lower"}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <Score value={it.composite} />
                  <SignalBadge signal={it.signal} small />
                  <Link
                    to={`/compare?ids=${[companyId, it.company_id].map(enc).join(",")}`}
                    className="text-xs text-gold hover:underline"
                  >
                    Compare
                  </Link>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Halal */}
      {data.halal && (
        <section aria-label="Halal flag" className="rounded-md border border-line bg-panel p-4">
          <div className="flex items-center gap-3">
            <HalalBadge status={data.halal.status} />
            <span className="text-sm text-fog">{halalCopy(data.halal.status)}</span>
          </div>
          {data.halal.failed_tests.length > 0 && (
            <ul className="mt-3 list-inside list-disc space-y-1 text-sm text-fog">
              {data.halal.failed_tests.map((t, i) => (
                <li key={i}>{t.test === "activity_screen" ? "Business-activity screen (industry classification)" : t.test}</li>
              ))}
            </ul>
          )}
          <p className="mt-2 text-xs text-dim">Not a religious ruling.</p>
        </section>
      )}

      {/* Actions */}
      <section aria-label="Actions" className="flex flex-wrap items-center gap-4 border-t border-line pt-5">
        <label className="flex cursor-pointer items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={inCompare}
            onChange={() => setCompareSet(toggleCompareSelection(companyId))}
            className="h-4 w-4 accent-[#e0a84f]"
          />
          Add to compare
        </label>
        {similar && similar.items.length > 0 && (
          <Link
            to={`/compare?ids=${[companyId, ...similar.items.slice(0, 3).map((i) => i.company_id)].map(enc).join(",")}`}
            className="text-sm text-gold hover:underline"
          >
            Compare with similar →
          </Link>
        )}
        {compareSet.length >= 2 && (
          <Link to={`/compare?ids=${compareSet.map(enc).join(",")}`} className="text-sm text-gold hover:underline">
            Go to compare ({compareSet.length} selected) →
          </Link>
        )}
      </section>
    </div>
  );
}

function gapSentence(name: string): string {
  switch (name) {
    case "growth":
      return "Growth not scored — fewer than 3 years of history in the database.";
    case "quality":
      return "Quality not scored — missing profitability inputs.";
    case "value":
      return "Value not scored — missing price or peer multiples.";
    default:
      return "Risk not scored — missing balance-sheet inputs.";
  }
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

function Row({ label, value }: { label: string; value: string }) {
  return (
    <tr>
      <th scope="row" className="px-4 py-2 text-left font-normal text-fog">{label}</th>
      <td className="px-4 py-2 text-right font-mono tabular-nums text-paper">{value}</td>
    </tr>
  );
}

function BarsColumn({ label, rows, heights }: { label: string; rows: DossierOut["history_annual"]; heights: number[] }) {
  return (
    <div>
      <p className="font-mono text-[10px] uppercase tracking-widest text-dim">{label}</p>
      <svg viewBox={`0 0 ${rows.length * 40} 100`} className="mt-1 h-24 w-full" role="img" aria-label={`${label} by fiscal year`}>
        {rows.map((h, i) => {
          const hh = heights[i] ?? 0;
          return <rect key={h.fiscal_year} x={i * 40 + 8} y={100 - hh} width={26} height={Math.max(hh, 0)} rx="2" fill="#e0a84f" />;
        })}
      </svg>
      <div className="mt-1 flex justify-between font-mono text-[9px] text-dim">
        <span>{rows[0]?.fiscal_year}</span>
        <span>{rows[rows.length - 1]?.fiscal_year}</span>
      </div>
    </div>
  );
}

function NotFound({ companyId }: { companyId: string }) {
  return (
    <div className="space-y-4">
      <h1 className="font-display text-3xl tracking-tight">Company not found</h1>
      <p className="text-sm text-fog">
        No company with ID <span className="font-mono">{companyId}</span> in the database.
      </p>
      <p className="text-sm text-fog">Use the search bar above, or browse:</p>
      <div className="flex gap-4 text-sm">
        <Link to="/sectors" className="text-gold hover:underline">Browse sectors →</Link>
        <Link to="/" className="text-gold hover:underline">Back to the desk →</Link>
      </div>
    </div>
  );
}
