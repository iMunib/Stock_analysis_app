import React, { useEffect, useRef, useState } from "react";

/**
 * TradingViewChart — zero-npm TradingView iframe embed (Workstream 4).
 *
 * Symbol mapping rules (mirrors backend mapping.py):
 *   US:AMD:US  → NASDAQ:AMD   (or NYSE prefix if in NYSE set)
 *   CA:RY:TSX  → TSX:RY
 *   Unknown    → raw ticker fallback
 *
 * Dark theme matches tokens.css via background/foreground color passing.
 * Fallback: SVG sparkline (Sparkline component) when iframe fails to load.
 */

interface TradingViewChartProps {
  companyId: string;
  ticker?: string;
  exchange?: string;
  currency?: string;
  height?: number;
  className?: string;
}

/** Derive TradingView symbol from company_id and optional context fields. */
function toTVSymbol(
  companyId: string,
  ticker?: string,
  exchange?: string
): string {
  const parts = companyId.split(":");
  const country = parts[0] ?? "";
  const tk = ticker ?? parts[1] ?? companyId;

  if (exchange) {
    // If caller passes a resolved exchange prefix, trust it.
    return `${exchange.toUpperCase()}:${tk.toUpperCase()}`;
  }

  if (country === "CA") {
    return `TSX:${tk.toUpperCase()}`;
  }

  // US: try to map common exchanges; NASDAQ is a safe default for US names.
  // A full exchange mapping is not possible without a price data call,
  // so we use NASDAQ as the default and let TradingView correct it.
  const NYSE_TICKERS = new Set([
    "BRK.A","BRK.B","JPM","BAC","WFC","C","GS","MS","JNJ","PG","XOM",
    "CVX","KO","MCD","WMT","HD","DIS","IBM","GE","GM","F","T","VZ","RTX",
    "MMM","CAT","BA","UNH","ABBV","MRK","PFE","ABT","BMY","LLY","AMGN",
    "MDT","CRM","ACN","SLB","HAL","COP","EOG","PSX","MPC","VLO","MA","V",
    "AXP","BK","USB","PNC","TFC","COF","SCHW","CB","MET","PRU","AFL","AIG",
    "PYPL","BLK","ICE","CME","MCO","SPGI","MSCI","FIS","FISV","WU","SYF",
  ]);
  if (NYSE_TICKERS.has(tk.toUpperCase())) {
    return `NYSE:${tk.toUpperCase()}`;
  }

  return `NASDAQ:${tk.toUpperCase()}`;
}

const TradingViewChart: React.FC<TradingViewChartProps> = ({
  companyId,
  ticker,
  exchange,
  currency,
  height = 450,
  className = "",
}) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [iframeError, setIframeError] = useState(false);
  const [iframeLoaded, setIframeLoaded] = useState(false);

  const tvSymbol = toTVSymbol(companyId, ticker, exchange);

  // TradingView widget embed URL (no API key required — it's a free public embed).
  const tvUrl = [
    "https://www.tradingview.com/widgetembed/?",
    `symbol=${encodeURIComponent(tvSymbol)}`,
    "&interval=W",
    "&hidesidetoolbar=1",
    "&hidetoptoolbar=0",
    "&symboledit=0",
    "&saveimage=0",
    "&toolbarbg=F1F3F6",
    "&studies=[]",
    "&theme=dark",
    "&style=1",
    "&timezone=exchange",
    "&withdateranges=1",
    "&showpopupbutton=1",
    "&locale=en",
    "&utm_source=localhost",
    "&utm_medium=widget",
  ].join("");

  // Timeout: if iframe hasn't loaded in 8s, show fallback.
  useEffect(() => {
    const t = setTimeout(() => {
      if (!iframeLoaded) setIframeError(true);
    }, 8000);
    return () => clearTimeout(t);
  }, [companyId, iframeLoaded]);

  // Reset state when companyId changes.
  useEffect(() => {
    setIframeError(false);
    setIframeLoaded(false);
  }, [companyId]);

  const handleLoad = () => setIframeLoaded(true);
  const handleError = () => setIframeError(true);

  if (iframeError) {
    return (
      <FallbackSparkline
        tvSymbol={tvSymbol}
        height={height}
      />
    );
  }

  return (
    <div
      className={`relative overflow-hidden rounded-card border border-border bg-bg-1 ${className}`}
      style={{ height }}
      aria-label={`TradingView chart for ${tvSymbol}`}
    >
      {!iframeLoaded && (
        <div className="absolute inset-0 flex items-center justify-center bg-bg-0/80 backdrop-blur-sm">
          <span className="text-xs text-ink-2 animate-pulse">
            Loading chart for {tvSymbol}…
          </span>
        </div>
      )}
      <iframe
        ref={iframeRef}
        src={tvUrl}
        title={`TradingView chart — ${tvSymbol}`}
        width="100%"
        height={height}
        frameBorder="0"
        allowTransparency={true}
        scrolling="no"
        className="block"
        onLoad={handleLoad}
        onError={handleError}
        sandbox="allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox"
      />
      <div className="absolute bottom-2 right-2 rounded border border-border/40 bg-bg-0/80 px-1.5 py-0.5 text-[9px] text-ink-2">
        {tvSymbol} · TradingView
        {currency ? ` · ${currency}` : ""}
      </div>
    </div>
  );
};

/** SVG fallback when the TradingView iframe times out. */
const FallbackSparkline: React.FC<{
  tvSymbol: string;
  height: number;
}> = ({ tvSymbol, height }) => (
  <div
    className="flex flex-col items-center justify-center rounded-card border border-border bg-bg-1 text-center"
    style={{ height }}
    aria-label={`Chart unavailable for ${tvSymbol}`}
  >
    <svg
      viewBox="0 0 120 40"
      width="120"
      height="40"
      className="mb-3 opacity-40"
      aria-hidden="true"
    >
      {/* Static placeholder sparkline */}
      <polyline
        points="0,35 20,28 40,30 60,18 80,22 100,10 120,15"
        fill="none"
        stroke="var(--accent)"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
    <p className="text-xs text-ink-2 mb-1">Chart not available</p>
    <p className="text-[10px] text-ink-2 mb-3">
      {tvSymbol} (iframe blocked or offline)
    </p>
    <a
      href={`https://www.tradingview.com/chart/?symbol=${encodeURIComponent(tvSymbol)}`}
      target="_blank"
      rel="noopener noreferrer"
      className="rounded-chip border border-accent/40 bg-accent-weak px-3 py-1 text-[11px] text-accent hover:bg-accent/20 transition-colors"
    >
      Open on TradingView ↗
    </a>
  </div>
);

export default TradingViewChart;
export { toTVSymbol };
