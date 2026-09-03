import React from "react";
import type { ShareholderYield } from "../../api/types";
import { Card } from "../layout";

interface CapitalReturnCardProps {
  data: ShareholderYield | null | undefined;
  className?: string;
}

export const CapitalReturnCard: React.FC<CapitalReturnCardProps> = ({
  data,
  className = "",
}) => {
  if (!data) {
    return (
      <Card
        title="Capital Return & Share Dilution"
        subtitle="Multi-year share count trajectory and true shareholder yield"
        padding="sm"
        className={className}
      >
        <div className="py-6 text-center text-xs text-ink-2">
          Capital return and share count history unavailable.
        </div>
      </Card>
    );
  }

  const history = data.share_count_history || [];
  const maxShares = Math.max(...history.map((h) => h.diluted_shares), 1);
  const minShares = Math.min(...history.map((h) => h.diluted_shares), maxShares * 0.8);
  const range = maxShares - minShares || 1;

  const flags = data.flags || [];
  const isDilution = flags.includes("SHAREHOLDER_DILUTION");
  const isBuybacks = flags.includes("ACCELERATED_BUYBACKS");
  const isOrganicShrink = flags.includes("ORGANIC_FLOAT_SHRINK");
  const isDilutiveBuybacks = flags.includes("DILUTIVE_BUYBACKS");

  const grossBuyback = data.gross_buyback_yield_pct ?? (data.net_repurchase_rate_pct != null && data.net_repurchase_rate_pct > 0 ? data.net_repurchase_rate_pct : 0);
  const sbcOffset = data.sbc_dilution_offset_pct ?? 0;
  const netBuyback = data.net_buyback_yield_pct ?? (grossBuyback - sbcOffset);
  const trueYield = data.true_shareholder_yield_pct ?? data.total_shareholder_yield_pct ?? 0;

  return (
    <Card
      title="Capital Return & Share Dilution"
      subtitle="Multi-year share count trajectory and true shareholder yield"
      padding="md"
      className={className}
    >
      <div className="space-y-6">
        {/* Core Yield Summary */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <div className="p-3 rounded border border-border bg-surface-2">
            <span className="text-[11px] text-ink-2 uppercase tracking-wider font-mono">
              Dividend Yield
            </span>
            <div className="font-mono text-xl font-bold text-ink-0 mt-1">
              {data.dividend_yield_pct != null ? `${data.dividend_yield_pct.toFixed(2)}%` : "0.00%"}
            </div>
            <span className="text-[10px] text-ink-2">Annualized cash payout</span>
          </div>

          <div className="p-3 rounded border border-border bg-surface-2">
            <span className="text-[11px] text-ink-2 uppercase tracking-wider font-mono">
              Net Buyback Yield
            </span>
            <div className={`font-mono text-xl font-bold mt-1 ${
              (netBuyback || 0) > 0 ? "text-pos" : (netBuyback || 0) < 0 ? "text-neg" : "text-ink-0"
            }`}>
              {netBuyback != null
                ? `${netBuyback > 0 ? "+" : ""}${netBuyback.toFixed(2)}%`
                : "—"}
            </div>
            <span className="text-[10px] text-ink-2">Buybacks less SBC dilution</span>
          </div>

          <div className="p-3 rounded border border-border bg-surface-2">
            <span className="text-[11px] text-ink-2 uppercase tracking-wider font-mono">
              SBC Drag (% Rev)
            </span>
            <div className={`font-mono text-xl font-bold mt-1 ${
              (data.sbc_drag_pct || 0) > 4.0 ? "text-warn" : "text-ink-0"
            }`}>
              {data.sbc_drag_pct != null ? `${data.sbc_drag_pct.toFixed(1)}%` : "—"}
            </div>
            <span className="text-[10px] text-ink-2">Stock comp burden on topline</span>
          </div>

          <div className="p-3 rounded border border-pos/30 bg-pos-weak">
            <span className="text-[11px] text-pos uppercase tracking-wider font-mono font-semibold">
              True Shareholder Yield
            </span>
            <div className="font-mono text-xl font-bold text-pos mt-1">
              {trueYield != null ? `${trueYield.toFixed(2)}%` : "—"}
            </div>
            <span className="text-[10px] text-ink-1">Total Shareholder Yield (Dividends + Net Repurchases)</span>
          </div>
        </div>

        {/* Buyback vs SBC Dilution Decomposition Bar */}
        <div className="rounded-lg border border-border bg-surface-1 p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-ink-0 uppercase tracking-wider">
              Shareholder Return Decomposition (Yield vs SBC Offset)
            </span>
            <span className="font-mono text-xs text-ink-2">
              Gross: {grossBuyback.toFixed(2)}% | SBC Offset: -{sbcOffset.toFixed(2)}%
            </span>
          </div>
          <div className="h-4 w-full bg-surface-2 rounded-full overflow-hidden flex border border-border">
            <div
              style={{ width: `${Math.min(100, Math.max(0, grossBuyback * 12))}%` }}
              className="bg-pos/80 h-full transition-all"
              title={`Gross Buyback Yield: ${grossBuyback.toFixed(2)}%`}
            />
            <div
              style={{ width: `${Math.min(100, Math.max(0, sbcOffset * 12))}%` }}
              className="bg-warn/80 h-full transition-all"
              title={`SBC Dilution Offset: ${sbcOffset.toFixed(2)}%`}
            />
          </div>
          <div className="flex items-center justify-between text-[11px] text-ink-2 mt-2 font-mono">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-pos/80 inline-block" />
              <span>Gross Repurchases</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-warn/80 inline-block" />
              <span>SBC Dilution Offset</span>
            </div>
            <div className="flex items-center gap-1.5 font-semibold text-ink-0">
              <span>Net Repurchase Rate: {data.net_repurchase_rate_pct != null ? `${data.net_repurchase_rate_pct.toFixed(2)}%` : "—"}</span>
            </div>
          </div>
        </div>

        {/* Flags & Trajectory Status */}
        <div className="flex flex-wrap items-center gap-2">
          {isOrganicShrink && (
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-pos-weak text-pos border border-pos/30">
              <span className="inline-block w-2 h-2 rounded-full bg-pos" />
              ORGANIC FLOAT SHRINK (Net Repurchase &gt; 2% &amp; Low SBC)
            </span>
          )}
          {isDilutiveBuybacks && (
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-warn-weak text-warn border border-warn/30">
              <span className="inline-block w-2 h-2 rounded-full bg-warn" />
              DILUTIVE BUYBACKS (Grants exceeding net share retirement)
            </span>
          )}
          {isDilution && (
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-neg-weak text-neg border border-neg/30">
              <span className="inline-block w-2 h-2 rounded-full bg-neg" />
              SHAREHOLDER DILUTION (&gt;2% annual expansion)
            </span>
          )}
          {isBuybacks && !isOrganicShrink && (
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-pos-weak text-pos border border-pos/30">
              <span className="inline-block w-2 h-2 rounded-full bg-pos" />
              ACCELERATED BUYBACKS (&gt;2% annual contraction)
            </span>
          )}
          {!isDilution && !isBuybacks && !isOrganicShrink && !isDilutiveBuybacks && (
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-surface-2 text-ink-1 border border-border">
              Stable Share Count
            </span>
          )}

          <div className="text-xs text-ink-2 ml-auto font-mono">
            <span>1Y Δ: </span>
            <strong className="text-ink-0">
              {data.share_count_delta_1y_pct != null
                ? `${data.share_count_delta_1y_pct > 0 ? "+" : ""}${data.share_count_delta_1y_pct.toFixed(2)}%`
                : "—"}
            </strong>
            <span className="mx-2">·</span>
            <span>3Y CAGR: </span>
            <strong className="text-ink-0">
              {data.share_count_cagr_3y_pct != null
                ? `${data.share_count_cagr_3y_pct > 0 ? "+" : ""}${data.share_count_cagr_3y_pct.toFixed(2)}%`
                : "—"}
            </strong>
          </div>
        </div>

        {/* Multi-Year Share Count SVG Bar Chart */}
        {history.length > 0 && (
          <div>
            <span className="text-xs font-semibold text-ink-0 uppercase tracking-wider block mb-2">
              Diluted Shares Outstanding Trajectory
            </span>
            <div className="p-4 rounded border border-border bg-surface-1" role="img" aria-label="Diluted shares outstanding trend">
              <div className="h-32 flex items-end justify-between gap-4">
                {history.map((item) => {
                  const normalizedHeightPct = 20 + ((item.diluted_shares - minShares) / range) * 80;
                  const formattedMillions = (item.diluted_shares / 1_000_000).toFixed(1);

                  return (
                    <div key={item.fiscal_year} className="flex-1 flex flex-col items-center gap-1.5 group">
                      <span className="font-mono text-[10px] text-ink-2 group-hover:text-ink-0 transition-colors">
                        {formattedMillions}M
                      </span>
                      <div className="w-full max-w-[48px] bg-surface-2 rounded-t overflow-hidden relative border-t border-x border-border/80 h-full flex items-end">
                        <div
                          style={{ height: `${normalizedHeightPct}%` }}
                          className={`w-full rounded-t transition-all duration-300 ${
                            isBuybacks || isOrganicShrink
                              ? "bg-pos/80 group-hover:bg-pos"
                              : isDilution
                                ? "bg-neg/80 group-hover:bg-neg"
                                : "bg-accent/80 group-hover:bg-accent"
                          }`}
                        />
                      </div>
                      <span className="font-mono text-xs font-semibold text-ink-1">
                        FY{item.fiscal_year}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};

export default CapitalReturnCard;
