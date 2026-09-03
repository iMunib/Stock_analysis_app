import React from "react";
import type { DossierOut, PractitionerOut, CommonSizeOut } from "../../api/types";
import { money, multiple, percentish } from "../../lib/format";

interface FactsheetPrintViewProps {
  dossier: DossierOut;
  practitioner?: PractitionerOut | null;
  commonSize?: CommonSizeOut | null;
  onClose?: () => void;
}

export const FactsheetPrintView: React.FC<FactsheetPrintViewProps> = ({
  dossier,
  practitioner,
  commonSize,
  onClose,
}) => {
  const comp = dossier.identity;
  const snap = (dossier.latest_snapshot || {}) as Record<string, any>;
  const score = dossier.score;
  const cur = comp.currency || "USD";

  const altman = practitioner?.distress_analysis;
  const beneish = practitioner?.beneish_analysis;
  const penman = practitioner?.penman;
  const sy = practitioner?.shareholder_yield;

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="bg-white text-slate-900 font-sans p-6 max-w-4xl mx-auto print:p-0 print:max-w-none">
      {/* Non-printed Toolbar */}
      <div className="no-print flex items-center justify-between pb-4 mb-6 border-b border-slate-200">
        <div>
          <h2 className="text-lg font-bold text-slate-900">Institutional Equity Research Factsheet</h2>
          <p className="text-xs text-slate-500">Print or export 2-page research memorandum (8.5" x 11" PDF optimized)</p>
        </div>
        <div className="flex items-center gap-3">
          {onClose && (
            <button
              onClick={onClose}
              className="px-3 py-1.5 rounded text-xs font-semibold border border-slate-300 text-slate-700 hover:bg-slate-50"
            >
              Close View
            </button>
          )}
          <button
            onClick={handlePrint}
            className="px-4 py-1.5 rounded text-xs font-semibold bg-blue-600 text-white hover:bg-blue-700 shadow-sm flex items-center gap-1.5"
          >
            <span>🖨️</span> Print Factsheet (PDF)
          </button>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* PAGE 1: EXECUTIVE OVERVIEW, 4-PILLAR RADAR & CORE FINANCIALS              */}
      {/* ========================================================================= */}
      <div className="print-page border border-slate-300 print:border-none p-6 rounded-xl bg-white mb-8 print:mb-0 print:break-after-page">
        {/* Header Ribbon */}
        <div className="flex items-start justify-between border-b-2 border-slate-900 pb-3">
          <div>
            <div className="flex items-baseline gap-2">
              <h1 className="text-2xl font-black tracking-tight text-slate-950">{comp.ticker}</h1>
              <span className="text-sm font-semibold text-slate-600">{comp.name}</span>
              <span className="text-xs px-2 py-0.5 rounded font-mono bg-slate-100 text-slate-700 border border-slate-200">
                {comp.country}
              </span>
            </div>
            <div className="text-xs text-slate-500 mt-0.5">
              {comp.gics_sector} &bull; {comp.custom_industry_sheet || comp.gics_industry} &bull; Reporting Currency: {cur}
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs uppercase tracking-wider text-slate-400 font-bold">Research Signal</div>
            <div className="text-xl font-black text-blue-700">
              {score?.signal || "NEUTRAL"}
            </div>
            <div className="text-xs font-mono font-semibold text-slate-600">
              Composite: {score?.composite != null ? score.composite.toFixed(1) : "—"} / 10.0
            </div>
          </div>
        </div>

        {/* Executive Summary Bar */}
        <div className="grid grid-cols-4 gap-3 my-4 p-3 bg-slate-50 rounded-lg border border-slate-200 text-center">
          <div>
            <span className="text-[10px] uppercase font-bold text-slate-500">Price</span>
            <div className="text-base font-bold font-mono text-slate-900">{money(snap.price, cur)}</div>
          </div>
          <div>
            <span className="text-[10px] uppercase font-bold text-slate-500">Market Cap</span>
            <div className="text-base font-bold font-mono text-slate-900">{money(snap.market_cap, cur)}</div>
          </div>
          <div>
            <span className="text-[10px] uppercase font-bold text-slate-500">P/E Ratio</span>
            <div className="text-base font-bold font-mono text-slate-900">{multiple(snap.pe_calc)}</div>
          </div>
          <div>
            <span className="text-[10px] uppercase font-bold text-slate-500">EV/EBITDA</span>
            <div className="text-base font-bold font-mono text-slate-900">{multiple(snap.ev_to_ebitda_calc)}</div>
          </div>
        </div>

        {/* 4-Pillar Score Decomposition */}
        <div className="mb-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 mb-2 border-b border-slate-200 pb-1">
            4-Pillar Fundamental Framework (MATH v1)
          </h3>
          <div className="grid grid-cols-4 gap-3">
            {[
              { name: "Quality (30%)", val: score?.pillars?.quality },
              { name: "Value (25%)", val: score?.pillars?.value },
              { name: "Growth (25%)", val: score?.pillars?.growth },
              { name: "Solvency / Risk (20%)", val: score?.pillars?.risk },
            ].map((p) => (
              <div key={p.name} className="p-2.5 rounded border border-slate-200 bg-white">
                <div className="text-[11px] font-semibold text-slate-600">{p.name}</div>
                <div className="text-lg font-bold font-mono text-slate-900 mt-0.5">
                  {p.val != null ? `${p.val.toFixed(1)} / 10` : "—"}
                </div>
                <div className="w-full bg-slate-100 rounded-full h-1.5 mt-1 overflow-hidden">
                  <div
                    className="bg-blue-600 h-full rounded-full"
                    style={{ width: `${Math.min(100, Math.max(0, (p.val || 0) * 10))}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Key Financial Health & Ratios */}
        <div className="mb-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 mb-2 border-b border-slate-200 pb-1">
            Fundamental Financial Snapshot ({cur})
          </h3>
          <table className="w-full text-xs text-left">
            <tbody>
              <tr className="border-b border-slate-100">
                <td className="py-1 font-semibold text-slate-600">Total Revenue</td>
                <td className="py-1 font-mono text-right text-slate-900">{money(snap.revenue, cur)}</td>
                <td className="py-1 pl-4 font-semibold text-slate-600">Gross Margin</td>
                <td className="py-1 font-mono text-right text-slate-900">{percentish(snap.grossmargin_calc)}</td>
              </tr>
              <tr className="border-b border-slate-100">
                <td className="py-1 font-semibold text-slate-600">Operating Cash Flow (CFO)</td>
                <td className="py-1 font-mono text-right text-slate-900">{money(snap.operating_cash_flow, cur)}</td>
                <td className="py-1 pl-4 font-semibold text-slate-600">FCF Margin</td>
                <td className="py-1 font-mono text-right text-slate-900">{percentish(snap.fcfmargin_calc)}</td>
              </tr>
              <tr className="border-b border-slate-100">
                <td className="py-1 font-semibold text-slate-600">Free Cash Flow (FCF)</td>
                <td className="py-1 font-mono text-right text-slate-900">
                  {money((snap.free_cash_flow as number | null) ?? (snap.fcf_calc as number | null), cur)}
                </td>
                <td className="py-1 pl-4 font-semibold text-slate-600">Return on Equity (ROE)</td>
                <td className="py-1 font-mono text-right text-slate-900">{percentish(snap.roe_calc)}</td>
              </tr>
              <tr className="border-b border-slate-100">
                <td className="py-1 font-semibold text-slate-600">Net Debt</td>
                <td className="py-1 font-mono text-right text-slate-900">{money(snap.netdebt_calc, cur)}</td>
                <td className="py-1 pl-4 font-semibold text-slate-600">Return on Assets (ROA)</td>
                <td className="py-1 font-mono text-right text-slate-900">{percentish(snap.roa_calc)}</td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Forensic & Solvency Verification Matrix */}
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 mb-2 border-b border-slate-200 pb-1">
            Forensic Accounting & Solvency Verification
          </h3>
          <div className="grid grid-cols-4 gap-3 text-center">
            <div className="p-2.5 rounded border border-slate-200 bg-slate-50">
              <span className="text-[10px] uppercase font-bold text-slate-500">Altman Z-Score</span>
              <div className="text-sm font-bold font-mono text-slate-900 mt-0.5">
                {altman?.z_score != null ? altman.z_score.toFixed(2) : "—"}
              </div>
              <span className={`text-[10px] font-semibold ${altman?.zone === "Safe" ? "text-green-600" : "text-amber-600"}`}>
                {altman?.zone || "Unrated"}
              </span>
            </div>

            <div className="p-2.5 rounded border border-slate-200 bg-slate-50">
              <span className="text-[10px] uppercase font-bold text-slate-500">Beneish M-Score</span>
              <div className="text-sm font-bold font-mono text-slate-900 mt-0.5">
                {beneish?.m_score != null ? beneish.m_score.toFixed(2) : "—"}
              </div>
              <span className={`text-[10px] font-semibold ${beneish?.is_manipulator ? "text-red-600" : "text-green-600"}`}>
                {beneish?.zone || "Normal"}
              </span>
            </div>

            <div className="p-2.5 rounded border border-slate-200 bg-slate-50">
              <span className="text-[10px] uppercase font-bold text-slate-500">Penman RNOA</span>
              <div className="text-sm font-bold font-mono text-slate-900 mt-0.5">
                {penman?.rnoa != null ? `${(penman.rnoa * 100).toFixed(1)}%` : "—"}
              </div>
              <span className="text-[10px] text-slate-500 font-mono">
                FLEV: {penman?.flev != null ? penman.flev.toFixed(2) : "—"}
              </span>
            </div>

            <div className="p-2.5 rounded border border-slate-200 bg-slate-50">
              <span className="text-[10px] uppercase font-bold text-slate-500">True Shareholder Yield</span>
              <div className="text-sm font-bold font-mono text-slate-900 mt-0.5">
                {sy?.true_shareholder_yield_pct != null ? `${sy.true_shareholder_yield_pct.toFixed(2)}%` : "—"}
              </div>
              <span className="text-[10px] text-slate-500">
                SBC Drag: {sy?.sbc_drag_pct != null ? `${sy.sbc_drag_pct.toFixed(1)}%` : "—"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* PAGE 2: MULTI-YEAR COMMON SIZE, REVERSE DCF & LOCAL THESIS CHECKLIST      */}
      {/* ========================================================================= */}
      <div className="print-page border border-slate-300 print:border-none p-6 rounded-xl bg-white">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-200 pb-2 mb-4">
          <span className="text-xs font-bold text-slate-600 uppercase tracking-wider">
            {comp.ticker} &bull; Longitudinal Statements &amp; Valuation Expectations
          </span>
          <span className="text-xs text-slate-400 font-mono">Page 2 of 2</span>
        </div>

        {/* 5-Year Common-Size History */}
        {commonSize && commonSize.income_statement_common_size && commonSize.income_statement_common_size.length > 0 && (
          <div className="mb-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 mb-2 border-b border-slate-200 pb-1">
              5-Year Common-Size Income Statement (% of Revenue)
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-500 font-mono">
                    <th className="py-1">Metric</th>
                    {commonSize.income_statement_common_size.map((col) => (
                      <th key={col.fiscal_year} className="py-1 text-right">
                        FY{col.fiscal_year}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  <tr>
                    <td className="py-1 font-semibold text-slate-700">Gross Margin</td>
                    {commonSize.income_statement_common_size.map((col) => (
                      <td key={col.fiscal_year} className="py-1 text-right font-mono">
                        {col.gross_profit?.pct != null ? `${col.gross_profit.pct.toFixed(1)}%` : "—"}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-1 font-semibold text-slate-700">Operating Margin (EBIT)</td>
                    {commonSize.income_statement_common_size.map((col) => (
                      <td key={col.fiscal_year} className="py-1 text-right font-mono">
                        {col.ebit?.pct != null ? `${col.ebit.pct.toFixed(1)}%` : "—"}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-1 font-semibold text-slate-700">Net Profit Margin</td>
                    {commonSize.income_statement_common_size.map((col) => (
                      <td key={col.fiscal_year} className="py-1 text-right font-mono">
                        {col.net_income?.pct != null ? `${col.net_income.pct.toFixed(1)}%` : "—"}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-1 font-semibold text-slate-700">FCF Conversion %</td>
                    {commonSize.income_statement_common_size.map((col) => (
                      <td key={col.fiscal_year} className="py-1 text-right font-mono">
                        {col.fcf?.pct != null ? `${col.fcf.pct.toFixed(1)}%` : "—"}
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Reverse DCF Expectations Matrix */}
        <div className="mb-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 mb-2 border-b border-slate-200 pb-1">
            Reverse DCF Market-Implied Expectations
          </h3>
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs leading-relaxed text-slate-700">
            <p>
              Current market price implies that the company must compound Free Cash Flow at an annualized rate of{" "}
              <strong className="text-slate-900 font-mono">
                {practitioner?.malkiel?.required_fcf_growth_10y != null
                  ? `${(practitioner.malkiel.required_fcf_growth_10y * 100).toFixed(1)}%`
                  : "N/A"}
              </strong>{" "}
              for the next 10 years to justify today's valuation against nominal index hurdle rates.
            </p>
          </div>
        </div>

        {/* Investment Thesis & Research Notes Checklist */}
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 mb-2 border-b border-slate-200 pb-1">
            Institutional Research Checklist &amp; Signoff
          </h3>
          <div className="space-y-2 text-xs text-slate-700">
            <div className="flex items-start gap-2">
              <span className="font-bold font-mono">[ ]</span>
              <span><strong>Moat &amp; Reinvestment Durability:</strong> Verified high RNOA / ROIC persistence without reliance on excessive financial leverage.</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="font-bold font-mono">[ ]</span>
              <span><strong>Solvency &amp; Liquidity Runway:</strong> Verified safe Altman Z-score zone and conservative fixed-charge coverage (&gt;3.0x).</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="font-bold font-mono">[ ]</span>
              <span><strong>Earnings Quality:</strong> Verified Beneish M-Score &lt; -1.78 and absent CFO-Net Income decoupling shenanigans.</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="font-bold font-mono">[ ]</span>
              <span><strong>Shareholder Alignment:</strong> Verified positive True Shareholder Yield after subtracting Stock-Based Compensation drag.</span>
            </div>
          </div>

          <div className="mt-8 pt-4 border-t border-slate-300 flex items-center justify-between text-[10px] text-slate-400 font-mono">
            <span>Generated by Personal Equity Research Desk &bull; Local Docker Environment</span>
            <span>Non-Investment Advice &bull; Research Memorandum Only</span>
          </div>
        </div>
      </div>

      {/* Embedded Print Styling */}
      <style>{`
        @media print {
          body {
            background-color: white !important;
            color: black !important;
          }
          .no-print {
            display: none !important;
          }
          .print-page {
            border: none !important;
            padding: 0 !important;
            margin: 0 !important;
            box-shadow: none !important;
          }
          .print\\:break-after-page {
            break-after: page !important;
            page-break-after: always !important;
          }
        }
      `}</style>
    </div>
  );
};

export default FactsheetPrintView;
