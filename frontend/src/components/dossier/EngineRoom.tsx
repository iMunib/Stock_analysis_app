import type { CommonSizeOut, DossierOut, PractitionerOut } from "../../api/types";
import BeneishMatrix from "./BeneishMatrix";
import PenmanDecompositionTable from "./PenmanDecompositionTable";
import AltmanZScoreCard from "./AltmanZScoreCard";
import FridsonRealitySpread from "./FridsonRealitySpread";
import CommonSizeTable from "../financials/CommonSizeTable";

export interface EngineRoomProps {
  data: DossierOut;
  practitioner?: PractitionerOut | null;
  commonSize?: CommonSizeOut | null;
  className?: string;
}

export function EngineRoom({
  data,
  practitioner,
  commonSize,
  className = "",
}: EngineRoomProps) {
  const snap = data.latest_snapshot ?? {};
  const cur = data.identity.currency || "USD";

  // Beneish analysis
  const beneishData = data.level3?.beneish_matrix ?? practitioner?.beneish_analysis ?? (practitioner as any)?.beneish ?? null;

  // Penman metrics
  const penmanData: any = data.level3?.penman_table ?? practitioner?.penman;
  const rnoa = penmanData?.rnoa ?? (typeof snap.roic === "number" ? snap.roic : null);
  const flev = penmanData?.flev ?? null;
  const nbc = penmanData?.nbc ?? null;
  const spread = penmanData?.roe_operational_spread ?? (rnoa != null && nbc != null ? rnoa - nbc : null);
  const roe = typeof snap.roe === "number" ? snap.roe : (rnoa != null && flev != null && spread != null ? rnoa + flev * spread : null);
  const distortionAlert = penmanData?.guardrail?.flag ?? penmanData?.distortion_alert ?? (penmanData?.exclusion ?? null);

  // Altman Z metrics
  const distressData = data.level3?.altman_breakdown ?? practitioner?.distress_analysis;
  const zScore = distressData?.active_z ?? distressData?.z_score ?? (typeof snap.altman_z === "number" ? snap.altman_z : null);
  const altmanZone = distressData?.zone ?? (zScore != null ? (zScore > 2.99 ? "Safe" : zScore < 1.81 ? "Distress" : "Grey") : null);
  const x1 = distressData?.factors?.x1_working_capital_to_ta ?? null;
  const x2 = distressData?.factors?.x2_retained_earnings_to_ta ?? null;
  const x3 = distressData?.factors?.x3_ebit_to_ta ?? null;
  const x4 = distressData?.factors?.x4_market_equity_to_tl ?? null;
  const x5 = distressData?.factors?.x5_sales_to_ta ?? null;

  // Fridson reality spread metrics
  const ebitda = practitioner?.fridson?.ebitda ?? (typeof snap.ebitda === "number" ? snap.ebitda : null);
  const cfo = practitioner?.fridson?.cfo ?? (typeof snap.operating_cash_flow === "number" ? snap.operating_cash_flow : null);

  return (
    <div className={`space-y-4 animate-fade-in ${className}`}>
      {/* Header Banner */}
      <div className="rounded-card border border-border bg-bg-1 p-4 shadow-card flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-accent inline-block animate-pulse-subtle" />
            <h2 className="font-heading text-sm font-bold uppercase tracking-wider text-ink-0">
              Level 3: Institutional Engine Room
            </h2>
          </div>
          <p className="mt-0.5 text-xs text-ink-1">
            Forensic manipulation matrix, Penman economic reformulation, Altman Z solvency suite, and 10-year common-size filings.
          </p>
        </div>
        <span className="font-mono text-xs text-ink-2 bg-bg-2 px-2.5 py-1 rounded-card border border-border">
          Forensic Grade
        </span>
      </div>

      {/* Grid 1: Beneish 8-Variable Matrix & Penman Decomposition */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-7">
          <BeneishMatrix analysis={beneishData} />
        </div>
        <div className="lg:col-span-5">
          <PenmanDecompositionTable
            rnoa={rnoa}
            flev={flev}
            nbc={nbc}
            spread={spread}
            roe={roe}
            distortionAlert={distortionAlert}
          />
        </div>
      </div>

      {/* Grid 2: Altman Z-Score Suite & Fridson Reality Spread */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-7">
          <AltmanZScoreCard
            zScore={zScore}
            zone={altmanZone}
            x1={x1}
            x2={x2}
            x3={x3}
            x4={x4}
            x5={x5}
          />
        </div>
        <div className="lg:col-span-5">
          <FridsonRealitySpread
            ebitda={ebitda}
            cfo={cfo}
            currency={cur}
          />
        </div>
      </div>

      {/* Common Size Historical Statements Table */}
      <div className="pt-2">
        <CommonSizeTable data={commonSize} currency={cur} />
      </div>
    </div>
  );
}

export default EngineRoom;
