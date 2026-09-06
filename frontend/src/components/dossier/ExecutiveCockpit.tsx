import type { DossierOut, PractitionerOut } from "../../api/types";
import VerdictBadge, { computeVerdict } from "./VerdictBadge";
import TrafficLightTile from "./TrafficLightTile";
import ReverseDcfRuleBox from "./ReverseDcfRuleBox";
import DecisionBullets from "./DecisionBullets";
import { money } from "../../lib/format";

export interface ExecutiveCockpitProps {
  data: DossierOut;
  practitioner?: PractitionerOut | null;
  className?: string;
}

export function ExecutiveCockpit({ data, practitioner, className = "" }: ExecutiveCockpitProps) {
  const snap = data.latest_snapshot ?? {};
  const s = data.score;
  const cur = data.identity.currency || "USD";
  const name = data.identity.name || data.identity.company_id;

  // Extract financial data points
  const rawRoic = typeof snap.roic === "number" ? snap.roic : (typeof snap.roic_calc === "number" ? snap.roic_calc : (practitioner as any)?.distress_analysis?.roic ?? null);
  const roic = typeof rawRoic === "number" ? (Math.abs(rawRoic) <= 1 ? rawRoic * 100 : rawRoic) : null;

  const rawGrossMargin = typeof snap.gross_margin === "number" ? snap.gross_margin : (typeof snap.grossmargin_calc === "number" ? snap.grossmargin_calc : (typeof snap.revenue === "number" && typeof snap.gross_profit === "number" && snap.revenue > 0 ? snap.gross_profit / snap.revenue : null));
  const grossMargin = typeof rawGrossMargin === "number" ? (Math.abs(rawGrossMargin) <= 1 ? rawGrossMargin * 100 : rawGrossMargin) : null;

  const totalDebt = typeof snap.total_debt === "number" ? snap.total_debt : 0;
  const cash = typeof snap.cash_and_equivalents === "number" ? snap.cash_and_equivalents : (typeof snap.cash_st_investments === "number" ? snap.cash_st_investments : 0);
  const netDebt = typeof snap.net_debt === "number" ? snap.net_debt : (typeof snap.netdebt_calc === "number" ? snap.netdebt_calc : totalDebt - cash);
  const pe = typeof snap.pe_calc === "number" ? snap.pe_calc : (typeof (snap as any).pe_ratio === "number" ? (snap as any).pe_ratio : null);
  const price = typeof snap.price === "number" ? snap.price : null;

  // Solvency & Forensic data from practitioner or snapshot
  const altmanZ = data.level3?.altman_breakdown?.active_z ?? practitioner?.distress_analysis?.active_z ?? practitioner?.distress_analysis?.z_score ?? (typeof snap.altman_z === "number" ? snap.altman_z : null);
  const altmanZone = data.level3?.altman_breakdown?.zone ?? practitioner?.distress_analysis?.zone ?? (altmanZ != null ? (altmanZ > 2.99 ? "Safe" : altmanZ < 1.81 ? "Distress" : "Grey") : null);
  const beneishFlagged = practitioner?.beneish_analysis?.is_manipulator === true || data.level3?.beneish_matrix?.is_manipulator === true;

  // Growth & Valuation Hurdle from level1, practitioner Reverse DCF, or snapshot
  const impliedCagr =
    data.level1?.implied_10y_cagr ??
    practitioner?.malkiel?.required_fcf_growth_10y ??
    practitioner?.malkiel?.required_fcf_growth_pct ??
    (typeof (snap as any).reverse_dcf_cagr === "number" ? (snap as any).reverse_dcf_cagr : null);
  const historicalCagr =
    data.level1?.historical_5y_cagr ??
    (typeof snap.fcf_5y_cagr === "number" ? snap.fcf_5y_cagr : (typeof (snap as any).historical_5y_cagr === "number" ? (snap as any).historical_5y_cagr : null));
  const reverseDcfGap =
    data.level1?.expectations_gap ??
    (typeof data.expectations_gap === "number" ? (Math.abs(data.expectations_gap) <= 1 ? data.expectations_gap * 100 : data.expectations_gap) : null) ??
    (impliedCagr != null && historicalCagr != null ? impliedCagr - historicalCagr : null);


  // Moat evaluation
  const moatRatingStr = data.moat_rating?.moat_rating ?? (data.identity.custom_industry_sheet === "Banks" ? "Wide" : null);
  const moatPass = (roic != null && roic > 15) || (grossMargin != null && grossMargin > 40) || (s?.pillars.quality != null && s.pillars.quality >= 7.0) || moatRatingStr === "Wide";
  const moatStatus = moatRatingStr === "None"
    ? "NO MOAT / COMMODITY"
    : moatRatingStr
    ? `${moatRatingStr.toUpperCase()} MOAT`
    : (roic != null && roic > 20 && grossMargin != null && grossMargin > 40
    ? "WIDE MOAT"
    : roic != null && roic > 12
    ? "NARROW MOAT"
    : "NO MOAT / COMMODITY");
  const moatTone = moatStatus.includes("WIDE") ? "green" : moatStatus.includes("NARROW") ? "amber" : "red";

  // Solvency evaluation
  const isNetCash = netDebt <= 0;
  const solvencyStatus = altmanZone === "Distress"
    ? "DISTRESS RISK"
    : isNetCash || (altmanZ != null && altmanZ > 2.99)
    ? "PRISTINE"
    : "ADEQUATE";
  const solvencyTone = solvencyStatus === "PRISTINE" ? "green" : solvencyStatus === "ADEQUATE" ? "amber" : "red";

  // Valuation evaluation
  const valuationStatus = reverseDcfGap != null && reverseDcfGap > 5
    ? "PRICED FOR PERFECTION"
    : reverseDcfGap != null && reverseDcfGap < -2
    ? "UNDERVALUED BARGAIN"
    : "FAIRLY VALUED";
  const valuationTone = valuationStatus === "UNDERVALUED BARGAIN" ? "green" : valuationStatus === "FAIRLY VALUED" ? "amber" : "red";

  // Compute overall verdict prioritizing authoritative backend verdict
  const backendVerdict = data.level1?.verdict_badge || data.decision_verdict?.verdict_badge;
  let verdictObj: { label: string; tone: "positive" | "warning" | "negative" | "info"; confidence: string };

  if (backendVerdict) {
    const tone = backendVerdict.includes("COMPOUNDER") || backendVerdict.includes("BARGAIN")
      ? "positive"
      : backendVerdict.includes("OVERVALUED") || backendVerdict.includes("CAUTION") || backendVerdict.includes("FAIR VALUE")
      ? "warning"
      : "negative";
    const conf = s?.coverage && s.coverage >= 4
      ? "HIGH (4/4 Pillars Complete)"
      : s?.coverage === 3
      ? "MEDIUM (3/4 Pillars Complete)"
      : "PRELIMINARY (Partial Coverage)";
    verdictObj = { label: backendVerdict, tone, confidence: conf };
  } else {
    verdictObj = computeVerdict({
      signal: s?.signal,
      moatPass,
      altmanSafe: altmanZone === "Safe" || isNetCash,
      altmanDistress: altmanZone === "Distress",
      reverseDcfGap,
      beneishFlagged,
      isCyclical: data.identity.custom_industry_sheet === "Commodities" || data.identity.gics_sector === "Energy",
      peRatio: pe,
      coverage: s?.coverage,
    });
  }

  // Decision bullets derivation
  const backendBullets = data.level1?.decision_bullets || data.decision_verdict?.decision_bullets;
  const strengths: string[] = [];
  if (backendBullets && backendBullets.length > 0) {
    strengths.push(...backendBullets.slice(0, 3));
  } else {
    if (grossMargin != null && grossMargin > 40) strengths.push(`High gross margins (${grossMargin.toFixed(1)}%) reflecting durable pricing power.`);
    if (isNetCash) strengths.push(`Net cash balance sheet (${money(Math.abs(netDebt), cur)} net cash) insulating against debt stress.`);
    else if (altmanZ != null && altmanZ > 3.0) strengths.push(`Robust Altman Z-score (${altmanZ.toFixed(2)}) indicates negligible insolvency risk.`);
    if (roic != null && roic > 15) strengths.push(`Exceptional capital allocation with ${roic.toFixed(1)}% Return on Invested Capital.`);
    if (strengths.length < 3 && historicalCagr != null && historicalCagr > 10) strengths.push(`Compounded historical cash flow at ${historicalCagr.toFixed(1)}% annually.`);
    if (strengths.length < 3) strengths.push(`Established market leadership in ${data.identity.gics_sector || "industry"}.`);
  }

  const keyRisk =
    altmanZone === "Distress"
      ? `Elevated balance sheet distress (Altman Z: ${altmanZ?.toFixed(2) ?? "low"}). Monitor debt maturities.`
      : reverseDcfGap != null && reverseDcfGap > 5
      ? `Priced for high expectation: must accelerate FCF growth to ${impliedCagr?.toFixed(1)}% annually.`
      : `Exposure to cyclical demand, supply chain constraints, or foreign exchange shifts.`;

  const expectedReturn = impliedCagr != null ? Math.max(impliedCagr * 0.9 + 2.0, 5.0) : 9.5;

  return (
    <div className={`space-y-4 animate-fade-in ${className}`}>
      {/* Cockpit Header Card */}
      <div className="rounded-card border border-border bg-bg-1 p-5 shadow-card">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/70 pb-3 mb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-accent inline-block animate-pulse-subtle" />
              <h2 className="font-heading text-sm font-bold uppercase tracking-wider text-ink-0">
                Level 1: 60-Second Executive Cockpit
              </h2>
            </div>
            <p className="mt-0.5 text-xs text-ink-1 font-sans">
              Instant bottom-line decision filter for retail and professional research.
            </p>
          </div>
          <div className="text-right">
            <span className="font-mono text-[11px] text-ink-2">Pillar Confidence</span>
            <div className="font-mono text-xs font-semibold text-accent">
              {s?.coverage != null ? `${s.coverage}/4 Pillars Verified` : "Coverage Pending"}
            </div>
          </div>
        </div>

        {/* Bottom-Line Safety Verdict Banner & Bessembinder Base-Rate Panel (US-0676) */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
          <div className="rounded border border-border/80 bg-bg-0 p-4">
            <span className="block font-mono text-[10px] uppercase tracking-wider text-ink-2 mb-1.5 font-semibold">
              Bottom-Line Safety Verdict:
            </span>
            <VerdictBadge
              verdict={verdictObj.label}
              tone={verdictObj.tone}
              confidence={verdictObj.confidence}
            />
          </div>

          <div className="rounded border border-border/80 bg-bg-0 p-4 flex flex-col justify-between" data-testid="bessembinder-base-rate-panel">
            <div>
              <div className="flex items-center justify-between gap-2 mb-1.5">
                <span className="font-mono text-[10px] uppercase tracking-wider text-ink-2 font-semibold">
                  Empirical Base-Rate Humility (Bessembinder 2018/2024)
                </span>
                <span className="rounded bg-accent/10 px-1.5 py-0.5 font-mono text-[10px] font-medium text-accent">
                  42% Beat T-Bills
                </span>
              </div>
              <p className="text-xs text-ink-1 leading-relaxed">
                <strong className="text-ink-0">Base Rate:</strong> Only 42% of US common stocks beat 1-month T-Bills over their full lifetime; the median stock generates a cumulative lifetime return of -100% relative to T-Bills (Bessembinder 2018/2024).
              </p>
            </div>
            <div className="mt-2 pt-2 border-t border-border/50 text-[11px] text-ink-2 font-sans italic">
              "Single-stock outcomes are positively skewed. High conviction must be weighed against unconditional survival odds."
            </div>
          </div>
        </div>

        {/* 3 Traffic Light Tiles (Moat, Solvency, Valuation) */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <TrafficLightTile
            number={1}
            title="Business Moat & Quality"
            statusText={moatStatus}
            status={moatTone}
            description={
              roic != null && grossMargin != null
                ? `ROIC of ${roic.toFixed(1)}% and ${grossMargin.toFixed(1)}% gross margins indicate pricing power and ecosystem durability.`
                : `Moat durability based on pricing power, returns on capital, and market positioning.`
            }
            metrics={[
              { label: "ROIC", value: roic != null ? `${roic.toFixed(1)}%` : "0.00" },
              { label: "Gross Margin", value: grossMargin != null ? `${grossMargin.toFixed(1)}%` : "0.00" },
            ]}
          />

          <TrafficLightTile
            number={2}
            title="Financial Safety & Solvency"
            statusText={solvencyStatus}
            status={solvencyTone}
            description={
              isNetCash
                ? `Net cash balance of ${money(Math.abs(netDebt), cur)}. Negligible insolvency risk (Altman Z: ${altmanZ?.toFixed(2) ?? "Safe"}).`
                : `Net debt of ${money(netDebt, cur)} with ${altmanZone ?? "adequate"} solvency cushion.`
            }
            metrics={[
              { label: isNetCash ? "Net Cash" : "Net Debt", value: money(Math.abs(netDebt), cur) },
              { label: "Altman Z", value: altmanZ != null ? altmanZ.toFixed(2) : "0.00" },
            ]}
          />

          <TrafficLightTile
            number={3}
            title="Valuation & Growth Hurdle"
            statusText={valuationStatus}
            status={valuationTone}
            description={
              impliedCagr != null
                ? `Priced for ${impliedCagr.toFixed(1)}% FCF growth. Historical 5Y CAGR was ${historicalCagr != null ? `${historicalCagr.toFixed(1)}%` : "N/A"}.`
                : `Market expectations and cash flow valuation hurdle.`
            }
            metrics={[
              { label: "Implied 10Y CAGR", value: impliedCagr != null ? `${impliedCagr.toFixed(1)}%` : "0.00" },
              {
                label: "Trailing P/E",
                value:
                  pe != null
                    ? pe > 0
                      ? `${pe.toFixed(1)}x`
                      : `Loss (${pe.toFixed(1)}x)`
                    : typeof snap.diluted_eps === "number" && snap.diluted_eps < 0
                    ? `Deficit (EPS: ${snap.diluted_eps})`
                    : "Not reported in filing",
              },
            ]}
          />
        </div>
      </div>

      {/* The Market's Expectation (Reverse DCF Rule Box) */}
      <ReverseDcfRuleBox
        currentPrice={price}
        currency={cur}
        companyName={name}
        impliedCagr={impliedCagr}
        historicalCagr={historicalCagr}
      />

      {/* Plain-English Decision Summary with Equal-Billing Bear Case */}
      <DecisionBullets
        strengths={strengths}
        keyRisk={keyRisk}
        expectedReturn={expectedReturn}
        indexBaseline={8.0}
        currency={cur}
        bearCase={data.bear_case}
      />
    </div>
  );
}

export default ExecutiveCockpit;