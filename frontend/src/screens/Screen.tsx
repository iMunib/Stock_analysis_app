import { useCallback, useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api, ApiError, enc } from "../api/client";
import type { ScreenOut, SectorsOut } from "../api/types";
import { CompanyLink, ErrorBanner, Score, SignalBadge, Spinner } from "../components/ui";
import { multiple, percentish } from "../lib/format";
import InfoTip from "../components/InfoTip";
import { evaluateAlert, getAlerts } from "../lib/alerts";
import { Card, Chip, Page } from "../components/layout";
import { EmptyState } from "../components/feedback";

type SortField = "composite" | "name" | "ticker" | "currency" | "signal" | "pe" | "roe" | "fcf_margin" | "peer_rank";
type SortDir = "asc" | "desc";

export default function Screen() {
  const [params, setParams] = useSearchParams();
  const nav = useNavigate();

  // Filter states initialized from URL params if present
  const currency = (params.get("currency") || "ALL").toUpperCase();
  const sector = params.get("sector") || "";
  const industry = params.get("industry") || "";
  const signal = params.get("signal") || "";
  const compositeMin = params.get("composite_min") || "";
  const peMax = params.get("pe_max") || "";
  const roeMin = params.get("roe_min") || "";
  const fcfMarginMin = params.get("fcf_margin_min") || "";
  const coverageMin = params.get("coverage_min") || "";
  const hasGrowthHistory = params.get("has_growth_history") === "true";
  const excludeBanks = params.get("exclude_banks") === "true";

  const sortBy = (params.get("sort_by") as SortField) || "composite";
  const sortDir = (params.get("sort_dir") as SortDir) || "desc";

  const [data, setData] = useState<ScreenOut | null>(null);
  const [sectors, setSectors] = useState<SectorsOut | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [alertBanners, setAlertBanners] = useState<string[]>([]);

  // Load sector metadata for dropdowns
  useEffect(() => {
    api.sectors().then(setSectors).catch(() => setSectors(null));
  }, []);

  // Update query params helper
  const updateParam = useCallback(
    (key: string, value: string | boolean | null) => {
      const next = new URLSearchParams(params);
      if (value === null || value === "" || value === false || (key === "currency" && value === "ALL")) {
        next.delete(key);
      } else {
        next.set(key, String(value));
      }
      setParams(next, { replace: true });
    },
    [params, setParams],
  );

  // Fetch screener data
  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    const queryPayload: Record<string, string | number | boolean | null | undefined> = {
      currency,
      sector: sector || undefined,
      industry: industry || undefined,
      signal: signal || undefined,
      composite_min: compositeMin ? parseFloat(compositeMin) : undefined,
      pe_max: peMax ? parseFloat(peMax) : undefined,
      roe_min: roeMin ? parseFloat(roeMin) : undefined,
      fcf_margin_min: fcfMarginMin ? parseFloat(fcfMarginMin) : undefined,
      coverage_min: coverageMin ? parseInt(coverageMin, 10) : undefined,
      has_growth_history: hasGrowthHistory ? true : undefined,
      exclude_banks: excludeBanks ? true : undefined,
      sort_by: sortBy,
      sort_dir: sortDir,
      limit: 1000,
    };

    api
      .screen(queryPayload)
      .then((res) => {
        setData(res);
        // Check local alerts for the returned list
        const allAlerts = getAlerts();
        if (allAlerts.length > 0) {
          const fired: string[] = [];
          for (const item of res.items) {
            const a = allAlerts.find((x) => x.id === item.company_id);
            if (a) {
              const msg = evaluateAlert(a, item.name || item.ticker || item.company_id, item.pe_calc, item.composite);
              if (msg) fired.push(msg);
            }
          }
          setAlertBanners(fired);
        }
      })
      .catch((e: ApiError) => setError(e.message))
      .finally(() => setLoading(false));
  }, [
    currency,
    sector,
    industry,
    signal,
    compositeMin,
    peMax,
    roeMin,
    fcfMarginMin,
    coverageMin,
    hasGrowthHistory,
    excludeBanks,
    sortBy,
    sortDir,
  ]);

  useEffect(() => {
    load();
  }, [load]);

  const handleSort = (field: SortField) => {
    if (sortBy === field) {
      updateParam("sort_dir", sortDir === "asc" ? "desc" : "asc");
    } else {
      const next = new URLSearchParams(params);
      next.set("sort_by", field);
      next.set("sort_dir", field === "name" || field === "ticker" || field === "currency" ? "asc" : "desc");
      setParams(next, { replace: true });
    }
  };

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  };

  const goCompare = () => {
    if (!selectedIds.length) return;
    nav(`/compare?ids=${selectedIds.slice(0, 8).map(enc).join(",")}`);
  };

  const resetFilters = () => {
    setParams(new URLSearchParams(), { replace: true });
  };

  const exportCsv = useCallback(() => {
    if (!data || !data.items.length) return;
    const headers = [
      "Company ID",
      "Ticker",
      "Name",
      "Currency",
      "GICS Sector",
      "Custom Industry",
      "Composite Score",
      "Signal",
      "PE Ratio",
      "ROE %",
      "FCF Margin %",
      "Peer Rank",
      "Peer Count",
      "Coverage",
    ];
    const rows = data.items.map((i) => [
      `"${i.company_id}"`,
      `"${i.ticker || ""}"`,
      `"${(i.name || "").replace(/"/g, '""')}"`,
      `"${i.currency || ""}"`,
      `"${i.gics_sector || ""}"`,
      `"${i.custom_industry_sheet || ""}"`,
      i.composite !== null ? i.composite.toFixed(1) : "",
      `"${i.signal || ""}"`,
      i.pe_calc !== null ? i.pe_calc.toFixed(2) : "",
      i.roe_calc !== null ? (i.roe_calc * 100).toFixed(1) : "",
      i.fcfmargin_calc !== null ? (i.fcfmargin_calc * 100).toFixed(1) : "",
      i.peer_rank !== null ? i.peer_rank : "",
      i.peer_n !== null ? i.peer_n : "",
      i.coverage !== null ? i.coverage : "",
    ]);
    const csvContent = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `screener_export_${currency.toLowerCase()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, [data, currency]);

  const hasActiveFilters = Boolean(
    (currency && currency !== "ALL") ||
      sector ||
      industry ||
      signal ||
      compositeMin ||
      peMax ||
      roeMin ||
      fcfMarginMin ||
      coverageMin ||
      hasGrowthHistory ||
      excludeBanks,
  );

  const headerActions = (
    <div className="flex items-center gap-3">
      {selectedIds.length > 0 && (
        <button
          onClick={goCompare}
          className="rounded-card border border-accent/60 bg-accent-weak px-3.5 py-1.5 font-mono text-xs font-semibold text-accent hover:bg-accent/20 transition-colors"
        >
          Compare Selected ({selectedIds.length}) →
        </button>
      )}
      {data && data.items.length > 0 && (
        <button
          onClick={exportCsv}
          className="rounded-card border border-border bg-bg-1 px-3 py-1.5 font-mono text-xs text-ink-1 hover:border-accent hover:text-ink-0 transition-colors flex items-center gap-1.5"
          title="Download results as CSV"
        >
          <span>⬇ Export CSV</span>
        </button>
      )}
    </div>
  );

  return (
    <Page
      title="Screener"
      description="Filter all 720 companies by deterministic scores and snapshot ratios. No FX conversion."
      actions={headerActions}
    >
      {/* Alerts banner if any triggered */}
      {alertBanners.length > 0 && (
        <div role="alert" className="space-y-1 rounded-card border border-accent/60 bg-accent-weak px-4 py-3 text-sm text-accent">
          <p className="font-semibold text-xs tracking-wider uppercase font-mono">Local Alerts Triggered</p>
          {alertBanners.slice(0, 3).map((b, idx) => (
            <p key={idx} className="font-mono text-xs text-ink-0">{b}</p>
          ))}
        </div>
      )}

      {/* Filter Panel Card */}
      <Card padding="md" className="space-y-4 text-xs">
        {/* System Presets Segmented Bar */}
        <div className="flex flex-wrap items-center gap-2 pb-3 border-b border-border">
          <span className="font-mono text-[10px] uppercase tracking-widest text-ink-2 mr-1">Presets:</span>
          <button
            type="button"
            onClick={resetFilters}
            className={`px-2.5 py-1 rounded-chip text-xs border font-medium transition-colors ${
              !hasActiveFilters ? "bg-accent-weak border-accent text-accent" : "bg-bg-0 border-border text-ink-1 hover:text-ink-0"
            }`}
          >
            All Names
          </button>
          <button
            type="button"
            onClick={() => {
              const next = new URLSearchParams();
              next.set("roe_min", "15");
              next.set("fcf_margin_min", "7");
              next.set("composite_min", "6.0");
              next.set("exclude_banks", "true");
              setParams(next, { replace: true });
            }}
            className="px-2.5 py-1 rounded-chip text-xs border border-border bg-bg-0 text-ink-1 hover:border-accent hover:text-accent transition-colors"
          >
            💎 Buffett-Burry Deep Value
          </button>
          <button
            type="button"
            onClick={() => {
              const next = new URLSearchParams();
              next.set("signal", "turnaround_watch");
              setParams(next, { replace: true });
            }}
            className="px-2.5 py-1 rounded-chip text-xs border border-border bg-bg-0 text-ink-1 hover:border-neg hover:text-neg transition-colors"
          >
            🚩 Forensic Red Flags
          </button>
          <button
            type="button"
            onClick={() => {
              const next = new URLSearchParams();
              next.set("roe_min", "18");
              next.set("fcf_margin_min", "10");
              next.set("composite_min", "7.0");
              setParams(next, { replace: true });
            }}
            className="px-2.5 py-1 rounded-chip text-xs border border-border bg-bg-0 text-ink-1 hover:border-pos hover:text-pos transition-colors"
          >
            🚀 Discounted Compounders
          </button>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border pb-3">
          <span className="font-mono text-[10px] uppercase tracking-widest text-ink-2">Filters (AND)</span>
          {hasActiveFilters && (
            <button
              onClick={resetFilters}
              className="text-xs text-accent hover:underline font-mono"
            >
              Reset filters
            </button>
          )}
        </div>

        {/* Top filter row: Currency, Sector, Industry, Signal */}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {/* Currency Toggle */}
          <div>
            <label className="block font-mono text-[10px] uppercase text-ink-2 mb-1">Currency</label>
            <div className="flex rounded-chip border border-border p-0.5 bg-bg-0">
              {(["ALL", "USD", "CAD"] as const).map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => updateParam("currency", c === "ALL" ? null : c)}
                  className={`flex-1 rounded-chip py-1 font-mono text-xs transition-colors ${
                    currency === c ? "bg-bg-1 text-accent font-medium" : "text-ink-1 hover:text-ink-0"
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>
          </div>

          {/* GICS Sector */}
          <div>
            <label htmlFor="filter-sector" className="block font-mono text-[10px] uppercase text-ink-2 mb-1">Sector (GICS)</label>
            <select
              id="filter-sector"
              value={sector}
              onChange={(e) => updateParam("sector", e.target.value)}
              className="w-full rounded-card border border-border bg-bg-0 px-2.5 py-1.5 text-xs text-ink-0"
            >
              <option value="">All Sectors</option>
              {(sectors?.gics_sectors ?? []).map((s) => (
                <option key={s.name} value={s.name}>
                  {s.name} ({s.count})
                </option>
              ))}
            </select>
          </div>

          {/* Custom Industry Sheet */}
          <div>
            <label htmlFor="filter-industry" className="block font-mono text-[10px] uppercase text-ink-2 mb-1">Custom Industry</label>
            <select
              id="filter-industry"
              value={industry}
              onChange={(e) => updateParam("industry", e.target.value)}
              className="w-full rounded-card border border-border bg-bg-0 px-2.5 py-1.5 text-xs text-ink-0"
            >
              <option value="">All Industries</option>
              {(sectors?.custom_industries ?? []).map((i) => (
                <option key={i.name} value={i.name}>
                  {i.name} ({i.count})
                </option>
              ))}
            </select>
          </div>

          {/* Signal */}
          <div>
            <label htmlFor="filter-signal" className="block font-mono text-[10px] uppercase text-ink-2 mb-1">Signal</label>
            <select
              id="filter-signal"
              value={signal}
              onChange={(e) => updateParam("signal", e.target.value)}
              className="w-full rounded-card border border-border bg-bg-0 px-2.5 py-1.5 text-xs text-ink-0"
            >
              <option value="">All Signals</option>
              <option value="strong_candidate">Strong candidate</option>
              <option value="positive_momentum">Positive momentum</option>
              <option value="balanced_opportunity">Balanced opportunity</option>
              <option value="turnaround_watch">Turnaround watch</option>
              <option value="mixed">Mixed</option>
              <option value="insufficient_data">Insufficient data</option>
            </select>
          </div>
        </div>

        {/* Quantitative Filter Row */}
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {/* Composite Min */}
          <div>
            <label htmlFor="filter-composite-min" className="block font-mono text-[10px] uppercase text-ink-2 mb-1">
              Composite Min <InfoTip term="Composite" />
            </label>
            <input
              id="filter-composite-min"
              type="number"
              min="0"
              max="10"
              step="0.5"
              placeholder="e.g. 5.0"
              value={compositeMin}
              onChange={(e) => updateParam("composite_min", e.target.value)}
              className="w-full rounded-card border border-border bg-bg-0 px-2.5 py-1 font-mono text-xs text-ink-0 placeholder:text-ink-2"
            />
          </div>

          {/* PE Max */}
          <div>
            <label htmlFor="filter-pe-max" className="block font-mono text-[10px] uppercase text-ink-2 mb-1">
              PE Max <InfoTip term="PE" />
            </label>
            <input
              id="filter-pe-max"
              type="number"
              min="1"
              max="200"
              step="1"
              placeholder="e.g. 25 (blanks out)"
              value={peMax}
              onChange={(e) => updateParam("pe_max", e.target.value)}
              className="w-full rounded-card border border-border bg-bg-0 px-2.5 py-1 font-mono text-xs text-ink-0 placeholder:text-ink-2"
            />
          </div>

          {/* ROE Min */}
          <div>
            <label htmlFor="filter-roe-min" className="block font-mono text-[10px] uppercase text-ink-2 mb-1">
              ROE Min % <InfoTip term="ROE" />
            </label>
            <input
              id="filter-roe-min"
              type="number"
              min="-100"
              max="1000"
              step="5"
              placeholder="e.g. 15"
              value={roeMin}
              onChange={(e) => updateParam("roe_min", e.target.value)}
              className="w-full rounded-card border border-border bg-bg-0 px-2.5 py-1 font-mono text-xs text-ink-0 placeholder:text-ink-2"
            />
          </div>

          {/* FCF Margin Min */}
          <div>
            <label htmlFor="filter-fcf-min" className="block font-mono text-[10px] uppercase text-ink-2 mb-1">
              FCF Margin Min % <InfoTip term="FCF margin" />
            </label>
            <input
              id="filter-fcf-min"
              type="number"
              min="-100"
              max="100"
              step="5"
              placeholder="e.g. 10"
              value={fcfMarginMin}
              onChange={(e) => updateParam("fcf_margin_min", e.target.value)}
              className="w-full rounded-card border border-border bg-bg-0 px-2.5 py-1 font-mono text-xs text-ink-0 placeholder:text-ink-2"
            />
          </div>

          {/* Coverage Min */}
          <div>
            <label htmlFor="filter-coverage-min" className="block font-mono text-[10px] uppercase text-ink-2 mb-1">
              Coverage Min <InfoTip term="Coverage" />
            </label>
            <select
              id="filter-coverage-min"
              value={coverageMin}
              onChange={(e) => updateParam("coverage_min", e.target.value)}
              className="w-full rounded-card border border-border bg-bg-0 px-2.5 py-1 text-xs text-ink-0"
            >
              <option value="">Any coverage</option>
              <option value="2">At least 2/4 pillars</option>
              <option value="3">At least 3/4 pillars</option>
              <option value="4">Full 4/4 pillars</option>
            </select>
          </div>
        </div>

        {/* Toggles */}
        <div className="flex flex-wrap items-center gap-6 pt-1 text-xs text-ink-1">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={hasGrowthHistory}
              onChange={(e) => updateParam("has_growth_history", e.target.checked)}
              className="h-4 w-4 rounded-chip border-border bg-bg-0 accent-accent"
            />
            <span>Has growth history (3+ yrs on file)</span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={excludeBanks}
              onChange={(e) => updateParam("exclude_banks", e.target.checked)}
              className="h-4 w-4 rounded-chip border-border bg-bg-0 accent-accent"
            />
            <span>Exclude banks and financials</span>
          </label>

          {data && (
            <span className="ml-auto font-mono text-ink-2 text-[11px]">
              Showing {data.count} of {data.total} matches
            </span>
          )}
        </div>
      </Card>

      {/* Results / Table */}
      {loading && <Spinner label="Screening universe…" />}
      {error && <ErrorBanner message={error} onRetry={load} />}

      {data && !loading && (
        <>
          {data.items.length === 0 ? (
            <EmptyState
              title="No names match"
              body="No names match — loosen PE or coverage."
              cta={
                <button
                  onClick={resetFilters}
                  className="rounded-card border border-accent/60 bg-accent-weak px-3 py-1.5 font-mono text-xs text-accent hover:bg-accent/20 transition-colors"
                >
                  Reset filters
                </button>
              }
            />
          ) : (
            <Card padding="none" className="overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-border bg-bg-2/70 text-left font-mono text-[10px] uppercase tracking-wider text-ink-2">
                      <th scope="col" className="px-3 py-2.5 w-8">
                        <span className="sr-only">Select</span>
                      </th>
                      <th scope="col" className="px-3 py-2.5 cursor-pointer hover:text-ink-0" onClick={() => handleSort("name")}>
                        <span>Name {sortBy === "name" && (sortDir === "asc" ? "▲" : "▼")}</span>
                      </th>
                      <th scope="col" className="px-2 py-2.5 cursor-pointer hover:text-ink-0" onClick={() => handleSort("currency")}>
                        <span>Ccy {sortBy === "currency" && (sortDir === "asc" ? "▲" : "▼")}</span>
                      </th>
                      <th scope="col" className="px-3 py-2.5 text-right cursor-pointer hover:text-ink-0" onClick={() => handleSort("composite")}>
                        <span>Composite {sortBy === "composite" && (sortDir === "asc" ? "▲" : "▼")}</span>
                        <InfoTip term="Composite" />
                      </th>
                      <th scope="col" className="px-3 py-2.5 cursor-pointer hover:text-ink-0" onClick={() => handleSort("signal")}>
                        <span>Signal {sortBy === "signal" && (sortDir === "asc" ? "▲" : "▼")}</span>
                      </th>
                      <th scope="col" className="px-3 py-2.5 text-right cursor-pointer hover:text-ink-0" onClick={() => handleSort("pe")}>
                        <span>PE {sortBy === "pe" && (sortDir === "asc" ? "▲" : "▼")}</span>
                        <InfoTip term="PE" />
                      </th>
                      <th scope="col" className="px-3 py-2.5 text-right cursor-pointer hover:text-ink-0" onClick={() => handleSort("roe")}>
                        <span>ROE {sortBy === "roe" && (sortDir === "asc" ? "▲" : "▼")}</span>
                        <InfoTip term="ROE" />
                      </th>
                      <th scope="col" className="px-3 py-2.5 text-right cursor-pointer hover:text-ink-0" onClick={() => handleSort("fcf_margin")}>
                        <span>FCF Margin {sortBy === "fcf_margin" && (sortDir === "asc" ? "▲" : "▼")}</span>
                        <InfoTip term="FCF margin" />
                      </th>
                      <th scope="col" className="px-3 py-2.5 text-right cursor-pointer hover:text-ink-0" onClick={() => handleSort("peer_rank")}>
                        <span>Peer Rank {sortBy === "peer_rank" && (sortDir === "asc" ? "▲" : "▼")}</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {data.items.map((it) => {
                      const isSelected = selectedIds.includes(it.company_id);
                      return (
                        <tr
                          key={it.company_id}
                          className={`hover:bg-bg-2/50 transition-colors ${isSelected ? "bg-accent-weak" : ""}`}
                        >
                          <td className="px-3 py-2">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => toggleSelect(it.company_id)}
                              aria-label={`Select ${it.name ?? it.ticker ?? it.company_id}`}
                              className="h-3.5 w-3.5 rounded-chip border-border bg-bg-0 accent-accent"
                            />
                          </td>
                          <td className="px-3 py-2 font-medium">
                            <CompanyLink companyId={it.company_id}>{it.name ?? it.company_id}</CompanyLink>
                            {it.ticker && <span className="ml-2 font-mono text-[10px] text-ink-2">{it.ticker}</span>}
                          </td>
                          <td className="px-2 py-2">
                            <Chip tone={it.currency === "USD" ? "info" : "warning"} size="sm">
                              {it.currency ?? "—"}
                            </Chip>
                          </td>
                          <td className="px-3 py-2 text-right">
                            <Score value={it.composite} />
                          </td>
                          <td className="px-3 py-2">
                            <SignalBadge signal={it.signal} small />
                          </td>
                          <td className="px-3 py-2 text-right font-mono tabular-nums text-ink-1">
                            {multiple(it.pe_calc)}
                          </td>
                          <td className="px-3 py-2 text-right font-mono tabular-nums text-ink-1">
                            {percentish(it.roe_calc)}
                          </td>
                          <td className="px-3 py-2 text-right font-mono tabular-nums text-ink-1">
                            {percentish(it.fcfmargin_calc)}
                          </td>
                          <td className="px-3 py-2 text-right font-mono tabular-nums text-ink-1">
                            {it.peer_rank != null && it.peer_n != null ? (
                              <span>#{it.peer_rank} of {it.peer_n}</span>
                            ) : (
                              "—"
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </>
      )}
    </Page>
  );
}
