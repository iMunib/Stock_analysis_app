import { useEffect, useState } from "react";
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
} from "../api/copy";
import { CompanyLink, ErrorBanner, HalalBadge, Score, SignalBadge, Spinner } from "../components/ui";

export default function Dossier() {
  const { companyId = "" } = useParams();
  const [data, setData] = useState<DossierOut | null>(null);
  const [similar, setSimilar] = useState<SimilarOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setData(null);
    setSimilar(null);
    setError(null);
    const dossier = api.dossier(companyId);
    const sim = api.similar(companyId, 5);
    dossier
      .then(setData)
      .catch((e: ApiError) => setError(e.message))
      .finally(() => setLoading(false));
    sim.then(setSimilar).catch(() => setSimilar(null)); // 409 (NULL score) is fine: hide the block
  }, [companyId]);

  if (loading) return <Spinner label={`Loading dossier for ${companyId}…`} />;
  if (error) return <ErrorBanner message={error} />;
  if (!data) return null;

  const s = data.score;
  const snap = data.latest_snapshot ?? {};
  const cur = data.identity.currency;
  const isFinancial = (data.identity.gics_sector ?? "").toLowerCase() === "financials";
  const bankNote = bankPathCopy(isFinancial);
  const penaltyNote = coveragePenaltyCopy(s?.coverage ?? null, s?.penalty ?? null);

  return (
    <div className="space-y-8">
      <nav className="text-xs text-dim" aria-label="Breadcrumb">
        <Link to="/" className="hover:text-gold">Home</Link>
        <span className="mx-2">/</span>
        <span className="font-mono">{companyId}</span>
      </nav>

      <header className="flex flex-wrap items-end justify-between gap-6 border-b border-line pb-6">
        <div>
          <h1 className="font-display text-4xl tracking-tight">{data.identity.name ?? companyId}</h1>
          <p className="mt-2 font-mono text-sm text-dim">
            {companyId} · {data.identity.gics_sector}
            {data.identity.custom_industry_sheet ? ` · ${data.identity.custom_industry_sheet}` : ""} ·{" "}
            <span className="text-info">{cur}</span>
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <SignalBadge signal={s?.signal ?? "insufficient_data"} />
            <HalalBadge status={data.halal?.status} />
            <span className="text-xs text-fog">{halalCopy(data.halal?.status)}</span>
          </div>
        </div>
        <div className="text-right">
          <p className="font-mono text-[10px] uppercase tracking-widest text-dim">Research score</p>
          <Score value={s?.composite ?? null} size="lg" />
          <p className="mt-1 text-sm text-fog">
            {s?.peer_rank
              ? `Peer rank ${s.peer_rank} of ${s.peer_n} (${s.peer_set_type === "custom_industry_currency" ? "same industry" : "same sector"}, same currency)`
              : "Not ranked (score missing)"}
          </p>
        </div>
      </header>

      <section aria-label="Signal explanation" className="space-y-2 text-sm leading-relaxed text-fog">
        <p>{signalCopy(s?.signal)}</p>
        <p>{growthCopy(s?.pillars.growth ?? null)}</p>
        {penaltyNote && <p>{penaltyNote}</p>}
        {bankNote && <p>{bankNote}</p>}
      </section>

      <section aria-label="Score pillars" className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <PillarCard name="Quality" value={s?.pillars.quality ?? null} note="profitability vs peers" />
        <PillarCard name="Value" value={s?.pillars.value ?? null} note="cheaper = higher" />
        <PillarCard name="Growth" value={s?.pillars.growth ?? null} note="needs 3+ years on file" />
        <PillarCard name="Risk" value={s?.pillars.risk ?? null} note="safer = higher" />
      </section>

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

      <section aria-label="Latest snapshot" className="space-y-3">
        <h2 className="font-display text-xl">Latest snapshot</h2>
        <div className="overflow-x-auto rounded-md border border-line">
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
        <p className="text-xs text-dim">
          Money shown in the company's own currency ({cur}) — never converted. Source: {String(snap.source ?? "—")}
        </p>
      </section>

      {data.history_annual.length > 0 && (
        <section aria-label="Annual history" className="space-y-3">
          <h2 className="font-display text-xl">Annual history</h2>
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
                {data.history_annual.map((h) => (
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
          <p className="text-xs text-dim">Values in {cur} as filed — no currency conversion.</p>
        </section>
      )}

      <div className="flex flex-wrap gap-6">
        <Link to={`/compare?ids=${enc(data.identity.company_id)}`} className="text-sm text-gold hover:underline">
          Add to compare →
        </Link>
        {data.identity.custom_industry_sheet && (
          <Link
            to={`/sectors/${enc(data.identity.custom_industry_sheet)}?currency=${cur}`}
            className="text-sm text-gold hover:underline"
          >
            Browse {data.identity.custom_industry_sheet} →
          </Link>
        )}
      </div>

      {similar && similar.items.length > 0 && (
        <section aria-label="Similar names" className="space-y-3">
          <h2 className="font-display text-xl">
            Similar names <span className="font-mono text-xs text-dim">({similar.peer_set_type === "custom_industry_currency" ? "same industry" : "same sector"}, same currency)</span>
          </h2>
          <ul className="divide-y divide-line rounded-md border border-line bg-panel">
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
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      {data.halal && data.halal.failed_tests.length > 0 && (
        <section aria-label="Halal flag details" className="rounded-md border border-line bg-panel p-4 text-sm">
          <p className="font-mono text-xs uppercase tracking-widest text-dim">Why this flag fired</p>
          <ul className="mt-2 list-inside list-disc space-y-1 text-fog">
            {data.halal.failed_tests.map((t, i) => (
              <li key={i}>{t.test === "activity_screen" ? "Business-activity screen (industry classification)" : t.test}</li>
            ))}
          </ul>
          <p className="mt-2 text-xs text-dim">{halalCopy(data.halal.status)}</p>
        </section>
      )}
    </div>
  );
}

function PillarCard({ name, value, note }: { name: string; value: number | null; note: string }) {
  return (
    <div className="rounded-md border border-line bg-panel px-4 py-3">
      <p className="font-mono text-[10px] uppercase tracking-widest text-dim">{name}</p>
      <Score value={value} />
      <p className="mt-1 text-xs text-fog">{value === null ? growthCopy(null).split(" — ")[0] : note}</p>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <tr>
      <th scope="row" className="px-4 py-2 text-left font-normal text-fog">{label}</th>
      <td className="px-4 py-2 text-right font-mono tabular-nums text-paper">{value}</td>
    </tr>
  );
}
