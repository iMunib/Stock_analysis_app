import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api, ApiError, enc } from "../api/client";
import type { ScreenOut, ScreenerPresetItem, SectorsOut } from "../api/types";
import { CompanyLink, ErrorBanner, HalalBadge, Score, SignalBadge, Spinner } from "../components/ui";
import { multiple, percentish } from "../lib/format";
import InfoTip from "../components/InfoTip";
import { evaluateAlert, getAlerts } from "../lib/alerts";
import { Card, Chip, Page } from "../components/layout";
import { EmptyState } from "../components/feedback";
import RevenueSparkline from "../components/screener/RevenueSparkline";
import BookChecklists from "../components/screener/BookChecklists";
import StrategyWizard, { type StrategyOption } from "../components/screener/StrategyWizard";

type SortField =
  | "composite"
  | "name"
  | "ticker"
  | "currency"
  | "signal"
  | "pe"
  | "roe"
  | "fcf_margin"
  | "peer_rank"
  | "roic"
  | "debt_to_ebitda";
type SortDir = "asc" | "desc";

const CANONICAL_PRESETS = [
  { id: "buffett_burry_deep_value", name: "Buffett-Burry Value", icon: "💎" },
  { id: "greenblatt_magic_formula", name: "Greenblatt Formula", icon: "⚡" },
  { id: "graham_defensive_bargains", name: "Graham Defensive", icon: "🛡️" },
  { id: "peter_lynch_growth_compounders", name: "Peter Lynch Stalwarts", icon: "📈" },
  { id: "sustainable_dividends", name: "Sustainable Dividends", icon: "💰" },
  { id: "garp_investor", name: "GARP Investor", icon: "🎯" },
  { id: "novy_marx_gross_profitability", name: "Novy-Marx GP/A", icon: "🏛️" },
  { id: "fortress_balance_sheet", name: "Fortress Solvency", icon: "🏰" },
  { id: "boring_great_businesses", name: "Boring Compounders", icon: "🧱" },
  { id: "operational_turnarounds", name: "Cash Turnarounds", icon: "🔄" },
  { id: "durable_growth_compounders", name: "Durable Growth (15%+)", icon: "🚀" },
  { id: "contrarian_deep_value", name: "Contrarian Value", icon: "🔍" },
];

export default function Screen() {
  const [params, setParams] = useSearchParams();
  const nav = useNavigate();

  // Primary filters from URL params
  const currency = (params.get("currency") || "ALL").toUpperCase();
  const sector = params.get("sector") || "";
  const industry = params.get("industry") || "";
  const signal = params.get("signal") || "";
  const compositeMin = params.get("composite_min") || "";
  const peMax = params.get("pe_max") || "";
  const pbMax = params.get("pb_max") || "";
  const roeMin = params.get("roe_min") || "";
  const fcfMarginMin = params.get("fcf_margin_min") || "";
  const coverageMin = params.get("coverage_min") || "";
  const hasGrowthHistory = params.get("has_growth_history") === "true";
  const excludeBanks = params.get("exclude_banks") === "true";

  // Wave 2 advanced criteria
  const activePreset = params.get("preset") || "";
  const criteriaLogic = (params.get("criteria_logic") || "AND").toUpperCase();
  const roicMin = params.get("roic_min") || "";
  const evEbitdaMax = params.get("ev_ebitda_max") || "";
  const debtToEbitdaMax = params.get("debt_to_ebitda_max") || "";
  const interestCoverageMin = params.get("interest_coverage_min") || "";
  const grossProfitabilityMin = params.get("gross_profitability_min") || "";
  const sbcDilutionMax = params.get("sbc_dilution_max") || "";
  const pegMax = params.get("peg_max") || "";
  const marketCapBand = params.get("market_cap_band") || "";
  const turnaroundOnly = params.get("turnaround_only") === "true";
  const altmanSafeOnly = params.get("altman_safe_only") === "true";
  const halalCandidate = params.get("halal_candidate") === "true";

  const sortBy = (params.get("sort_by") as SortField) || "composite";
  const sortDir = (params.get("sort_dir") as SortDir) || "desc";

  const [data, setData] = useState<ScreenOut | null>(null);
  const [sectors, setSectors] = useState<SectorsOut | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [alertBanners, setAlertBanners] = useState<string[]>([]);

  // Strategy wizard & saved presets states
  const [isWizardOpen, setIsWizardOpen] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [savedPresets, setSavedPresets] = useState<ScreenerPresetItem[]>([]);
  const [presetNameInput, setPresetNameInput] = useState("");
  const [autoRunInput, setAutoRunInput] = useState(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);
  const [isSaveModalOpen, setIsSaveModalOpen] = useState(false);

  // Load sector metadata and saved presets
  useEffect(() => {
    api.sectors().then(setSectors).catch(() => setSectors(null));
    api
      .screenerPresets()
      .then((res) => {
        if (Array.isArray(res)) {
          setSavedPresets(res as unknown as ScreenerPresetItem[]);
        }
      })
      .catch(() => {});
  }, []);

  // Update query params helper
  const updateParam = useCallback(
    (key: string, value: string | boolean | null) => {
      const next = new URLSearchParams(params);
      if (
        value === null ||
        value === "" ||
        value === false ||
        (key === "currency" && value === "ALL") ||
        (key === "criteria_logic" && value === "AND")
      ) {
        next.delete(key);
      } else {
        next.set(key, String(value));
      }
      setParams(next, { replace: true });
    },
    [params, setParams],
  );

  const queryPayload = useMemo(
    () => ({
      currency,
      sector: sector || undefined,
      industry: industry || undefined,
      signal: signal || undefined,
      composite_min: compositeMin ? parseFloat(compositeMin) : undefined,
      pe_max: peMax ? parseFloat(peMax) : undefined,
      pb_max: pbMax ? parseFloat(pbMax) : undefined,
      roe_min: roeMin ? parseFloat(roeMin) : undefined,
      fcf_margin_min: fcfMarginMin ? parseFloat(fcfMarginMin) : undefined,
      coverage_min: coverageMin ? parseInt(coverageMin, 10) : undefined,
      has_growth_history: hasGrowthHistory ? true : undefined,
      exclude_banks: excludeBanks ? true : undefined,
      preset: activePreset || undefined,
      criteria_logic: criteriaLogic,
      roic_min: roicMin ? parseFloat(roicMin) : undefined,
      ev_ebitda_max: evEbitdaMax ? parseFloat(evEbitdaMax) : undefined,
      debt_to_ebitda_max: debtToEbitdaMax ? parseFloat(debtToEbitdaMax) : undefined,
      interest_coverage_min: interestCoverageMin ? parseFloat(interestCoverageMin) : undefined,
      gross_profitability_min: grossProfitabilityMin ? parseFloat(grossProfitabilityMin) : undefined,
      sbc_dilution_max: sbcDilutionMax ? parseFloat(sbcDilutionMax) : undefined,
      peg_max: pegMax ? parseFloat(pegMax) : undefined,
      market_cap_band: marketCapBand || undefined,
      turnaround_only: turnaroundOnly ? true : undefined,
      altman_safe_only: altmanSafeOnly ? true : undefined,
      halal_candidate: halalCandidate ? true : undefined,
      sort_by: sortBy,
      sort_dir: sortDir,
      limit: 1000,
    }),
    [
      currency,
      sector,
      industry,
      signal,
      compositeMin,
      peMax,
      pbMax,
      roeMin,
      fcfMarginMin,
      coverageMin,
      hasGrowthHistory,
      excludeBanks,
      activePreset,
      criteriaLogic,
      roicMin,
      evEbitdaMax,
      debtToEbitdaMax,
      interestCoverageMin,
      grossProfitabilityMin,
      sbcDilutionMax,
      pegMax,
      marketCapBand,
      turnaroundOnly,
      altmanSafeOnly,
      halalCandidate,
      sortBy,
      sortDir,
    ],
  );

  // Fetch screener data
  const load = useCallback(() => {
    setLoading(true);
    setError(null);

    api
      .screen(queryPayload)
      .then((res) => {
        setData(res);
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
  }, [queryPayload]);

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
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  const goCompare = () => {
    if (!selectedIds.length) return;
    nav(`/compare?ids=${selectedIds.slice(0, 8).map(enc).join(",")}`);
  };

  const resetFilters = () => {
    setParams(new URLSearchParams(), { replace: true });
  };

  const applyPreset = (presetId: string) => {
    const next = new URLSearchParams();
    next.set("preset", presetId);
    setParams(next, { replace: true });
  };

  // Formula-Transparent CSV Export (US-0012, US-0030)
  const exportCsv = useCallback(() => {
    if (!data || !data.items.length) return;
    const downloadUrl = api.screenExportUrl(queryPayload);
    const link = document.createElement("a");
    link.href = downloadUrl;
    link.setAttribute("download", `screener_audit_export_${currency.toLowerCase()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, [data, queryPayload, currency]);

  // Strategy Wizard selection handler (US-0001)
  const handleSelectStrategy = (strat: StrategyOption) => {
    const next = new URLSearchParams();
    if (strat.id) {
      next.set("preset", strat.id);
    }
    for (const [k, v] of Object.entries(strat.criteria)) {
      if (v !== undefined && v !== null) {
        next.set(k, String(v));
      }
    }
    setParams(next, { replace: true });
  };

  // Save Custom Preset (US-0009, US-0042)
  const handleSavePreset = async () => {
    const cleanName = presetNameInput.trim().replace(/\s+/g, "_");
    if (!cleanName) return;

    try {
      const criteriaToSave: Record<string, any> = {};
      for (const [k, v] of Object.entries(queryPayload)) {
        if (v !== undefined && k !== "sort_by" && k !== "sort_dir" && k !== "limit") {
          criteriaToSave[k] = v;
        }
      }

      await api.savePreset({
        name: cleanName,
        criteria: criteriaToSave,
        auto_run: autoRunInput,
      });

      setSaveSuccessMsg(`Preset '${cleanName}' saved successfully!`);
      setPresetNameInput("");
      setIsSaveModalOpen(false);
      // Refresh presets list
      api.screenerPresets().then((res) => {
        if (Array.isArray(res)) setSavedPresets(res as unknown as ScreenerPresetItem[]);
      });
      setTimeout(() => setSaveSuccessMsg(null), 4000);
    } catch (err: any) {
      setError(err?.message || "Failed to save preset");
    }
  };

  const hasActiveFilters = Boolean(
    (currency && currency !== "ALL") ||
      sector ||
      industry ||
      signal ||
      compositeMin ||
      peMax ||
      pbMax ||
      roeMin ||
      fcfMarginMin ||
      coverageMin ||
      hasGrowthHistory ||
      excludeBanks ||
      activePreset ||
      roicMin ||
      evEbitdaMax ||
      debtToEbitdaMax ||
      interestCoverageMin ||
      grossProfitabilityMin ||
      sbcDilutionMax ||
      pegMax ||
      marketCapBand ||
      turnaroundOnly ||
      altmanSafeOnly ||
      halalCandidate ||
      criteriaLogic === "OR",
  );

  const headerActions = (
    <div className="flex items-center gap-2.5">
      <Link
        to="/morning-brief"
        className="rounded-card border border-border bg-bg-1 px-3 py-1.5 font-mono text-xs text-ink-1 hover:border-accent hover:text-accent transition-colors flex items-center gap-1.5"
      >
        <span>🌅 Morning Brief</span>
      </Link>

      <button
        type="button"
        onClick={() => setIsWizardOpen(true)}
        className="rounded-card border border-accent/70 bg-accent-weak px-3 py-1.5 font-mono text-xs font-semibold text-accent hover:bg-accent/20 transition-colors flex items-center gap-1.5 shadow-xs"
      >
        <span>✨ Strategy Wizard</span>
      </button>

      {selectedIds.length > 0 && (
        <button
          onClick={goCompare}
          className="rounded-card border border-accent/60 bg-accent-weak px-3 py-1.5 font-mono text-xs font-semibold text-accent hover:bg-accent/20 transition-colors"
        >
          Compare Selected ({selectedIds.length}) →
        </button>
      )}

      {data && data.items.length > 0 && (
        <button
          onClick={exportCsv}
          className="rounded-card border border-border bg-bg-1 px-3 py-1.5 font-mono text-xs text-ink-1 hover:border-accent hover:text-ink-0 transition-colors flex items-center gap-1.5"
          title="Download audit-ready formula-transparent CSV"
        >
          <span>⬇ Export CSV</span>
        </button>
      )}
    </div>
  );

  return (
    <Page
      title="Screener"
      description="Deterministic literature screens, multi-metric AND/OR criteria, formula-transparent CSV export, and 5Y sparklines."
      actions={headerActions}
    >
      {/* Strategy Wizard Modal (US-0001) */}
      <StrategyWizard
        isOpen={isWizardOpen}
        onClose={() => setIsWizardOpen(false)}
        onSelectStrategy={handleSelectStrategy}
      />

      {/* Save Preset Modal (US-0009, US-0042) */}
      {isSaveModalOpen && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink-0/60 backdrop-blur-sm animate-fade-in"
        >
          <div className="w-full max-w-md rounded-card border border-border bg-bg-1 p-5 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-2">
              <h3 className="font-heading font-semibold text-sm text-ink-0">Save Custom Screener Preset</h3>
              <button
                type="button"
                onClick={() => setIsSaveModalOpen(false)}
                className="text-ink-2 hover:text-ink-0 font-mono text-xs"
              >
                ✕
              </button>
            </div>
            <div>
              <label htmlFor="preset-name" className="block font-mono text-[10px] uppercase text-ink-2 mb-1">
                Preset Name (concise one-word or joined)
              </label>
              <input
                id="preset-name"
                type="text"
                placeholder="e.g. Fortress_Compounders"
                value={presetNameInput}
                onChange={(e) => setPresetNameInput(e.target.value)}
                className="w-full rounded-card border border-border bg-bg-0 px-3 py-1.5 font-mono text-xs text-ink-0"
              />
            </div>
            <label className="flex items-center gap-2 text-xs text-ink-1 cursor-pointer">
              <input
                type="checkbox"
                checked={autoRunInput}
                onChange={(e) => setAutoRunInput(e.target.checked)}
                className="h-4 w-4 rounded-chip border-border bg-bg-0 accent-accent"
              />
              <span>Auto-run on nightly data refresh (US-0042)</span>
            </label>
            <div className="flex justify-end gap-2 pt-2 border-t border-border">
              <button
                type="button"
                onClick={() => setIsSaveModalOpen(false)}
                className="rounded-card border border-border bg-bg-0 px-3 py-1 text-xs font-mono text-ink-1"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSavePreset}
                disabled={!presetNameInput.trim()}
                className="rounded-card border border-accent bg-accent px-3 py-1 text-xs font-mono font-medium text-bg-0 disabled:opacity-50"
              >
                Save Preset
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Success banner */}
      {saveSuccessMsg && (
        <div role="status" className="rounded-card border border-pos/60 bg-pos/10 px-4 py-2 text-xs font-mono text-pos">
          ✓ {saveSuccessMsg}
        </div>
      )}

      {/* Alerts banner if any triggered */}
      {alertBanners.length > 0 && (
        <div role="alert" className="space-y-1 rounded-card border border-accent/60 bg-accent-weak px-4 py-3 text-sm text-accent">
          <p className="font-semibold text-xs tracking-wider uppercase font-mono">Local Alerts Triggered</p>
          {alertBanners.slice(0, 3).map((b, idx) => (
            <p key={idx} className="font-mono text-xs text-ink-0">
              {b}
            </p>
          ))}
        </div>
      )}

      {/* Filter & Preset Card */}
      <Card padding="md" className="space-y-4 text-xs">
        {/* Canonical Literature Presets (US-0003, US-0005, US-0007, US-0011, US-0022, US-0025, US-0028) */}
        <div className="space-y-2 pb-3 border-b border-border">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[10px] uppercase tracking-widest text-ink-2 font-medium">
              Canonical Presets:
            </span>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setIsSaveModalOpen(true)}
                className="text-[11px] font-mono text-accent hover:underline flex items-center gap-1"
                title="Save current filters as custom preset (US-0009)"
              >
                <span>💾 Save Preset</span>
              </button>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-1.5">
            <button
              type="button"
              onClick={resetFilters}
              className={`px-2.5 py-1 rounded-chip text-xs border font-medium transition-colors ${
                !hasActiveFilters
                  ? "bg-accent-weak border-accent text-accent"
                  : "bg-bg-0 border-border text-ink-1 hover:text-ink-0"
              }`}
            >
              All Names (720)
            </button>

            {CANONICAL_PRESETS.map((p) => {
              const isSelected = activePreset === p.id;
              return (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => applyPreset(p.id)}
                  className={`px-2.5 py-1 rounded-chip text-xs border font-medium transition-colors flex items-center gap-1 ${
                    isSelected
                      ? "bg-accent-weak border-accent text-accent shadow-xs"
                      : "bg-bg-0 border-border text-ink-1 hover:border-accent hover:text-accent"
                  }`}
                >
                  <span>{p.icon}</span>
                  <span>{p.name}</span>
                </button>
              );
            })}

            {/* Custom Saved Presets (US-0009) */}
            {savedPresets.map((sp) => (
              <button
                key={sp.id}
                type="button"
                onClick={() => applyPreset(sp.id)}
                className={`px-2.5 py-1 rounded-chip text-xs border font-medium transition-colors flex items-center gap-1 ${
                  activePreset === sp.id
                    ? "bg-info/20 border-info text-info font-bold"
                    : "bg-bg-0 border-border text-ink-1 hover:border-info hover:text-info"
                }`}
                title={sp.auto_run ? "Auto-run enabled" : undefined}
              >
                <span>⭐</span>
                <span>{sp.name}</span>
                {sp.auto_run && <span className="text-[9px] text-pos">●</span>}
              </button>
            ))}
          </div>
        </div>

        {/* Criteria Logic Toggle (AND / OR) & Status Header (US-0010) */}
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border pb-3">
          <div className="flex items-center gap-3">
            <span className="font-mono text-[10px] uppercase tracking-widest text-ink-2">Criteria Logic:</span>
            <div className="flex rounded-chip border border-border p-0.5 bg-bg-0">
              <button
                type="button"
                onClick={() => updateParam("criteria_logic", "AND")}
                className={`rounded-chip px-2.5 py-0.5 font-mono text-xs transition-colors ${
                  criteriaLogic === "AND"
                    ? "bg-bg-1 text-accent font-semibold shadow-xs"
                    : "text-ink-1 hover:text-ink-0"
                }`}
                title="All active criteria must match (Strict intersection)"
              >
                AND (Strict)
              </button>
              <button
                type="button"
                onClick={() => updateParam("criteria_logic", "OR")}
                className={`rounded-chip px-2.5 py-0.5 font-mono text-xs transition-colors ${
                  criteriaLogic === "OR"
                    ? "bg-bg-1 text-warning font-semibold shadow-xs"
                    : "text-ink-1 hover:text-ink-0"
                }`}
                title="At least one criteria must match (Relaxed union)"
              >
                OR (Relaxed)
              </button>
            </div>
            <span className="font-mono text-[11px] text-ink-2">
              {data ? `${data.count} matches` : "Filtering…"}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="font-mono text-xs text-accent hover:underline flex items-center gap-1"
            >
              <span>{showAdvanced ? "▼ Simple Filters" : "▶ Advanced Metrics (ROIC, EV/EBITDA, Debt, PEG)"}</span>
            </button>
            {hasActiveFilters && (
              <button onClick={resetFilters} className="text-xs text-accent hover:underline font-mono">
                Reset filters
              </button>
            )}
          </div>
        </div>

        {/* Row 1: Currency, Sector, Industry, Signal */}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
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

          <div>
            <label htmlFor="filter-sector" className="block font-mono text-[10px] uppercase text-ink-2 mb-1">
              Sector (GICS)
            </label>
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

          <div>
            <label htmlFor="filter-industry" className="block font-mono text-[10px] uppercase text-ink-2 mb-1">
              Custom Industry
            </label>
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

          <div>
            <label htmlFor="filter-signal" className="block font-mono text-[10px] uppercase text-ink-2 mb-1">
              Signal
            </label>
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

        {/* Row 2: Quantitative Criteria */}
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
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
              placeholder="e.g. 5.5"
              value={compositeMin}
              onChange={(e) => updateParam("composite_min", e.target.value)}
              className="w-full rounded-card border border-border bg-bg-0 px-2.5 py-1 font-mono text-xs text-ink-0 placeholder:text-ink-2"
            />
          </div>

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
              placeholder="e.g. 25"
              value={peMax}
              onChange={(e) => updateParam("pe_max", e.target.value)}
              className="w-full rounded-card border border-border bg-bg-0 px-2.5 py-1 font-mono text-xs text-ink-0 placeholder:text-ink-2"
            />
          </div>

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
              placeholder="e.g. 7"
              value={fcfMarginMin}
              onChange={(e) => updateParam("fcf_margin_min", e.target.value)}
              className="w-full rounded-card border border-border bg-bg-0 px-2.5 py-1 font-mono text-xs text-ink-0 placeholder:text-ink-2"
            />
          </div>

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

        {/* Row 3: Advanced Quantitative Metrics (Expandable) */}
        {showAdvanced && (
          <div className="pt-3 border-t border-border grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6 animate-fade-in">
            <div>
              <label htmlFor="filter-roic-min" className="block font-mono text-[10px] uppercase text-ink-2 mb-1">
                ROIC Min % (US-0034)
              </label>
              <input
                id="filter-roic-min"
                type="number"
                min="0"
                max="100"
                step="1"
                placeholder="e.g. 15"
                value={roicMin}
                onChange={(e) => updateParam("roic_min", e.target.value)}
                className="w-full rounded-card border border-border bg-bg-0 px-2 py-1 font-mono text-xs text-ink-0"
              />
            </div>

            <div>
              <label htmlFor="filter-ev-ebitda" className="block font-mono text-[10px] uppercase text-ink-2 mb-1">
                EV / EBITDA Max
              </label>
              <input
                id="filter-ev-ebitda"
                type="number"
                min="1"
                max="50"
                step="1"
                placeholder="e.g. 10"
                value={evEbitdaMax}
                onChange={(e) => updateParam("ev_ebitda_max", e.target.value)}
                className="w-full rounded-card border border-border bg-bg-0 px-2 py-1 font-mono text-xs text-ink-0"
              />
            </div>

            <div>
              <label htmlFor="filter-debt-ebitda" className="block font-mono text-[10px] uppercase text-ink-2 mb-1">
                Debt/EBITDA Max (US-0011)
              </label>
              <input
                id="filter-debt-ebitda"
                type="number"
                min="0"
                max="20"
                step="0.5"
                placeholder="e.g. 3.0"
                value={debtToEbitdaMax}
                onChange={(e) => updateParam("debt_to_ebitda_max", e.target.value)}
                className="w-full rounded-card border border-border bg-bg-0 px-2 py-1 font-mono text-xs text-ink-0"
              />
            </div>

            <div>
              <label htmlFor="filter-int-cov" className="block font-mono text-[10px] uppercase text-ink-2 mb-1">
                Int. Coverage Min (US-0011)
              </label>
              <input
                id="filter-int-cov"
                type="number"
                min="1"
                max="50"
                step="1"
                placeholder="e.g. 8.0"
                value={interestCoverageMin}
                onChange={(e) => updateParam("interest_coverage_min", e.target.value)}
                className="w-full rounded-card border border-border bg-bg-0 px-2 py-1 font-mono text-xs text-ink-0"
              />
            </div>

            <div>
              <label htmlFor="filter-gp-assets" className="block font-mono text-[10px] uppercase text-ink-2 mb-1">
                GP / Assets Min (US-0007)
              </label>
              <input
                id="filter-gp-assets"
                type="number"
                min="0"
                max="2"
                step="0.05"
                placeholder="e.g. 0.25"
                value={grossProfitabilityMin}
                onChange={(e) => updateParam("gross_profitability_min", e.target.value)}
                className="w-full rounded-card border border-border bg-bg-0 px-2 py-1 font-mono text-xs text-ink-0"
              />
            </div>

            <div>
              <label htmlFor="filter-mcap-band" className="block font-mono text-[10px] uppercase text-ink-2 mb-1">
                Market Cap (US-0020)
              </label>
              <select
                id="filter-mcap-band"
                value={marketCapBand}
                onChange={(e) => updateParam("market_cap_band", e.target.value)}
                className="w-full rounded-card border border-border bg-bg-0 px-2 py-1 text-xs text-ink-0"
              >
                <option value="">All Sizes</option>
                <option value="micro">Micro (&lt; $300M)</option>
                <option value="small">Small ($300M-$2B)</option>
                <option value="mid">Mid ($2B-$10B)</option>
                <option value="large">Large (&gt; $10B)</option>
              </select>
            </div>
          </div>
        )}

        {/* Toggles Strip */}
        <div className="flex flex-wrap items-center gap-5 pt-1 text-xs text-ink-1 border-t border-border">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={hasGrowthHistory}
              onChange={(e) => updateParam("has_growth_history", e.target.checked)}
              className="h-4 w-4 rounded-chip border-border bg-bg-0 accent-accent"
            />
            <span>Has growth history</span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={excludeBanks}
              onChange={(e) => updateParam("exclude_banks", e.target.checked)}
              className="h-4 w-4 rounded-chip border-border bg-bg-0 accent-accent"
            />
            <span>Exclude banks & financials (US-0024)</span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={turnaroundOnly}
              onChange={(e) => updateParam("turnaround_only", e.target.checked)}
              className="h-4 w-4 rounded-chip border-border bg-bg-0 accent-accent"
            />
            <span>Turnaround only (Loss with positive FCF)</span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={altmanSafeOnly}
              onChange={(e) => updateParam("altman_safe_only", e.target.checked)}
              className="h-4 w-4 rounded-chip border-border bg-bg-0 accent-accent"
            />
            <span>Altman Z Safe zone only</span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={halalCandidate}
              onChange={(e) => updateParam("halal_candidate", e.target.checked)}
              className="h-4 w-4 rounded-chip border-border bg-bg-0 accent-accent"
            />
            <span>AAOIFI Halal candidates (US-0004)</span>
          </label>

          {data && (
            <span className="ml-auto font-mono text-ink-2 text-[11px]">
              Showing {data.count} of {data.total} matches
            </span>
          )}
        </div>
      </Card>

      {/* 'Why These Matched' Statistical Summary Strip (US-0038) */}
      {data?.why_matched_summary && data.count > 0 && (
        <div
          role="region"
          aria-label="Why These Matched summary"
          className="rounded-card border border-border bg-bg-1 p-3 flex flex-wrap items-center justify-between gap-4 text-xs"
        >
          <div className="flex items-center gap-2">
            <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-accent bg-accent-weak px-2 py-0.5 rounded">
              Cohort Analysis
            </span>
            <span className="font-semibold text-ink-0">
              Why These {data.count} Companies Matched
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-5 font-mono text-[11px] text-ink-1">
            <div>
              <span className="text-ink-2 mr-1">Median Score:</span>
              <span className="font-bold text-ink-0">
                {data.why_matched_summary.median_composite !== null
                  ? data.why_matched_summary.median_composite.toFixed(2)
                  : "Not reported in filing"}
              </span>
            </div>
            <div>
              <span className="text-ink-2 mr-1">Median P/E:</span>
              <span className="font-bold text-ink-0">
                {data.why_matched_summary.median_pe !== null
                  ? `${data.why_matched_summary.median_pe.toFixed(1)}x`
                  : "Not reported in filing"}
              </span>
            </div>
            <div>
              <span className="text-ink-2 mr-1">Median ROE:</span>
              <span className="font-bold text-ink-0">
                {data.why_matched_summary.median_roe !== null
                  ? `${(data.why_matched_summary.median_roe * 100).toFixed(1)}%`
                  : "Not reported in filing"}
              </span>
            </div>
            {data.why_matched_summary.top_sectors?.length > 0 && (
              <div>
                <span className="text-ink-2 mr-1">Top Sector:</span>
                <span className="text-ink-0 font-medium">
                  {data.why_matched_summary.top_sectors[0].sector} (
                  {data.why_matched_summary.top_sectors[0].count})
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* NULL Diagnostic Warning Banner (US-0049) */}
      {data?.null_warning?.has_null_data_warning && (
        <div
          role="alert"
          className="rounded-card border border-warning/60 bg-warning/10 p-4 text-xs text-ink-0 space-y-1.5"
        >
          <div className="flex items-center gap-2 font-mono font-bold text-warning uppercase text-[11px]">
            <span>⚠️</span>
            <span>Zero Matches Due to Conservative NULL Handling (US-0049)</span>
          </div>
          <p className="text-ink-1 leading-relaxed">
            {data.null_warning.explanation ||
              "Active criteria returned zero candidates. Under our honest NULL handling policy, companies with missing fundamental statements are never assigned artificial placeholder values."}
          </p>
          <div className="flex flex-wrap items-center gap-2 pt-1 font-mono text-[10px] text-ink-2">
            <span>Potential culprits:</span>
            {data.null_warning.null_reasons.map((r, i) => (
              <span key={i} className="bg-bg-0 border border-border px-1.5 py-0.5 rounded text-ink-1">
                {r}
              </span>
            ))}
          </div>
          <div className="pt-2">
            <button
              type="button"
              onClick={() => updateParam("criteria_logic", "OR")}
              className="font-mono text-xs text-accent hover:underline"
            >
              Switch criteria logic to OR →
            </button>
          </div>
        </div>
      )}

      {/* Loading & Error States */}
      {loading && <Spinner label="Screening universe…" />}
      {error && <ErrorBanner message={error} onRetry={load} />}

      {/* Results Table & Instructive Empty State (US-0031) */}
      {data && !loading && (
        <>
          {data.items.length === 0 ? (
            <div className="space-y-6">
              <EmptyState
                title="No names match"
                body="No names match - loosen PE or coverage."
                cta={
                  <button
                    onClick={resetFilters}
                    className="rounded-card border border-accent/60 bg-accent-weak px-3 py-1.5 font-mono text-xs text-accent hover:bg-accent/20 transition-colors"
                  >
                    Reset filters
                  </button>
                }
              />

              {/* Instructive Empty State with 4 Quick-Start Queries (US-0031) */}
              <div className="rounded-card border border-border bg-bg-1 p-5 space-y-3">
                <div className="flex items-center justify-between border-b border-border pb-2">
                  <h4 className="font-heading font-semibold text-xs uppercase tracking-wider text-ink-0">
                    Quick-Start Verified Strategies
                  </h4>
                  <span className="font-mono text-[10px] text-ink-2">1-Click Screener Setup</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                  <div
                    onClick={() => {
                      const next = new URLSearchParams();
                      next.set("currency", "CAD");
                      next.set("preset", "sustainable_dividends");
                      setParams(next, { replace: true });
                    }}
                    className="p-3 rounded border border-border bg-bg-0 hover:border-accent cursor-pointer transition-colors"
                  >
                    <span className="font-bold text-xs text-ink-0 block">🇨🇦 Safe Canadian Dividends</span>
                    <span className="text-[11px] text-ink-2 mt-1 block">
                      CAD-only dividend payers with conservative payout ratio under 60%.
                    </span>
                  </div>

                  <div
                    onClick={() => {
                      const next = new URLSearchParams();
                      next.set("composite_min", "6.5");
                      next.set("pe_max", "20");
                      next.set("roe_min", "15");
                      setParams(next, { replace: true });
                    }}
                    className="p-3 rounded border border-border bg-bg-0 hover:border-accent cursor-pointer transition-colors"
                  >
                    <span className="font-bold text-xs text-ink-0 block">🚀 Discounted Compounders</span>
                    <span className="text-[11px] text-ink-2 mt-1 block">
                      Top-quartile Composite (&gt;= 6.5) with ROE &gt;= 15% and modest P/E &lt;= 20.
                    </span>
                  </div>

                  <div
                    onClick={() => {
                      const next = new URLSearchParams();
                      next.set("altman_safe_only", "true");
                      next.set("exclude_banks", "true");
                      next.set("composite_min", "6.0");
                      setParams(next, { replace: true });
                    }}
                    className="p-3 rounded border border-border bg-bg-0 hover:border-accent cursor-pointer transition-colors"
                  >
                    <span className="font-bold text-xs text-ink-0 block">🛡️ Forensic Clean Sheets</span>
                    <span className="text-[11px] text-ink-2 mt-1 block">
                      Altman Safe zone with zero bank leverage and solid 6.0+ Composite.
                    </span>
                  </div>

                  <div
                    onClick={() => {
                      const next = new URLSearchParams();
                      next.set("turnaround_only", "true");
                      setParams(next, { replace: true });
                    }}
                    className="p-3 rounded border border-border bg-bg-0 hover:border-accent cursor-pointer transition-colors"
                  >
                    <span className="font-bold text-xs text-ink-0 block">🔄 Cash-Flow Turnarounds</span>
                    <span className="text-[11px] text-ink-2 mt-1 block">
                      Accounting losses masking positive, expanding Free Cash Flow.
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <Card padding="none" className="overflow-hidden terminal-card">
              <div className="overflow-x-auto max-h-[75vh]">
                <table className="w-full text-xs">
                  <thead className="sticky top-0 z-10 bg-bg-2/95 backdrop-blur-xs">
                    <tr className="border-b border-border text-left font-mono text-[10px] uppercase tracking-wider text-ink-2">
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
                      <th scope="col" className="px-2.5 py-2.5 text-center">
                        <span>Halal (AAOIFI)</span>
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
                      {/* Inline 5-Year Revenue Sparklines (US-0039) */}
                      <th scope="col" className="px-3 py-2.5 text-center">
                        <span>5Y Rev Trend (US-0039)</span>
                      </th>
                      {/* Book Checklist Scorer (US-0041) */}
                      <th scope="col" className="px-3 py-2.5 text-center">
                        <span>Checklists (US-0041)</span>
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
                          className={`hover:bg-bg-2/60 transition-colors ${isSelected ? "bg-accent-weak" : ""}`}
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
                              {it.currency ?? "Not reported in filing"}
                            </Chip>
                          </td>
                          <td className="px-3 py-2 text-right">
                            <Score value={it.composite} />
                          </td>
                          <td className="px-3 py-2">
                            <SignalBadge signal={it.signal} small />
                          </td>
                          <td className="px-2.5 py-2 text-center">
                            <HalalBadge status={it.halal_status} />
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
                          {/* 5-Year Revenue Sparkline (US-0039) */}
                          <td className="px-3 py-2 text-center">
                            <RevenueSparkline values={it.revenue_sparkline} />
                          </td>
                          {/* Academic Book Checklists (US-0041) */}
                          <td className="px-3 py-2 text-center">
                            <BookChecklists checklists={it.checklists} />
                          </td>
                          <td className="px-3 py-2 text-right font-mono tabular-nums text-ink-1">
                            {it.peer_rank != null && it.peer_n != null ? (
                              <span>
                                #{it.peer_rank} of {it.peer_n}
                              </span>
                            ) : (
                              "Not reported in filing"
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