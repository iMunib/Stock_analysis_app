import React, { useState } from "react";
import type { HalalPayload } from "../../api/types";
import { halalCopy } from "../../api/copy";
import { Card } from "../layout";
import { HalalBadge } from "../ui";

interface HalalComplianceCardProps {
  halal: HalalPayload | null | undefined;
  className?: string;
}

export const HalalComplianceCard: React.FC<HalalComplianceCardProps> = ({
  halal,
  className = "",
}) => {
  const [detailsOpen, setDetailsOpen] = useState(false);

  if (!halal) {
    return (
      <Card
        title="Halal Screening (AAOIFI)"
        subtitle="Shariah governance & ethical compliance flag"
        padding="sm"
        className={className}
      >
        <div className="py-3 text-xs text-ink-2 font-mono">
          Halal screening data not available for this company.
        </div>
      </Card>
    );
  }

  const isCandidate = halal.status === "halal_candidate";
  const isNotHalal = halal.status === "not_halal";
  const failedCount = halal.failed_tests?.length || 0;

  return (
    <Card
      title="Halal Screening (AAOIFI Standard 21)"
      subtitle="Deterministic ethical filter based on business activities and debt/cash ratios"
      action={
        <button
          type="button"
          onClick={() => setDetailsOpen(!detailsOpen)}
          className="text-xs font-mono text-accent hover:underline flex items-center gap-1"
        >
          <span>{detailsOpen ? "Hide Criteria" : "Inspect Criteria"}</span>
          <span>{detailsOpen ? "▲" : "▼"}</span>
        </button>
      }
      padding="md"
      className={className}
    >
      <div className="space-y-4">
        {/* Top Status Banner */}
        <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-card bg-bg-2/50 border border-border">
          <div className="flex items-center gap-2.5">
            <HalalBadge status={halal.status} />
            <span className="text-xs text-ink-1 leading-relaxed">
              {halalCopy(halal.status)}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-[11px] text-ink-2">
              Method: <span className="text-ink-0 font-semibold">{halal.method || "AAOIFI-21"}</span>
            </span>
            {failedCount > 0 && (
              <span className="rounded-chip bg-neg-weak border border-neg/30 px-2 py-0.5 font-mono text-[10px] text-neg font-semibold">
                {failedCount} {failedCount === 1 ? "flag" : "flags"}
              </span>
            )}
          </div>
        </div>

        {/* 3 Core AAOIFI Screening Pillars (Visual Gauges) */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {/* Screen 1: Business Activity */}
          <div className="p-3 rounded border border-border bg-bg-0 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono uppercase tracking-wider text-ink-2">1. Business Activity</span>
              <span
                className={`h-2 w-2 rounded-full ${
                  isNotHalal ? "bg-neg animate-pulse" : isCandidate ? "bg-pos" : "bg-ink-2"
                }`}
              />
            </div>
            <div className="mt-2">
              <div className="font-mono text-sm font-bold text-ink-0">
                {isNotHalal ? "Flagged Non-Permissible" : isCandidate ? "Pass (<5% non-core)" : "Pending Review"}
              </div>
              <p className="text-[11px] text-ink-2 mt-0.5">
                Excludes conventional banking/interest, alcohol, gambling, adult content, defense weapons.
              </p>
            </div>
          </div>

          {/* Screen 2: Debt / Market Cap */}
          <div className="p-3 rounded border border-border bg-bg-0 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono uppercase tracking-wider text-ink-2">2. Debt / Market Cap</span>
              <span
                className={`h-2 w-2 rounded-full ${
                  halal.failed_tests?.some((t) => t.test.toLowerCase().includes("debt"))
                    ? "bg-neg"
                    : isCandidate
                    ? "bg-pos"
                    : "bg-ink-2"
                }`}
              />
            </div>
            <div className="mt-2">
              <div className="font-mono text-sm font-bold text-ink-0">
                Threshold: &lt; 30.0%
              </div>
              <p className="text-[11px] text-ink-2 mt-0.5">
                Interest-bearing debt divided by 36-month trailing average market cap.
              </p>
            </div>
          </div>

          {/* Screen 3: Cash & Securities / Market Cap */}
          <div className="p-3 rounded border border-border bg-bg-0 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono uppercase tracking-wider text-ink-2">3. Cash & Securities</span>
              <span
                className={`h-2 w-2 rounded-full ${
                  halal.failed_tests?.some((t) => t.test.toLowerCase().includes("cash"))
                    ? "bg-neg"
                    : isCandidate
                    ? "bg-pos"
                    : "bg-ink-2"
                }`}
              />
            </div>
            <div className="mt-2">
              <div className="font-mono text-sm font-bold text-ink-0">
                Threshold: &lt; 30.0%
              </div>
              <p className="text-[11px] text-ink-2 mt-0.5">
                Cash and interest-bearing deposits divided by market capitalization.
              </p>
            </div>
          </div>
        </div>

        {/* Failed Tests Transparency Drilldown */}
        {failedCount > 0 && (
          <div className="rounded border border-neg/40 bg-neg-weak/30 p-3 space-y-1.5">
            <div className="flex items-center gap-1.5 font-mono text-xs font-semibold text-neg">
              <span>⚠️</span>
              <span>Failed Compliance Criteria ({failedCount}):</span>
            </div>
            <ul className="divide-y divide-border/60">
              {halal.failed_tests.map((f, i) => {
                let ratioText: string | null = null;
                if (f.ratio != null) {
                  if (typeof f.ratio === "number") {
                    ratioText = `${(f.ratio * 100).toFixed(1)}%`;
                  } else if (typeof f.ratio === "object" && f.ratio !== null) {
                    const rObj = f.ratio as Record<string, any>;
                    const rVal = typeof rObj.ratio === "number" ? rObj.ratio : typeof rObj.value === "number" ? rObj.value : null;
                    const limVal = typeof rObj.limit === "number" ? rObj.limit : typeof rObj.threshold === "number" ? rObj.threshold : null;
                    if (rVal != null) {
                      ratioText = `${(rVal * 100).toFixed(1)}%${limVal != null ? ` (limit ${(limVal * 100).toFixed(0)}%)` : ""}`;
                    }
                  } else if (typeof f.ratio === "string") {
                    ratioText = f.ratio;
                  }
                }

                let basisText: string | null = null;
                if (f.basis != null && typeof f.basis === "object") {
                  const bObj = f.basis as Record<string, any>;
                  if (bObj.keyword_hit) {
                    basisText = `Hit: "${bObj.keyword_hit}"`;
                  } else if (bObj.gics_sector || bObj.custom_industry_sheet) {
                    basisText = `${bObj.gics_sector || bObj.custom_industry_sheet}`;
                  }
                }

                const testLabel =
                  f.test === "activity_screen"
                    ? "Non-Permissible Business Activity"
                    : f.test === "debt_to_mcap"
                    ? "Debt / Market Cap Ratio (>30%)"
                    : f.test === "cash_to_mcap"
                    ? "Cash & Securities / Market Cap (>30%)"
                    : f.test === "impure_income"
                    ? "Impure / Interest Income Ratio (>5%)"
                    : f.test;

                return (
                  <li key={i} className="py-1.5 flex flex-wrap items-center justify-between gap-2 text-xs font-mono">
                    <span className="text-ink-0 font-medium">{testLabel}</span>
                    <div className="flex items-center gap-2">
                      {basisText && <span className="text-ink-2 text-[11px]">{basisText}</span>}
                      {ratioText && <span className="text-neg font-bold">Ratio: {ratioText}</span>}
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>
        )}

        {/* Detailed Methodology Disclosure */}
        {detailsOpen && (
          <div className="rounded border border-border bg-bg-2/40 p-3.5 space-y-2 text-xs text-ink-1">
            <h4 className="font-heading font-semibold text-ink-0">AAOIFI Screening Protocol Rules</h4>
            <p className="leading-relaxed">
              1. <strong>Sector Exclusions:</strong> Conventional financial institutions, insurance providers (Takaful excepted), gambling, alcohol breweries, pork processing, and defense contracting.
            </p>
            <p className="leading-relaxed">
              2. <strong>Financial Ratio Screens:</strong> Total interest-bearing debt must not exceed 30% of market capitalization; Cash and interest-bearing investments must not exceed 30% of market capitalization.
            </p>
            <p className="leading-relaxed">
              3. <strong>Dividend Purification:</strong> If impure income is below 5%, the stock remains permissible with dividend purification required for the non-permissible fraction.
            </p>
          </div>
        )}

        <p className="text-[10px] font-mono text-ink-2 border-t border-border pt-2">
          Personal research software. Informational research flag (AAOIFI standard), not an official fatwa or religious ruling.
        </p>
      </div>
    </Card>
  );
};

export default HalalComplianceCard;
