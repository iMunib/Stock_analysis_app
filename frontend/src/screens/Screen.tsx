import { useCallback, useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api, ApiError, enc } from "../api/client";
import type { ScreenOut, SectorsOut } from "../api/types";
import { CompanyLink, ErrorBanner, Score, SignalBadge, Spinner } from "../components/ui";
import { multiple, percentish } from "../lib/format";
import InfoTip from "../components/InfoTip";
import { evaluateAlert, getAlerts } from "../lib/alerts";

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
        // Evaluate local alerts against loaded results
        const storedAlerts = getAlerts();
        if (storedAlerts.length > 0 && res.items.length > 0) {
          const matchedBanners: string[] = [];
          for (const it of res.items) {
            const found = storedAlerts.find((a) => a.id === it.company_id);
            if (found) {
              const b = evaluateAlert(found, it.ticker || it.company_id, it.pe_calc, it.composite);
              if (b) matchedBanners.push(b);
            }
          }
          setAlertBanners(matchedBanners);
        } else {
          setAlertBanners([]);
        }
      })
      .catch((e: ApiError) => {
        console.error("Screen error:", e);
        setError(e.message);
      })
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
      next.set("sort_dir", field === "name" || field === "ticker" ? "asc" : "desc");
      setParams(next, { replace: true });
    }
  };

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  const goCompare = () => {
    if (selectedIds.length > 0) {
      nav(`/compare?ids=${selectedIds.map(enc).join(",")}`);
    }
  };

  const resetFilters = () => {
    setParams(new URLSearchParams(), { replace: true });
  };

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

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Alerts banner if any triggered */}
      {alertBanners.length > 0 && (
        <div role="alert" className="space-y-1 rounded-md border border-gold/60 bg-gold/10 px-4 py-3 text-sm text-gold">
          <p className="font-semibold text-xs tracking-wider uppercase">Local Alerts Triggered</p>
          {alertBanners.slice(0, 3).map((b, idx) => (
            <p key={idx} className="font-mono text-xs text-paper">{b}</p>
          ))}
        </div>
      )}

      {/* Header */}
      <header className="flex flex-wrap items-baseline justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl tracking-tight">Screener</h1>
          <p className="text-sm text-fog">
            Filter all 720 companies by deterministic scores and snapshot ratios. No FX conversion.
          </p>
        </div>
        {selectedIds.length > 0 && (
          <button
            onClick={goCompare}
            className="rounded-md border border-gold/60 bg-gold/15 px-3.5 py-1.5 font-mono text-xs font-semibold text-gold hover:bg-gold/25 transition-colors"
          >
            Compare Selected ({selectedIds.length}) →
          </button>
        )}
      </header>

      {/* Filter Panel */}
      <section
        aria-label="Screener filters"
        className="rounded-md border border-line bg-panel p-4 space-y-4 text-xs"
      >
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line pb-3">
          <span className="font-mono text-[10px] uppercase tracking-widest text-dim">Filters (AND)</span>
          {hasActiveFilters && (
            <button
              onClick={resetFilters}
              className="text-xs text-gold hover:underline"
            >
              Reset filters
            </button>
          )}
        </div>

        {/* Top filter row: Currency, Sector, Industry, Signal */}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {/* Currency Toggle */}
          <div>
            <label className="block font-mono text-[10px] uppercase text-dim mb-1">Currency</label>
            <div className="flex rounded border border-line p-0.5 bg-ink">
              {(["ALL", "USD", "CAD"] as const).map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => updateParam("currency", c === "ALL" ? null : c)}
                  className={`flex-1 rounded py-1 font-mono text-xs transition-colors ${
                    currency === c ? "bg-panel text-gold font-medium" : "text-fog hover:text-paper"
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>
          </div>

          {/* GICS Sector */}
          <div>
            <label htmlFor="filter-sector" className="block font-mono text-[10px] uppercase text-dim mb-1">Sector (GICS)</label>
            <select
              id="filter-sector"
              value={sector}
              onChange={(e) => updateParam("sector", e.target.value)}
              className="w-full rounded border border-line bg-ink px-2.5 py-1.5 text-xs text-paper"
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
            <label htmlFor="filter-industry" className="block font-mono text-[10px] uppercase text-dim mb-1">Custom Industry</label>
            <select
              id="filter-industry"
              value={industry}
              onChange={(e) => updateParam("industry", e.target.value)}
              className="w-full rounded border border-line bg-ink px-2.5 py-1.5 text-xs text-paper"
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
            <label htmlFor="filter-signal" className="block font-mono text-[10px] uppercase text-dim mb-1">Signal</label>
            <select
              id="filter-signal"
              value={signal}
              onChange={(e) => updateParam("signal", e.target.value)}
              className="w-full rounded border border-line bg-ink px-2.5 py-1.5 text-xs text-paper"
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

        {/* Quantitative Filter Row: Composite Min, PE Max, ROE Min, FCF Margin Min, Coverage */}
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {/* Composite Min */}
          <div>
            <label htmlFor="filter-composite-min" className="block font-mono text-[10px] uppercase text-dim mb-1">
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
              className="w-full rounded border border-line bg-ink px-2.5 py-1 font-mono text-xs text-paper placeholder:text-dim"
            />
          </div>

          {/* PE Max (blank excluded) */}
          <div>
            <label htmlFor="filter-pe-max" className="block font-mono text-[10px] uppercase text-dim mb-1">
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
              className="w-full rounded border border-line bg-ink px-2.5 py-1 font-mono text-xs text-paper placeholder:text-dim"
            />
          </div>

          {/* ROE Min */}
          <div>
            <label htmlFor="filter-roe-min" className="block font-mono text-[10px] uppercase text-dim mb-1">
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
              className="w-full rounded border border-line bg-ink px-2.5 py-1 font-mono text-xs text-paper placeholder:text-dim"
            />
          </div>

          {/* FCF Margin Min */}
          <div>
            <label htmlFor="filter-fcf-min" className="block font-mono text-[10px] uppercase text-dim mb-1">
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
              className="w-full rounded border border-line bg-ink px-2.5 py-1 font-mono text-xs text-paper placeholder:text-dim"
            />
          </div>

          {/* Coverage Min */}
          <div>
            <label htmlFor="filter-coverage-min" className="block font-mono text-[10px] uppercase text-dim mb-1">
              Coverage Min <InfoTip term="Coverage" />
            </label>
            <select
              id="filter-coverage-min"
              value={coverageMin}
              onChange={(e) => updateParam("coverage_min", e.target.value)}
              className="w-full rounded border border-line bg-ink px-2.5 py-1 text-xs text-paper"
            >
              <option value="">Any coverage</option>
              <option value="2">At least 2/4 pillars</option>
              <option value="3">At least 3/4 pillars</option>
              <option value="4">Full 4/4 pillars</option>
            </select>
          </div>
        </div>

        {/* Toggles: Has Growth History & Exclude Banks */}
        <div className="flex flex-wrap items-center gap-6 pt-1 text-xs text-fog">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={hasGrowthHistory}
              onChange={(e) => updateParam("has_growth_history", e.target.checked)}
              className="h-4 w-4 rounded border-line bg-ink accent-[#e0a84f]"
            />
            <span>Has growth history (3+ yrs on file)</span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={excludeBanks}
              onChange={(e) => updateParam("exclude_banks", e.target.checked)}
              className="h-4 w-4 rounded border-line bg-ink accent-[#e0a84f]"
            />
            <span>Exclude banks and financials</span>
          </label>

          {data && (
            <span className="ml-auto font-mono text-dim text-[11px]">
              Showing {data.count} of {data.total} matches
            </span>
          )}
        </div>
      </section>

      {/* Results / Table */}
      {loading && <Spinner label="Screening universe…" />}
      {error && <ErrorBanner message={error} onRetry={load} />}

      {data && !loading && (
        <>
          {data.items.length === 0 ? (
            <div className="rounded-md border border-line bg-panel p-8 text-center space-y-3">
              <p className="font-display text-lg text-paper">No names match</p>
              <p className="text-sm text-fog max-w-md mx-auto">
                No names match — loosen PE or coverage.
              </p>
              <button
                onClick={resetFilters}
                className="inline-flex rounded border border-gold/60 bg-gold/10 px-3 py-1.5 text-xs text-gold hover:bg-gold/20"
              >
                Reset filters
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto rounded-md border border-line bg-panel">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-line bg-panel2/60 text-left font-mono text-[10px] uppercase tracking-wider text-dim">
                    <th scope="col" className="px-3 py-2.5 w-8">
                      <span className="sr-only">Select</span>
                    </th>
                    <th scope="col" className="px-3 py-2.5 cursor-pointer hover:text-paper" onClick={() => handleSort("name")}>
                      <span>Name {sortBy === "name" && (sortDir === "asc" ? "▲" : "▼")}</span>
                    </th>
                    <th scope="col" className="px-2 py-2.5 cursor-pointer hover:text-paper" onClick={() => handleSort("currency")}>
                      <span>Ccy {sortBy === "currency" && (sortDir === "asc" ? "▲" : "▼")}</span>
                    </th>
                    <th scope="col" className="px-3 py-2.5 text-right cursor-pointer hover:text-paper" onClick={() => handleSort("composite")}>
                      <span>Composite {sortBy === "composite" && (sortDir === "asc" ? "▲" : "▼")}</span>
                      <InfoTip term="Composite" />
                    </th>
                    <th scope="col" className="px-3 py-2.5 cursor-pointer hover:text-paper" onClick={() => handleSort("signal")}>
                      <span>Signal {sortBy === "signal" && (sortDir === "asc" ? "▲" : "▼")}</span>
                    </th>
                    <th scope="col" className="px-3 py-2.5 text-right cursor-pointer hover:text-paper" onClick={() => handleSort("pe")}>
                      <span>PE {sortBy === "pe" && (sortDir === "asc" ? "▲" : "▼")}</span>
                      <InfoTip term="PE" />
                    </th>
                    <th scope="col" className="px-3 py-2.5 text-right cursor-pointer hover:text-paper" onClick={() => handleSort("roe")}>
                      <span>ROE {sortBy === "roe" && (sortDir === "asc" ? "▲" : "▼")}</span>
                      <InfoTip term="ROE" />
                    </th>
                    <th scope="col" className="px-3 py-2.5 text-right cursor-pointer hover:text-paper" onClick={() => handleSort("fcf_margin")}>
                      <span>FCF Margin {sortBy === "fcf_margin" && (sortDir === "asc" ? "▲" : "▼")}</span>
                      <InfoTip term="FCF margin" />
                    </th>
                    <th scope="col" className="px-3 py-2.5 text-right cursor-pointer hover:text-paper" onClick={() => handleSort("peer_rank")}>
                      <span>Peer Rank {sortBy === "peer_rank" && (sortDir === "asc" ? "▲" : "▼")}</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {data.items.map((it) => {
                    const isSelected = selectedIds.includes(it.company_id);
                    return (
                      <tr
                        key={it.company_id}
                        className={`hover:bg-panel2/40 transition-colors ${isSelected ? "bg-gold/5" : ""}`}
                      >
                        <td className="px-3 py-2">
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => toggleSelect(it.company_id)}
                            aria-label={`Select ${it.name ?? it.ticker ?? it.company_id}`}
                            className="h-3.5 w-3.5 rounded border-line bg-ink accent-[#e0a84f]"
                          />
                        </td>
                        <td className="px-3 py-2 font-medium">
                          <CompanyLink companyId={it.company_id}>{it.name ?? it.company_id}</CompanyLink>
                          {it.ticker && <span className="ml-2 font-mono text-[10px] text-dim">{it.ticker}</span>}
                        </td>
                        <td className="px-2 py-2">
                          <span
                            className={`rounded border px-1.5 py-0.5 font-mono text-[10px] ${
                              it.currency === "USD" ? "border-info/40 text-info" : "border-gold/40 text-gold"
                            }`}
                          >
                            {it.currency ?? "—"}
                          </span>
                        </td>
                        <td className="px-3 py-2 text-right">
                          <Score value={it.composite} />
                        </td>
                        <td className="px-3 py-2">
                          <SignalBadge signal={it.signal} small />
                        </td>
                        <td className="px-3 py-2 text-right font-mono tabular-nums text-fog">
                          {multiple(it.pe_calc)}
                        </td>
                        <td className="px-3 py-2 text-right font-mono tabular-nums text-fog">
                          {percentish(it.roe_calc)}
                        </td>
                        <td className="px-3 py-2 text-right font-mono tabular-nums text-fog">
                          {percentish(it.fcfmargin_calc)}
                        </td>
                        <td className="px-3 py-2 text-right font-mono tabular-nums text-dim">
                          {it.peer_rank != null && it.peer_n != null ? `#${it.peer_rank}/${it.peer_n}` : "—"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
          <p className="text-[11px] text-dim">
            All ratios are dimensionless and comparable. Money columns are excluded in multi-currency views to prevent cross-border distortion.
          </p>
        </>
      )}
    </div>
  );
}
