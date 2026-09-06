import React from "react";

interface BookChecklistsProps {
  checklists?: {
    graham?: boolean;
    lynch?: boolean;
    greenblatt?: boolean;
    piotroski?: boolean;
  };
  className?: string;
}

export const BookChecklists: React.FC<BookChecklistsProps> = ({
  checklists = {},
  className = "",
}) => {
  const items = [
    {
      key: "graham",
      short: "G",
      name: "Benjamin Graham Defensive",
      desc: "P/E * P/B <= 22.5 or Net Current Asset Value > 0",
      passed: Boolean(checklists.graham),
    },
    {
      key: "lynch",
      short: "L",
      name: "Peter Lynch Stalwart",
      desc: "PEG <= 1.2 or ROE >= 14% with low debt",
      passed: Boolean(checklists.lynch),
    },
    {
      key: "greenblatt",
      short: "GB",
      name: "Joel Greenblatt Magic Formula",
      desc: "ROIC >= 14% combined with P/E <= 22.0",
      passed: Boolean(checklists.greenblatt),
    },
    {
      key: "piotroski",
      short: "P",
      name: "Joseph Piotroski Turnaround",
      desc: "Piotroski F-Score >= 6 or Composite >= 6.5",
      passed: Boolean(checklists.piotroski),
    },
  ];

  return (
    <div className={`inline-flex items-center gap-1 ${className}`} aria-label="Academic book checklists">
      {items.map((it) => (
        <span
          key={it.key}
          title={`${it.name}: ${it.passed ? "PASS" : "FAIL"} (${it.desc})`}
          className={`inline-flex items-center justify-center font-mono text-[9px] font-bold rounded px-1 py-0.5 min-w-[16px] transition-colors cursor-help ${
            it.passed
              ? "bg-pos/20 text-pos border border-pos/40"
              : "bg-bg-2 text-ink-2 border border-border/50 opacity-60"
          }`}
        >
          {it.short}
        </span>
      ))}
    </div>
  );
};

export default BookChecklists;
