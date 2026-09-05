import React, { useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import { SuggestionItem } from "../../api/types";

interface TickerTypeaheadProps {
  value?: string;
  onChange?: (val: string) => void;
  onSelect: (item: SuggestionItem) => void;
  placeholder?: string;
  autoFocus?: boolean;
  className?: string;
  inputClassName?: string;
  size?: "sm" | "md" | "lg";
  ariaLabel?: string;
}

export const TickerTypeahead: React.FC<TickerTypeaheadProps> = ({
  value = "",
  onChange,
  onSelect,
  placeholder = "Search ticker, company name, or exchange…",
  autoFocus = false,
  className = "",
  inputClassName = "",
  size = "md",
  ariaLabel = "Ticker to add",
}) => {
  const [query, setQuery] = useState(value);
  const [suggestions, setSuggestions] = useState<SuggestionItem[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState<number>(-1);

  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setQuery(value);
  }, [value]);

  useEffect(() => {
    const q = query.trim();
    if (!q || q.length < 1) {
      setSuggestions([]);
      setOpen(false);
      setLoading(false);
      return;
    }

    setLoading(true);
    const timer = setTimeout(async () => {
      try {
        const res = await api.suggestions(q, 10);
        setSuggestions(res.items);
        setOpen(true);
        setSelectedIndex(-1);
      } catch {
        setSuggestions([]);
      } finally {
        setLoading(false);
      }
    }, 180);

    return () => clearTimeout(timer);
  }, [query]);

  // Click outside to close
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (item: SuggestionItem) => {
    setOpen(false);
    setQuery(item.ticker);
    if (onChange) onChange(item.ticker);
    onSelect(item);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!open || suggestions.length === 0) {
      if (e.key === "ArrowDown" && suggestions.length > 0) {
        setOpen(true);
      }
      return;
    }

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev < suggestions.length - 1 ? prev + 1 : 0));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : suggestions.length - 1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
        handleSelect(suggestions[selectedIndex]);
      } else if (suggestions.length > 0) {
        handleSelect(suggestions[0]);
      }
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  const exchangeBadgeStyle = (ex: string) => {
    switch (ex.toUpperCase()) {
      case "NASDAQ":
        return "bg-sky-500/10 text-sky-400 border-sky-500/30";
      case "NYSE":
        return "bg-amber-500/10 text-amber-400 border-amber-500/30";
      case "TSX":
      case "TSXV":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
      default:
        return "bg-indigo-500/10 text-indigo-400 border-indigo-500/30";
    }
  };

  const sizeClasses = {
    sm: "px-2.5 py-1 text-xs",
    md: "px-3 py-2 text-sm",
    lg: "px-4 py-2.5 text-base",
  }[size];

  return (
    <div ref={containerRef} className={`relative w-full ${className}`}>
      <div className="relative flex items-center">
        <input
          ref={inputRef}
          type="text"
          value={query}
          autoFocus={autoFocus}
          onChange={(e) => {
            setQuery(e.target.value);
            if (onChange) onChange(e.target.value);
            setOpen(true);
          }}
          onFocus={() => {
            if (suggestions.length > 0) setOpen(true);
          }}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          aria-label={ariaLabel}
          aria-autocomplete="list"
          aria-expanded={open}
          className={`w-full rounded-card border border-border bg-bg-0 text-ink-0 placeholder:text-ink-2 focus:border-accent focus:outline-none transition-all shadow-xs ${sizeClasses} ${inputClassName}`}
        />
        {loading && (
          <div className="absolute right-3 flex items-center">
            <span className="h-3 w-3 rounded-full border-2 border-accent border-t-transparent animate-spin" />
          </div>
        )}
      </div>

      {open && suggestions.length > 0 && (
        <div className="absolute left-0 right-0 top-full mt-1.5 z-50 rounded-card border border-border bg-bg-1 shadow-modal backdrop-blur-md overflow-hidden max-h-80 overflow-y-auto divide-y divide-border">
          <div className="px-3 py-1.5 bg-bg-2/70 text-[10px] font-mono uppercase tracking-wider text-ink-2 flex items-center justify-between">
            <span>Suggestions & Exchange Resolution</span>
            <span>Use ↑↓ to navigate · Enter to select</span>
          </div>

          <ul role="listbox">
            {suggestions.map((item, idx) => {
              const isSelected = idx === selectedIndex;
              return (
                <li
                  key={`${item.company_id}-${item.ticker}`}
                  role="option"
                  aria-selected={isSelected}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  onClick={() => handleSelect(item)}
                  className={`px-3 py-2.5 cursor-pointer flex items-center justify-between gap-3 transition-colors ${
                    isSelected ? "bg-accent-weak/40 text-ink-0" : "hover:bg-bg-2 text-ink-1"
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0 flex-1">
                    {/* Ticker badge */}
                    <span className="font-mono font-bold text-ink-0 text-sm tracking-tight shrink-0 bg-bg-2 px-2 py-0.5 rounded-chip border border-border">
                      {item.ticker}
                    </span>

                    {/* Exchange badge */}
                    <span
                      className={`text-[10px] font-mono px-1.5 py-0.5 rounded-chip border shrink-0 font-medium ${exchangeBadgeStyle(
                        item.exchange
                      )}`}
                    >
                      {item.exchange}
                    </span>

                    {/* Country tag */}
                    <span className="text-[10px] font-mono text-ink-2 shrink-0">
                      {item.country}
                    </span>

                    {/* Universe cohort badges */}
                    {item.universe_tags && item.universe_tags.length > 0 && (
                      <div className="hidden sm:flex items-center gap-1 shrink-0">
                        {item.universe_tags.includes("SP500") && (
                          <span className="text-[9px] font-mono px-1 py-0.2 bg-blue-500/10 text-blue-400 border border-blue-500/30 rounded-chip font-medium">
                            S&P 500
                          </span>
                        )}
                        {item.universe_tags.includes("RUSSELL1000") && (
                          <span className="text-[9px] font-mono px-1 py-0.2 bg-purple-500/10 text-purple-400 border border-purple-500/30 rounded-chip font-medium">
                            Russell 1000
                          </span>
                        )}
                        {item.universe_tags.includes("TSX") && (
                          <span className="text-[9px] font-mono px-1 py-0.2 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded-chip font-medium">
                            TSX
                          </span>
                        )}
                        {item.universe_tags.includes("MICROCAP") && (
                          <span className="text-[9px] font-mono px-1 py-0.2 bg-amber-500/10 text-amber-400 border border-amber-500/30 rounded-chip font-medium">
                            MicroCap
                          </span>
                        )}
                      </div>
                    )}

                    {/* Company name & Sector */}
                    <div className="truncate flex-1 flex items-baseline gap-2">
                      <span className="text-xs font-medium text-ink-0 truncate">
                        {item.name || item.ticker}
                      </span>
                      {item.sector && (
                        <span className="text-[11px] text-ink-2 truncate hidden sm:inline">
                          · {item.sector}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Right metadata / status badges */}
                  <div className="flex items-center gap-2 shrink-0">
                    {item.in_database ? (
                      <div className="flex items-center gap-1.5">
                        {item.composite != null && (
                          <span className="text-[11px] font-mono font-semibold text-accent bg-accent-weak px-1.5 py-0.5 rounded-chip">
                            {item.composite.toFixed(1)}/10
                          </span>
                        )}
                        <span className="text-[10px] font-mono text-pos bg-pos-weak/80 border border-pos/30 px-2 py-0.5 rounded-chip hidden md:inline">
                          In Database
                        </span>
                      </div>
                    ) : (
                      <span className="text-[10px] font-mono text-ink-1 bg-bg-2 border border-border px-2 py-0.5 rounded-chip hover:border-accent hover:text-accent transition-colors">
                        Fetch & Ingest →
                      </span>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
};

export default TickerTypeahead;
