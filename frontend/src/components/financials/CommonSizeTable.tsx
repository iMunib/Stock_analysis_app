import React, { useState } from "react";
import type { CommonSizeOut } from "../../api/types";
import { money } from "../../lib/format";
import { Card } from "../layout";

interface CommonSizeTableProps {
  data: CommonSizeOut | null | undefined;
  currency?: string | null;
  className?: string;
}

export const CommonSizeTable: React.FC<CommonSizeTableProps> = ({
  data,
  currency = "USD",
  className = "",
}) => {
  const [mode, setMode] = useState<"percent" | "raw">("percent");

  if (!data || (!data.income_statement_common_size.length && !data.balance_sheet_common_size.length)) {
    return (
      <Card title="Common-Size Financial Statements" subtitle="Normalized financial statements" padding="sm" className={className}>
        <div className="py-6 text-center text-xs text-ink-2">
          Multi-year common-size financial statements not available.
        </div>
      </Card>
    );
  }

  const isList = data.income_statement_common_size;
  const bsList = data.balance_sheet_common_size;

  const years = isList.map((row) => row.fiscal_year).filter(Boolean) as number[];

  const formatVal = (item: { raw: number | null; pct: number | null } | undefined) => {
    if (!item) return "Not reported in filing";
    if (mode === "percent") {
      if (item.pct == null) return "Not reported in filing";
      return `${item.pct.toFixed(1)}%`;
    } else {
      if (item.raw == null) return "Not reported in filing";
      return money(item.raw, currency || "USD");
    }
  };

  const isLineItems = [
    { label: "Total Revenue", key: "revenue", isBase: true },
    { label: "Gross Profit", key: "gross_profit" },
    { label: "Operating Income (EBIT)", key: "ebit" },
    { label: "EBITDA", key: "ebitda" },
    { label: "Net Income", key: "net_income" },
    { label: "Cash from Operations (CFO)", key: "cfo" },
    { label: "Capital Expenditures (CapEx)", key: "capex" },
    { label: "Free Cash Flow (FCF)", key: "fcf" },
    { label: "Operating Expenses (OpEx)", key: "opex" },
  ];

  const bsLineItems = [
    { label: "Total Assets", key: "total_assets", isBase: true },
    { label: "Cash & Short-Term Investments", key: "cash_st_investments" },
    { label: "Total Debt", key: "total_debt" },
    { label: "Total Liabilities", key: "total_liabilities" },
    { label: "Common Book Equity", key: "book_equity" },
    { label: "Net Debt", key: "net_debt" },
  ];

  return (
    <Card
      title="Common-Size Statements & Margin Drift"
      subtitle={`Normalized statement structure (${mode === "percent" ? "% of Revenue & Total Assets" : `Raw ${currency || "Currency"}`})`}
      padding="md"
      className={className}
      action={
        <div className="inline-flex rounded border border-border bg-surface-2 p-0.5 text-xs">
          <button
            type="button"
            onClick={() => setMode("percent")}
            className={`px-2.5 py-1 rounded font-medium transition-colors ${
              mode === "percent"
                ? "bg-surface-1 text-ink-0 shadow-sm"
                : "text-ink-2 hover:text-ink-0"
            }`}
          >
            % of Revenue / Assets
          </button>
          <button
            type="button"
            onClick={() => setMode("raw")}
            className={`px-2.5 py-1 rounded font-medium transition-colors ${
              mode === "raw"
                ? "bg-surface-1 text-ink-0 shadow-sm"
                : "text-ink-2 hover:text-ink-0"
            }`}
          >
            Raw Currency Units
          </button>
        </div>
      }
    >
      <div className="space-y-6">
        {/* Margin Drift Flags Banner */}
        {data.margin_drift_flags && data.margin_drift_flags.length > 0 && (
          <div className="space-y-2">
            <span className="text-[11px] font-mono uppercase tracking-wider text-ink-2 font-semibold">
              Margin Drift Warnings
            </span>
            <div className="flex flex-wrap gap-2">
              {data.margin_drift_flags.map((flag, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-2 px-3 py-1.5 rounded border border-warn/30 bg-warn-weak text-xs text-ink-0"
                >
                  <span className="inline-block w-2 h-2 rounded-full bg-warn" />
                  <span className="font-mono font-bold text-warn">{flag.code}</span>
                  <span>{flag.message}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Common-Size Income Statement */}
        <div>
          <h4 className="text-xs font-semibold text-ink-0 uppercase tracking-wider mb-2 flex items-center justify-between">
            <span>Income Statement ({mode === "percent" ? "% of Total Revenue" : currency || "USD"})</span>
            <span className="text-[10px] text-ink-2 font-mono font-normal">Fiscal Years Delivered: {data.years_delivered}</span>
          </h4>
          <div className="overflow-x-auto rounded border border-border">
            <table className="w-full text-xs text-left">
              <thead className="bg-surface-2 text-ink-2 border-b border-border font-mono text-[11px]">
                <tr>
                  <th className="py-2 px-3 font-semibold text-ink-1">Line Item</th>
                  {years.map((y) => (
                    <th key={y} className="py-2 px-3 text-right font-semibold text-ink-1">
                      FY{y}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border font-mono">
                {isLineItems.map((line) => (
                  <tr
                    key={line.key}
                    className={`hover:bg-surface-2/60 transition-colors ${
                      line.isBase ? "font-semibold bg-surface-2/30" : ""
                    }`}
                  >
                    <td className="py-2 px-3 font-sans text-ink-0">{line.label}</td>
                    {isList.map((row) => {
                      const item = row[line.key];
                      return (
                        <td key={row.fiscal_year} className="py-2 px-3 text-right text-ink-1">
                          {formatVal(item)}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Common-Size Balance Sheet */}
        <div>
          <h4 className="text-xs font-semibold text-ink-0 uppercase tracking-wider mb-2">
            Balance Sheet ({mode === "percent" ? "% of Total Assets" : currency || "USD"})
          </h4>
          <div className="overflow-x-auto rounded border border-border">
            <table className="w-full text-xs text-left">
              <thead className="bg-surface-2 text-ink-2 border-b border-border font-mono text-[11px]">
                <tr>
                  <th className="py-2 px-3 font-semibold text-ink-1">Line Item</th>
                  {years.map((y) => (
                    <th key={y} className="py-2 px-3 text-right font-semibold text-ink-1">
                      FY{y}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border font-mono">
                {bsLineItems.map((line) => (
                  <tr
                    key={line.key}
                    className={`hover:bg-surface-2/60 transition-colors ${
                      line.isBase ? "font-semibold bg-surface-2/30" : ""
                    }`}
                  >
                    <td className="py-2 px-3 font-sans text-ink-0">{line.label}</td>
                    {bsList.map((row) => {
                      const item = row[line.key];
                      return (
                        <td key={row.fiscal_year} className="py-2 px-3 text-right text-ink-1">
                          {formatVal(item)}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default CommonSizeTable;