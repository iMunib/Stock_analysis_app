import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../api/client";
import { SuggestionItem } from "../../api/types";

interface CommandItem {
  id: string;
  category: "Navigation" | "Screener Preset" | "Stock";
  title: string;
  subtitle?: string;
  path: string;
  badge?: string;
}

const STATIC_COMMANDS: CommandItem[] = [
  { id: "nav-screener", category: "Navigation", title: "Forensic Analysis & Screener", subtitle: "Single-stock forensic audit and quantitative accounting screener", path: "/screener" },
  { id: "nav-sectors", category: "Navigation", title: "Sectors Hub", subtitle: "GICS sector breakdowns and median valuations", path: "/sectors" },
  { id: "nav-compare", category: "Navigation", title: "Compare Desk", subtitle: "Side-by-side multi-stock comparison", path: "/compare" },
  { id: "nav-jobs", category: "Navigation", title: "System Jobs", subtitle: "Background ingestion and calculation status", path: "/jobs" },
  { id: "nav-learn", category: "Navigation", title: "Methodology & Learn", subtitle: "Scoring formulas and research philosophy", path: "/learn" },
  // Screener Presets
  { id: "preset-graham", category: "Screener Preset", title: "Graham Deep Bargains", subtitle: "Price < Graham Floor, margin of safety", path: "/screen?preset=graham_deep_bargains", badge: "Preset" },
  { id: "preset-antibubble", category: "Screener Preset", title: "Anti-Bubble Deep Value", subtitle: "Extreme multiple compression with positive FCF", path: "/screen?preset=anti_bubble_deep_value", badge: "Preset" },
  { id: "preset-lynch", category: "Screener Preset", title: "Peter Lynch Stalwarts", subtitle: "High PEG safety with consistent cash return", path: "/screen?preset=lynch_stalwarts_fair_value", badge: "Preset" },
  { id: "preset-compounders", category: "Screener Preset", title: "Compounders Under Implied Growth", subtitle: "Reverse DCF expectations gap < -5%", path: "/screen?preset=compounders_under_implied_growth", badge: "Preset" },
  { id: "preset-piotroski", category: "Screener Preset", title: "Piotroski High-Quality Turnarounds", subtitle: "F-Score >= 8 with healthy balance sheet", path: "/screen?preset=piotroski_high_quality_turnarounds", badge: "Preset" },
  { id: "preset-halal", category: "Screener Preset", title: "Halal Dividend Champions", subtitle: "AAOIFI compliant dividend compounders", path: "/screen?preset=halal_dividend_champions", badge: "Preset" },
];

export const CommandPalette: React.FC = () => {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [stockResults, setStockResults] = useState<SuggestionItem[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  // Listen for Ctrl+K or Cmd+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((prev) => !prev);
      } else if (e.key === "Escape") {
        setOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Focus input when opened
  useEffect(() => {
    if (open) {
      setQuery("");
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  // Search stocks dynamically
  useEffect(() => {
    if (!open || !query.trim()) {
      setStockResults([]);
      return;
    }
    const timer = setTimeout(() => {
      api.suggestions(query)
        .then((res) => setStockResults(res.items.slice(0, 6)))
        .catch(() => setStockResults([]));
    }, 150);
    return () => clearTimeout(timer);
  }, [open, query]);

  // Combine items
  const filteredStatic = STATIC_COMMANDS.filter((cmd) => {
    const q = query.toLowerCase();
    return (
      cmd.title.toLowerCase().includes(q) ||
      cmd.category.toLowerCase().includes(q) ||
      (cmd.subtitle && cmd.subtitle.toLowerCase().includes(q))
    );
  });

  const stockCommands: CommandItem[] = stockResults.map((s) => ({
    id: `stock-${s.company_id}`,
    category: "Stock",
    title: `${s.ticker} · ${s.name || s.company_id}`,
    subtitle: `${s.sector || "General"} · ${s.country || "US"}`,
    path: `/c/${encodeURIComponent(s.company_id)}`,
    badge: s.composite ? `Score ${s.composite.toFixed(1)}` : undefined,
  }));

  const allItems = [...stockCommands, ...filteredStatic];

  const handleSelect = (item: CommandItem) => {
    setOpen(false);
    navigate(item.path);
  };

  const handleInputKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % Math.max(1, allItems.length));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + allItems.length) % Math.max(1, allItems.length));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (allItems[selectedIndex]) {
        handleSelect(allItems[selectedIndex]);
      }
    }
  };

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-16 sm:pt-24 bg-black/70 backdrop-blur-sm p-4 animate-fade-in no-print"
      onClick={() => setOpen(false)}
    >
      <div
        className="w-full max-w-xl rounded-card border border-border-strong bg-bg-1 shadow-modal overflow-hidden animate-scale-in"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input Bar */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-border bg-bg-2/50">
          <span className="text-accent text-sm" aria-hidden="true">🔍</span>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            onKeyDown={handleInputKeyDown}
            placeholder="Type a ticker (AAPL, PLTR), screener preset, or page..."
            className="w-full bg-transparent text-sm text-ink-0 placeholder:text-ink-2 focus:outline-none font-mono"
          />
          <kbd className="hidden sm:inline-block px-1.5 py-0.5 text-[10px] font-mono text-ink-2 bg-bg-3 border border-border rounded">
            ESC
          </kbd>
        </div>

        {/* Results List */}
        <div className="max-h-80 overflow-y-auto p-2 divide-y divide-border/40">
          {allItems.length === 0 ? (
            <div className="p-4 text-center text-xs text-ink-2 font-mono">
              No matching commands or stocks found.
            </div>
          ) : (
            allItems.map((item, idx) => {
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={item.id}
                  onClick={() => handleSelect(item)}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`flex items-center justify-between px-3 py-2 rounded cursor-pointer transition-colors text-xs ${
                    isSelected ? "bg-accent-weak text-ink-0" : "text-ink-1 hover:bg-bg-2/70"
                  }`}
                >
                  <div className="min-w-0 pr-2">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-ink-0 font-mono">{item.title}</span>
                      {item.badge && (
                        <span className="text-[10px] px-1.5 py-0.2 rounded bg-bg-2 text-accent font-mono border border-accent/30">
                          {item.badge}
                        </span>
                      )}
                    </div>
                    {item.subtitle && (
                      <p className="text-[11px] text-ink-2 truncate mt-0.5">{item.subtitle}</p>
                    )}
                  </div>
                  <span className="text-[10px] uppercase font-mono text-ink-2 shrink-0 px-2 py-0.5 rounded bg-bg-2/50 border border-border">
                    {item.category}
                  </span>
                </div>
              );
            })
          )}
        </div>

        {/* Footer shortcuts hint */}
        <div className="px-3 py-2 border-t border-border bg-bg-2/30 flex items-center justify-between text-[11px] font-mono text-ink-2">
          <span>Navigate: ↑ ↓ · Select: ↵ · Close: Esc</span>
          <span className="text-accent">Institutional Command Palette</span>
        </div>
      </div>
    </div>
  );
};

export default CommandPalette;
