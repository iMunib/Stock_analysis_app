import type { DossierOut, PractitionerOut } from "../../api/types";
import VerdictBadge, { computeVerdict } from "./VerdictBadge";
import { CompositeGauge, PillarRadar } from "../viz";
import { SignalBadge } from "../ui";
import { money } from "../../lib/format";

export interface ExecutiveCockpitProps {
  data: DossierOut;
  practitioner?: PractitionerOut | null;
  className?: string;
}

const WACC_ASSUMPTION = 8.0;

function MoatStatus({ roic }: { roic: number | null }) {
  if (roic === null) return { label: "Not applicable: Bank model", tone: "text-ink-2 border-border bg-bg-2" };
  const spread = roic - WACC_ASSUMPTION;
  if (spread > 7) return { label: `Wide Moat · ${roic.toFixed(1)}% ROIC vs ${WACC_ASSUMPTION}% WACC (+${spread.toFixed(1)}% spread)`, tone: "text-pos border-pos/30 bg-pos-weak" };
  if (spread > 2) return { label: `Narrow Moat · ${roic.toFixed(1)}% ROIC vs ${WACC_ASSUMPTION}% WACC (+${spread.toFixed(1)}%)`, tone: "text-accent border-accent/30 bg-accent-weak" };
  if (spread > -2) return { label: `No Moat · ${roic.toFixed(1)}% ROIC vs ${WACC_ASSUMPTION}% WACC (${spread.toFixed(1)}%)`, tone: "text-warn border-warn/30 bg-warn-weak" };
  return { label: `Negative Spread · ${roic.toFixed(1)}% ROIC vs ${WACC_ASSUMPTION}% WACC (${spread.toFixed(1)}%)`, tone: "text-neg border-neg/30 bg-neg-weak" };
}

function SolvencyStatus({ altmanZ, netDebt, currency }: { altmanZ: number | null; netDebt: number; currency: string }) {
  if (altmanZ === null) return { label: "Not applicable: Bank model — use CET1/Leverage", tone: "text-ink-2 border-border bg-bg-2" };
  const distance = altmanZ - 1.81;
  if (altmanZ > 2.99) return { label: `Pristine · Z ${altmanZ.toFixed(2)} (+${distance.toFixed(2)} above distress) · Net ${netDebt <= 0 ? "Cash " + money(Math.abs(netDebt), currency) : "Debt " + money(netDebt, currency)}`, tone: "text-pos border-pos/30 bg-pos-weak" };
  if (altmanZ > 1.81) return { label: `Grey Zone · Z ${altmanZ.toFixed(2)} (+${distance.toFixed(2)} above distress)`, tone: "text-warn border-warn/30 bg-warn-weak" };
  return { label: `Distress Risk · Z ${altmanZ.toFixed(2)} (${distance.toFixed(2)} below threshold)`, tone: "text-neg border-neg/30 bg-neg-weak" };
}

export function ExecutiveCockpit({ data, practitioner, className = "" }: ExecutiveCockpitProps) {
  const snap = data.latest_snapshot ?? {};
  const s = data.score;
  const cur = data.identity.currency || "USD";
  const name = data.identity.name || data.identity.company_id;

  const rawRoic = typeof snap.roic === "number" ? snap.roic : typeof (snap as any).roic_calc === "number" ? (snap as any).roic_calc : (practitioner as any)?.distress_analysis?.roic ?? null;
  const roic = typeof rawRoic === "number" ? (Math.abs(rawRoic) <= 1 ? rawRoic * 100 : rawRoic) : null;

  const totalDebt = typeof snap.total_debt === "number" ? snap.total_debt : 0;
  const cash = typeof snap.cash_and_equivalents === "number" ? snap.cash_and_equivalents : typeof (snap as any).cash_st_investments === "number" ? (snap as any).cash_st_investments : 0;
  const netDebt = typeof (snap as any).netdebt_calc === "number" ? (snap as any).netdebt_calc : totalDebt - cash;
  const price = typeof snap.price === "number" ? snap.price : null;
  const pe = typeof snap.pe_calc === "number" ? snap.pe_calc : (typeof (snap as any).pe_ratio === "number" ? (snap as any).pe_ratio : null);

  const altmanZ = data.level3?.altman_breakdown?.active_z ?? practitioner?.distress_analysis?.active_z ?? practitioner?.distress_analysis?.z_score ?? (typeof snap.altman_z === "number" ? snap.altman_z : null);
  const altmanZone = data.level3?.altman_breakdown?.zone ?? practitioner?.distress_analysis?.zone ?? (altmanZ != null ? (altmanZ > 2.99 ? "Safe" : altmanZ < 1.81 ? "Distress" : "Grey") : null);
  const beneishFlagged = practitioner?.beneish_analysis?.is_manipulator === true || data.level3?.beneish_matrix?.is_manipulator === true;

  const impliedCagr = data.level1?.implied_10y_cagr ?? practitioner?.malkiel?.required_fcf_growth_10y ?? practitioner?.malkiel?.required_fcf_growth_pct ?? (typeof (snap as any).reverse_dcf_cagr === "number" ? (snap as any).reverse_dcf_cagr : null);
  const historicalCagr = data.level1?.historical_5y_cagr ?? (typeof snap.fcf_5y_cagr === "number" ? snap.fcf_5y_cagr : typeof (snap as any).historical_5y_cagr === "number" ? (snap as any).historical_5y_cagr : null);
  const reverseDcfGap = data.level1?.expectations_gap ?? (typeof (data as any).expectations_gap === "number" ? (Math.abs((data as any).expectations_gap) <= 1 ? (data as any).expectations_gap * 100 : (data as any).expectations_gap) : null) ?? (impliedCagr != null && historicalCagr != null ? impliedCagr - historicalCagr : null);

  const backendVerdict = data.level1?.verdict_badge || (data as any).decision_verdict?.verdict_badge;
  let verdictObj: { label: string; tone: "positive" | "warning" | "negative" | "info"; confidence: string };
  if (backendVerdict) {
    const tone = backendVerdict.includes("COMPOUNDER") || backendVerdict.includes("BARGAIN") ? "positive" : backendVerdict.includes("OVERVALUED") || backendVerdict.includes("CAUTION") || backendVerdict.includes("FAIR VALUE") ? "warning" : "negative";
    const conf = s?.coverage && s.coverage >= 4 ? "HIGH (4/4 Pillars Complete)" : s?.coverage === 3 ? "MEDIUM (3/4 Pillars Complete)" : "PRELIMINARY (Partial Coverage)";
    verdictObj = { label: backendVerdict, tone, confidence: conf };
  } else {
    const moatPass = roic != null && roic > 15;
    verdictObj = computeVerdict({
      signal: s?.signal,
      moatPass,
      altmanSafe: altmanZone === "Safe" || netDebt <= 0,
      altmanDistress: altmanZone === "Distress",
      reverseDcfGap,
      beneishFlagged,
      isCyclical: data.identity.custom_industry_sheet === "Commodities" || data.identity.gics_sector === "Energy",
      peRatio: pe,
      coverage: s?.coverage,
    });
  }

  const moat = MoatStatus({ roic });
  const solvency = SolvencyStatus({ altmanZ, netDebt, currency: cur });

  const pillars = {
    quality: s?.pillars.quality ?? null,
    value: s?.pillars.value ?? null,
    growth: s?.pillars.growth ?? null,
    risk: s?.pillars.risk ?? null,
  };

  return (
    <div className={`space-y-4 ${className}`} aria-label="Executive Cockpit HUD">
      {/* Tier 1 — 60s Cockpit */}
      <section
        aria-label="Tier 1: 60-Second Executive Cockpit"
        className="rounded-md border border-border-subtle bg-bg-1 p-4"
      >
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border-subtle pb-3 mb-3">
          <h2 className="font-heading text-sm font-bold uppercase tracking-wider text-ink-0">Tier 1 — 60s Cockpit · Instant Verdict</h2>
          <span className="font-mono text-[11px] text-ink-2">{s?.coverage != null ? `${s.coverage}/4 Pillars Verified` : "Coverage Pending"}</span>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-12">
          <div className="md:col-span-3 flex flex-col items-center justify-center rounded-md border border-border-subtle bg-bg-0 p-3">
            <span className="font-mono text-[10px] uppercase tracking-wider text-ink-2">Composite Score</span>
            <div className="mt-2">
              <CompositeGauge value={s?.composite ?? null} size="sm" showLabel={false} />
            </div>
            <span className="mt-1 font-mono text-lg font-bold text-accent">{s?.composite != null ? s.composite.toFixed(1) : "Not scored"} / 10</span>
            <div className="mt-2">
              <SignalBadge signal={s?.signal ?? "insufficient_data"} />
            </div>
            <span className="mt-1 font-mono text-[10px] text-ink-2">{name} · {cur}</span>
          </div>

          <div className="md:col-span-9 space-y-3">
            <div className="rounded border border-border-subtle bg-bg-0 p-3">
              <span className="block font-mono text-[10px] uppercase tracking-wider text-ink-2 font-semibold mb-1">Bottom-Line Verdict</span>
              <VerdictBadge verdict={verdictObj.label} tone={verdictObj.tone} confidence={verdictObj.confidence} />
              {price != null && <span className="mt-1 block font-mono text-[11px] text-ink-2">Price {money(price, cur)} · P/E {pe != null ? `${pe.toFixed(1)}x` : "Not reported in filing"}</span>}
            </div>

            <div className={`rounded border px-3 py-2 text-xs font-mono ${moat.tone}`} role="status" aria-label="Moat status">
              <span className="font-bold uppercase text-[10px] tracking-wider">Moat — ROIC persistence vs WACC · </span>
              <span>{moat.label}</span>
            </div>

            <div className={`rounded border px-3 py-2 text-xs font-mono ${solvency.tone}`} role="status" aria-label="Solvency status">
              <span className="font-bold uppercase text-[10px] tracking-wider">Solvency — Altman Z distance to default · </span>
              <span>{solvency.label}</span>
            </div>
          </div>
        </div>
      </section>

      {/* Tier 2 — Flight Deck */}
      <section
        aria-label="Tier 2: Flight Deck — Pillars & Base Rates"
        className="rounded-md border border-border-subtle bg-bg-1 p-4"
      >
        <h2 className="font-heading text-sm font-bold uppercase tracking-wider text-ink-0 border-b border-border-subtle pb-3 mb-3">Tier 2 — Flight Deck · Pillars & Context</h2>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
          <div className="lg:col-span-4 flex flex-col items-center rounded-md border border-border-subtle bg-bg-0 p-3">
            <span className="font-mono text-[10px] uppercase tracking-wider text-ink-2">4-Pillar Radar</span>
            <div className="mt-2">
              <PillarRadar quality={pillars.quality} value={pillars.value} growth={pillars.growth} risk={pillars.risk} size={180} />
            </div>
            <div className="mt-2 grid w-full grid-cols-4 gap-1 text-center font-mono text-[10px]">
              <span className="rounded bg-bg-1 border border-border-subtle py-1">Q {pillars.quality != null ? pillars.quality.toFixed(1) : "Not scored"}</span>
              <span className="rounded bg-bg-1 border border-border-subtle py-1">V {pillars.value != null ? pillars.value.toFixed(1) : "Not scored"}</span>
              <span className="rounded bg-bg-1 border border-border-subtle py-1">G {pillars.growth != null ? pillars.growth.toFixed(1) : "Not scored"}</span>
              <span className="rounded bg-bg-1 border border-border-subtle py-1">R {pillars.risk != null ? pillars.risk.toFixed(1) : "Not scored"}</span>
            </div>
          </div>

          <div className="lg:col-span-4 rounded-md border border-border-subtle bg-bg-0 p-3">
            <span className="font-mono text-[10px] uppercase tracking-wider text-ink-2 font-semibold">Sector Percentile Rankings</span>
            <div className="mt-2 space-y-2 text-xs">
              {data.pillar_drilldown?.sector_peer_medians ? (
                Object.entries(data.pillar_drilldown.sector_peer_medians as Record<string, number | null>).slice(0, 4).map(([k, v]) => (
                  <div key={k} className="flex items-center justify-between border-b border-border-subtle py-1 last:border-0">
                    <span className="font-mono uppercase text-[11px] text-ink-1">{k}</span>
                    <span className="font-mono text-ink-0">{v != null ? v.toFixed(1) : "Not reported in filing"}</span>
                  </div>
                ))
              ) : (
                <p className="text-xs text-ink-2">Sector medians from cached peer set (n={s?.peer_n ?? 1}).</p>
              )}
              <p className="font-mono text-[10px] text-ink-2 pt-1">Peer: {data.identity.custom_industry_sheet || data.identity.gics_sector || "Broad"} · n={s?.peer_n ?? 1} · {s?.peer_set_type}</p>
              {data.sector_medians && (
                <div className="mt-2 grid grid-cols-2 gap-1 font-mono text-[11px]">
                  {Object.entries(data.sector_medians).map(([k, v]) => (
                    <span key={k} className="text-ink-2">{k}: <span className="text-ink-0">{typeof v === "number" ? v.toFixed(2) : String(v)}</span></span>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="lg:col-span-4 rounded-md border border-border-subtle bg-bg-0 p-3 flex flex-col justify-between" data-testid="bessembinder-base-rate-panel">
            <div>
              <div className="flex items-center justify-between gap-2 mb-1">
                <span className="font-mono text-[10px] uppercase tracking-wider text-ink-2 font-semibold">Bessembinder Base Rate</span>
                <span className="rounded bg-accent-weak px-1.5 py-0.5 font-mono text-[10px] font-medium text-accent">42% Beat T-Bills</span>
              </div>
              <p className="text-xs text-ink-1 leading-relaxed">
                Only 42% of US common stocks beat 1-month T-Bills over their lifetime; median lifetime excess return is -100% (Bessembinder 2018/2024).
              </p>
            </div>
            <p className="mt-2 border-t border-border-subtle pt-2 font-mono text-[11px] text-ink-2 italic">High conviction must be weighed against unconditional survival odds.</p>
          </div>
        </div>
      </section>

      {/* Tier 3 — Engine Room */}
      <section
        aria-label="Tier 3: Engine Room — Forensics, Valuation & Filings"
        className="rounded-md border border-border-subtle bg-bg-1 p-4"
      >
        <h2 className="font-heading text-sm font-bold uppercase tracking-wider text-ink-0 border-b border-border-subtle pb-3 mb-3">Tier 3 — Engine Room · Drilldown Status</h2>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <div className="rounded-md border border-border-subtle bg-bg-0 p-3">
            <div className="flex items-center justify-between">
              <span className="font-mono text-xs font-semibold text-ink-0">Forensics</span>
              <span className={`h-2 w-2 rounded-full ${beneishFlagged ? "bg-neg" : "bg-pos"}`} aria-label={beneishFlagged ? "Flagged" : "Clean"} />
            </div>
            <p className="mt-1 text-xs text-ink-1">Beneish M-Score · Sloan Accruals · Schilit checks</p>
            <span className="mt-1 inline-block rounded bg-bg-1 border border-border-subtle px-2 py-0.5 font-mono text-[11px] text-ink-1">
              {beneishFlagged ? "Manipulator risk flagged" : "No manipulation flag"} · Altman {altmanZone ?? "Not scored"}
            </span>
            <div className="mt-3 flex gap-2">
              <a href={`#forensics`} onClick={(e) => { e.preventDefault(); document.getElementById("tabpanel-forensics")?.scrollIntoView({ behavior: "smooth" }); }} className="rounded border border-accent bg-accent-weak px-3 py-1 font-mono text-xs text-accent hover:bg-accent hover:text-bg-0 transition-colors" role="button" tabIndex={0}>Open Forensics �-</a>
            </div>
          </div>

          <div className="rounded-md border border-border-subtle bg-bg-0 p-3">
            <div className="flex items-center justify-between">
              <span className="font-mono text-xs font-semibold text-ink-0">Valuation</span>
              <span className="h-2 w-2 rounded-full bg-accent" aria-label="Valuation ready" />
            </div>
            <p className="mt-1 text-xs text-ink-1">DCF / EPV / Residual · Reverse DCF hurdle</p>
            <span className="mt-1 inline-block rounded bg-bg-1 border border-border-subtle px-2 py-0.5 font-mono text-[11px] text-ink-1">
              {impliedCagr != null ? `Implied ${impliedCagr.toFixed(1)}% vs Hist ${historicalCagr != null ? historicalCagr.toFixed(1) + "%" : "Not scored"}` : "Valuation inputs on file"}
            </span>
            <div className="mt-3 flex gap-2">
              <a href={`#valuation`} onClick={(e) => { e.preventDefault(); document.getElementById("tabpanel-valuation")?.scrollIntoView({ behavior: "smooth" }); }} className="rounded border border-accent bg-accent-weak px-3 py-1 font-mono text-xs text-accent hover:bg-accent hover:text-bg-0 transition-colors" role="button" tabIndex={0}>Open Valuation �-</a>
            </div>
          </div>

          <div className="rounded-md border border-border-subtle bg-bg-0 p-3">
            <div className="flex items-center justify-between">
              <span className="font-mono text-xs font-semibold text-ink-0">Filings & Provenance</span>
              <span className="h-2 w-2 rounded-full bg-pos" aria-label="Filings provenance" />
            </div>
            <p className="mt-1 text-xs text-ink-1">10-K / 10-Q provenance · As-filed vs restated</p>
            <span className="mt-1 inline-block rounded bg-bg-1 border border-border-subtle px-2 py-0.5 font-mono text-[11px] text-ink-1">
              Source: {String((snap as any).source ?? "Seed")} · FY {String((snap as any).fiscal_year ?? data.score?.as_of_fy ?? "Latest")}
            </span>
            <div className="mt-3 flex gap-2">
              <a href={`#sources`} onClick={(e) => { e.preventDefault(); document.getElementById("tabpanel-sources")?.scrollIntoView({ behavior: "smooth" }); }} className="rounded border border-accent bg-accent-weak px-3 py-1 font-mono text-xs text-accent hover:bg-accent hover:text-bg-0 transition-colors" role="button" tabIndex={0}>View Filings �-</a>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

export default ExecutiveCockpit;
