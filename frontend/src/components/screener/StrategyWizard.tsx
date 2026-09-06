import React from "react";

export interface StrategyOption {
  id: string;
  name: string;
  author: string;
  badge: string;
  badgeTone: "pos" | "info" | "warning" | "accent";
  description: string;
  criteria: Record<string, any>;
  summaryText: string;
}

export const STRATEGY_OPTIONS: StrategyOption[] = [
  {
    id: "buffett_burry_deep_value",
    name: "Compound Quality (Buffett / Burry)",
    author: "Warren Buffett & Michael Burry",
    badge: "Capital Return",
    badgeTone: "pos",
    description: "High return on invested capital with modest valuation, solid free cash flow margin, and zero bank leverage.",
    criteria: {
      roic_min: 15,
      ev_ebitda_max: 10,
      fcf_margin_min: 7,
      composite_min: 6.0,
      exclude_banks: true,
    },
    summaryText: "ROIC >= 15%, EV/EBITDA <= 10x, FCF Margin >= 7%, Composite >= 6.0 (Non-Banks)",
  },
  {
    id: "greenblatt_magic_formula",
    name: "Magic Formula (Joel Greenblatt)",
    author: "Joel Greenblatt",
    badge: "Quant Value",
    badgeTone: "info",
    description: "Top-tier return on capital combined with high earnings yield (low P/E). Unemotional statistical bargain hunting.",
    criteria: {
      roic_min: 15,
      pe_max: 20,
      composite_min: 6.0,
      exclude_banks: true,
    },
    summaryText: "ROIC >= 15%, P/E <= 20x, Composite >= 6.0",
  },
  {
    id: "graham_defensive_bargains",
    name: "Defensive Value (Benjamin Graham)",
    author: "Benjamin Graham",
    badge: "Margin of Safety",
    badgeTone: "accent",
    description: "Intelligent Investor classic: P/E * P/B <= 22.5 with positive earnings, tangible asset backing, and minimal leverage.",
    criteria: {
      pe_max: 22.5,
      pb_max: 2.0,
      composite_min: 5.0,
      exclude_banks: true,
    },
    summaryText: "P/E <= 22.5, P/B <= 2.0, Composite >= 5.0",
  },
  {
    id: "peter_lynch_growth_compounders",
    name: "Stalwart Compounders (Peter Lynch)",
    author: "Peter Lynch",
    badge: "GARP",
    badgeTone: "pos",
    description: "Consistent compounding with ROE >= 15%, healthy FCF generation, and manageable debt relative to cash flow.",
    criteria: {
      roe_min: 15,
      fcf_margin_min: 7,
      debt_to_ebitda_max: 2.5,
      has_growth_history: true,
    },
    summaryText: "ROE >= 15%, FCF Margin >= 7%, Debt/EBITDA <= 2.5x, 3Y+ Growth",
  },
  {
    id: "sustainable_dividends",
    name: "Fortress Dividends (Income)",
    author: "Dividend Aristocrat Framework",
    badge: "Cash Yield",
    badgeTone: "warning",
    description: "Durable multi-year dividend payers with conservative payout ratio (< 60%) and resilient balance sheet health.",
    criteria: {
      consecutive_div_years_min: 5,
      payout_ratio_max: 0.60,
      composite_min: 5.5,
    },
    summaryText: "5+ Yrs Dividend History, Payout <= 60%, Composite >= 5.5",
  },
  {
    id: "novy_marx_gross_profitability",
    name: "Gross Profitability (Novy-Marx)",
    author: "Robert Novy-Marx (2013)",
    badge: "Asset Productivity",
    badgeTone: "info",
    description: "High Gross Profit / Assets (>= 0.25) delivering proven long-term outperformance independent of accounting accruals.",
    criteria: {
      gross_profitability_min: 0.25,
      composite_min: 6.0,
      exclude_banks: true,
    },
    summaryText: "GP / Assets >= 0.25, Composite >= 6.0 (Non-Banks)",
  },
  {
    id: "fortress_balance_sheet",
    name: "Retiree Fortress Balance Sheet",
    author: "Credit Risk & Solvency",
    badge: "Low Risk",
    badgeTone: "accent",
    description: "Heavy debt-refinancing protection: Debt/EBITDA <= 3.0x and Operating Income covers Interest Expense 8x or more.",
    criteria: {
      debt_to_ebitda_max: 3.0,
      interest_coverage_min: 8.0,
      exclude_banks: true,
    },
    summaryText: "Debt/EBITDA <= 3x, Interest Coverage >= 8x",
  },
  {
    id: "operational_turnarounds",
    name: "Cash-Flow Positive Turnarounds",
    author: "Forensic Accounting",
    badge: "Turnaround",
    badgeTone: "warning",
    description: "Companies reporting accounting net loss masking positive, expanding Free Cash Flow.",
    criteria: {
      turnaround_only: true,
    },
    summaryText: "Net Income < 0 with Positive Operating FCF",
  },
];

interface StrategyWizardProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectStrategy: (strategy: StrategyOption) => void;
}

export const StrategyWizard: React.FC<StrategyWizardProps> = ({
  isOpen,
  onClose,
  onSelectStrategy,
}) => {
  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="strategy-wizard-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink-0/60 backdrop-blur-sm animate-fade-in"
    >
      <div className="relative w-full max-w-4xl max-h-[90vh] flex flex-col rounded-card border border-border bg-bg-1 shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-bg-0">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl">✨</span>
              <h2 id="strategy-wizard-title" className="font-heading text-lg font-bold text-ink-0">
                Strategy Selection Wizard
              </h2>
            </div>
            <p className="text-xs text-ink-2 mt-0.5">
              Select an institutional research archetype to configure verified, literature-backed screening criteria in one click.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close strategy wizard"
            className="rounded p-1.5 text-ink-2 hover:text-ink-0 hover:bg-bg-2 transition-colors font-mono text-sm"
          >
            ✕
          </button>
        </div>

        {/* Modal Body: Cards Grid */}
        <div className="flex-1 overflow-y-auto p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          {STRATEGY_OPTIONS.map((st) => (
            <div
              key={st.id}
              onClick={() => {
                onSelectStrategy(st);
                onClose();
              }}
              className="group relative flex flex-col justify-between p-4 rounded-card border border-border bg-bg-0 hover:border-accent/80 hover:bg-accent-weak/30 transition-all cursor-pointer text-left"
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <span className="font-mono text-[10px] uppercase tracking-wider text-ink-2 font-medium">
                    {st.author}
                  </span>
                  <span className="font-mono text-[9px] uppercase px-2 py-0.5 rounded-chip font-semibold border border-border bg-bg-1 text-ink-1">
                    {st.badge}
                  </span>
                </div>
                <h3 className="font-heading font-semibold text-sm text-ink-0 group-hover:text-accent transition-colors">
                  {st.name}
                </h3>
                <p className="text-xs text-ink-1 mt-1 leading-relaxed">
                  {st.description}
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-border/60 flex items-center justify-between">
                <span className="font-mono text-[10px] text-ink-2 truncate max-w-[80%]">
                  {st.summaryText}
                </span>
                <span className="font-mono text-xs text-accent font-semibold group-hover:translate-x-0.5 transition-transform">
                  Apply →
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between px-6 py-3 border-t border-border bg-bg-0 text-xs text-ink-2">
          <span>All screening applies deterministic, reproducible calculations with locked composite weights.</span>
          <button
            type="button"
            onClick={onClose}
            className="rounded-card border border-border bg-bg-1 px-3 py-1 text-xs font-mono text-ink-1 hover:text-ink-0 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default StrategyWizard;
