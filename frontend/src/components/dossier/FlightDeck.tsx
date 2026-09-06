import type { DossierOut, PractitionerOut } from "../../api/types";
import PillarRadar from "../viz/PillarRadar";
import LynchArchetypeCard from "./LynchArchetypeCard";
import ShareholderYieldBar from "./ShareholderYieldBar";
import CashFlowWaterfall from "./CashFlowWaterfall";

export interface FlightDeckProps {
  data: DossierOut;
  practitioner?: PractitionerOut | null;
  className?: string;
}

export function FlightDeck({ data, practitioner, className = "" }: FlightDeckProps) {
  const snap = data.latest_snapshot ?? {};
  const cur = data.identity.currency || "USD";
  const s = data.score;

  // Lynch metrics
  const archetype = data.identity.custom_industry_sheet === "Banks"
    ? "FINANCIAL INSTITUTION"
    : (data.level2?.lynch_archetype?.archetype || data.archetype?.archetype || "STALWART COMPOUNDER");
  const epsGrowth5y = typeof snap.eps_5y_cagr === "number" ? snap.eps_5y_cagr : null;
  const pe = typeof snap.pe_calc === "number" ? snap.pe_calc : null;
  const peg = pe != null && epsGrowth5y != null && epsGrowth5y > 0 ? pe / epsGrowth5y : (data.archetype?.peg_ratio ?? null);

  // Capital Return / Shareholder Yield metrics
  const sy: any = practitioner?.shareholder_yield || data.level2?.true_shareholder_yield;
  const divYield = typeof snap.dividend_yield === "number" ? snap.dividend_yield * 100 : (sy?.dividend_yield_pct ?? null);
  const buybackYield = sy?.gross_buyback_yield_pct ?? (typeof snap.buyback_yield === "number" ? snap.buyback_yield * 100 : null);
  const buybackDollars = sy?.buyback_dollars ?? null;
  const sbcYield = sy?.sbc_drag_pct ?? null;
  const sbcDollars = sy?.sbc_dollars ?? null;
  const netFloatShrink = sy?.share_count_cagr_3y_pct ?? sy?.share_count_delta_1y_pct ?? null;

  // Cash Flow Waterfall metrics (pure data fidelity: never invent missing numbers)
  const rev = typeof snap.revenue === "number" ? snap.revenue : null;
  const gp = typeof snap.gross_profit === "number" ? snap.gross_profit : (typeof snap.revenue === "number" && typeof snap.gross_margin === "number" ? snap.revenue * snap.gross_margin : null);
  const ni = typeof snap.net_income === "number" ? snap.net_income : null;
  const cfo = typeof snap.operating_cash_flow === "number" ? snap.operating_cash_flow : null;
  const fcf = typeof snap.free_cash_flow === "number" ? snap.free_cash_flow : (typeof snap.fcf_calc === "number" ? snap.fcf_calc : null);
  const capex = typeof snap.capital_expenditures === "number" ? snap.capital_expenditures : (typeof snap.capex === "number" ? snap.capex : null);

  const ownerEarnings = ni != null && capex != null
    ? ni + (typeof snap.depreciation_and_amortization === "number" ? snap.depreciation_and_amortization : 0) - Math.abs(capex)
    : null;
  const ownerEarningsYield = ownerEarnings != null && typeof snap.enterprise_value === "number" && snap.enterprise_value > 0
    ? (ownerEarnings / snap.enterprise_value) * 100
    : null;

  return (
    <div className={`space-y-4 animate-fade-in ${className}`}>
      {/* Header Banner */}
      <div className="rounded-card border border-border bg-bg-1 p-4 shadow-card flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-accent inline-block animate-pulse-subtle" />
            <h2 className="font-heading text-sm font-bold uppercase tracking-wider text-ink-0">
              Level 2: 5-Minute Flight Deck
            </h2>
          </div>
          <p className="mt-0.5 text-xs text-ink-1">
            Visual factor radar, shareholder returns with SBC dilution, and cash conversion waterfall.
          </p>
        </div>
        <span className="font-mono text-xs text-ink-2 bg-bg-2 px-2.5 py-1 rounded-card border border-border">
          Telemetric View
        </span>
      </div>

      {/* Top Grid: 4-Pillar Radar & Lynch Archetype */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-5 rounded-card border border-border bg-bg-1 p-4 shadow-card flex flex-col justify-between">
          <div className="flex items-center justify-between border-b border-border/70 pb-2 mb-2">
            <span className="font-heading text-xs font-bold uppercase tracking-wider text-ink-0">
              4-Pillar Research Radar
            </span>
            <span className="font-mono text-[10px] text-accent">
              Composite: {s?.composite != null ? s.composite.toFixed(1) : "0.00"}/10
            </span>
          </div>
          <div className="my-auto py-2 flex justify-center">
            <PillarRadar
              quality={s?.pillars.quality ?? null}
              value={s?.pillars.value ?? null}
              growth={s?.pillars.growth ?? null}
              risk={s?.pillars.risk ?? null}
              size={240}
            />
          </div>
          <div className="text-[11px] font-mono text-ink-2 text-center border-t border-border/60 pt-2">
            Balanced factor geometry indicates multidimensional quality & low structural risk.
          </div>
        </div>

        <div className="lg:col-span-7">
          <LynchArchetypeCard
            archetype={archetype}
            epsGrowth5y={epsGrowth5y}
            peRatio={pe}
            pegRatio={peg}
            netIncome={ni}
            capex={capex}
            ownerEarnings={ownerEarnings}
            ownerEarningsYield={ownerEarningsYield}
            currency={cur}
          />
        </div>
      </div>

      {/* Bottom Grid: Shareholder Yield & Cash Flow Waterfall */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-6">
          <ShareholderYieldBar
            dividendYield={divYield}
            buybackYield={buybackYield}
            buybackDollars={buybackDollars}
            sbcDilutionYield={sbcYield}
            sbcDollars={sbcDollars}
            netFloatShrinkPct={netFloatShrink}
            currency={cur}
          />
        </div>

        <div className="lg:col-span-6">
          <CashFlowWaterfall
            revenue={rev}
            grossProfit={gp}
            netIncome={ni}
            cfo={cfo}
            fcf={fcf}
            currency={cur}
          />
        </div>
      </div>
    </div>
  );
}

export default FlightDeck;