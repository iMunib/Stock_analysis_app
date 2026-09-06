import React from "react";

interface TickerItem {
  symbol: string;
  name: string;
  price: string;
  change: string;
  isPositive: boolean;
  tag?: string;
}

const MARKET_BENCHMARKS: TickerItem[] = [
  { symbol: "SPX", name: "S&P 500", price: "5,864.67", change: "+0.42%", isPositive: true },
  { symbol: "TX60", name: "TSX 60", price: "1,442.18", change: "+0.28%", isPositive: true },
  { symbol: "NDX", name: "Nasdaq 100", price: "20,385.12", change: "+0.65%", isPositive: true },
  { symbol: "US10Y", name: "US 10-Yr Yield", price: "4.08%", change: "-0.04%", isPositive: false },
  { symbol: "CL", name: "Crude WTI", price: "$68.75", change: "-1.12%", isPositive: false },
  { symbol: "GC", name: "Gold Spot", price: "$2,654.80", change: "+0.85%", isPositive: true },
  { symbol: "USDCAD", name: "USD / CAD", price: "1.3542", change: "+0.08%", isPositive: true },
  { symbol: "SPUS", name: "Halal S&P ETF", price: "$41.95", change: "+0.51%", isPositive: true, tag: "AAOIFI" },
];

export const TerminalMarketTape: React.FC<{ className?: string }> = ({ className = "" }) => {
  return (
    <div
      aria-label="Global market benchmarks ticker tape"
      className={`relative w-full border-b border-border/80 bg-bg-1/90 backdrop-blur-md overflow-hidden select-none py-1.5 px-3 text-xs ${className}`}
    >
      <div className="flex items-center justify-between gap-4 max-w-desk mx-auto">
        {/* Live System Status Pill */}
        <div className="flex items-center gap-2 shrink-0 border-r border-border pr-3">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-pos opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-pos" />
          </span>
          <span className="font-mono text-[10px] uppercase font-bold tracking-widest text-ink-1">
            DESK FEED
          </span>
          <span className="rounded-chip border border-border px-1.5 py-0.2 font-mono text-[9px] text-ink-2 bg-bg-2/50 hidden sm:inline">
            SQLITE WAL
          </span>
        </div>

        {/* Scrolling Institutional Benchmark Ribbon */}
        <div className="flex-1 overflow-hidden [mask-image:linear-gradient(to_right,transparent,black_16px,black_calc(100%-16px),transparent)]">
          <div className="flex items-center gap-6 sm:gap-8 animate-ticker hover:[animation-play-state:paused] focus-within:[animation-play-state:paused] motion-reduce:animate-none motion-reduce:overflow-x-auto motion-reduce:no-scrollbar py-0.5">
            {[...MARKET_BENCHMARKS, ...MARKET_BENCHMARKS].map((item, idx) => (
              <div
                key={`${item.symbol}-${idx}`}
                className="flex items-center gap-1.5 shrink-0 font-mono text-[11px] cursor-default"
                title={`${item.name} (${item.symbol}): ${item.price} (${item.change})`}
              >
                <span className="font-bold text-ink-0">{item.symbol}</span>
                <span className="text-ink-2 hidden md:inline text-[10px]">{item.name}</span>
                <span className="tabular-nums text-ink-1">{item.price}</span>
                <span
                  className={`tabular-nums font-semibold flex items-center ${
                    item.isPositive ? "text-pos" : "text-neg"
                  }`}
                >
                  <span className="text-[9px] mr-0.5">{item.isPositive ? "▲" : "▼"}</span>
                  {item.change}
                </span>
                {item.tag && (
                  <span className="rounded-chip border border-accent/40 bg-accent-weak px-1 py-0.2 text-[8px] font-mono font-bold text-accent">
                    {item.tag}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Currency Isolation Rule Notice */}
        <div className="hidden lg:flex items-center gap-1 text-[10px] font-mono text-ink-2 shrink-0 border-l border-border pl-3">
          <span className="text-accent font-semibold">CAD vs USD</span>
          <span>· Money isolated · Ratios comparable</span>
        </div>
      </div>
    </div>
  );
};

export default TerminalMarketTape;
