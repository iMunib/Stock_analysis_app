import React, { useState, useRef, useEffect } from "react";

export const GLOSSARY: Record<string, { label: string; text: string }> = {
  flev: {
    label: "Debt Leverage Multiplier",
    text: "Measures how much debt magnifies returns. High leverage boosts profits in good times, but increases bankruptcy risk during recessions.",
  },
  sloan: {
    label: "Cash Earnings Quality",
    text: "Compares reported accounting profit to actual cash in the bank. High accruals warn that paper earnings may not turn into cash.",
  },
  beneish: {
    label: "Accounting Red Flag Check",
    text: "Statistically tests 8 accounting relationships to detect aggressive revenue recognition, capitalized expenses, or hidden costs.",
  },
  altman: {
    label: "Bankruptcy Safety Score",
    text: "Evaluates debt, working capital, and earnings to determine if a company faces insolvency risk over the next 24 months.",
  },
  reverse_dcf: {
    label: "Market Growth Hurdle",
    text: "The annual free cash flow growth rate required over the next 10 years to justify today's stock price.",
  },
  shareholder_yield: {
    label: "Net Cash Returned to Owners",
    text: "Total dividends and share repurchases, reduced by the new shares issued to executives as stock-based compensation.",
  },
  fridson: {
    label: "EBITDA vs. Real Cash Spread",
    text: "Checks if paper EBITDA is backed by actual cash flow. A large gap indicates cash is trapped in unpaid customer bills or unsold inventory.",
  },
  owner_earnings: {
    label: "Buffett True Owner Profit",
    text: "The actual cash a business generates after paying for the maintenance investments needed to protect its competitive position.",
  },
};

export interface TooltipProps {
  term?: keyof typeof GLOSSARY;
  title?: string;
  content?: React.ReactNode;
  children?: React.ReactNode;
  side?: "top" | "bottom" | "left" | "right";
}

export function Tooltip({ term, title, content, children, side = "top" }: TooltipProps) {
  const [visible, setVisible] = useState(false);
  const triggerRef = useRef<HTMLButtonElement | HTMLSpanElement>(null);
  const entry = term ? GLOSSARY[term] : undefined;
  const displayTitle = title || entry?.label;
  const displayText = content || entry?.text;

  // Close on escape
  useEffect(() => {
    if (!visible) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setVisible(false);
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [visible]);

  return (
    <span
      className="relative inline-flex items-center"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onFocus={() => setVisible(true)}
      onBlur={() => setVisible(false)}
    >
      {children ? (
        <span className="cursor-help underline decoration-dotted decoration-border-strong hover:decoration-accent">
          {children}
        </span>
      ) : (
        <button
          type="button"
          ref={triggerRef as React.RefObject<HTMLButtonElement>}
          aria-label={displayTitle ? `Definition: ${displayTitle}` : "Definition tooltip"}
          className="ml-1 inline-flex h-3.5 w-3.5 items-center justify-center rounded-full border border-border text-[10px] font-mono text-ink-2 hover:border-accent hover:text-accent focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent"
        >
          ?
        </button>
      )}

      {visible && (
        <span
          role="tooltip"
          className={`absolute z-40 w-64 rounded-card border border-border bg-bg-1 p-3 text-left shadow-modal animate-fade-in pointer-events-none ${
            side === "top"
              ? "bottom-full left-1/2 -translate-x-1/2 mb-2"
              : side === "bottom"
              ? "top-full left-1/2 -translate-x-1/2 mt-2"
              : side === "left"
              ? "right-full top-1/2 -translate-y-1/2 mr-2"
              : "left-full top-1/2 -translate-y-1/2 ml-2"
          }`}
        >
          {displayTitle && (
            <span className="block font-heading text-xs font-semibold text-ink-0 border-b border-border pb-1 mb-1">
              {displayTitle}
            </span>
          )}
          <span className="block font-sans text-xs text-ink-1 leading-relaxed">
            {displayText}
          </span>
        </span>
      )}
    </span>
  );
}

export default Tooltip;
