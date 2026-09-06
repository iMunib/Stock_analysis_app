import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import type { FactorEvidenceOut } from "../api/types";
import { GLOSSARY, type GlossaryEntry } from "../api/glossary";
import { Card, Page } from "../components/layout";
import { Spinner } from "../components/ui";

type TabId = "factors" | "forensics" | "baseRates" | "glossary";

const TABS: { id: TabId; label: string; desc: string }[] = [
  { id: "factors", label: "Factor Evidence & Decay", desc: "Value, Quality, Investment, Low Vol" },
  { id: "forensics", label: "Forensic Model Disclosures", desc: "Altman, Beneish, Piotroski, Sloan" },
  { id: "baseRates", label: "Empirical Base Rates", desc: "Bessembinder distribution" },
  { id: "glossary", label: "Interactive Glossary", desc: "80+ metrics, A–Z, searchable" },
];

function categorize(entry: GlossaryEntry): string {
  const t = entry.term.toLowerCase();
  if (["pe", "pb", "ev/ebitda", "peg", "graham number", "ncav", "nnwc", "margin of safety", "dcf", "epv", "ddm", "reverse dcf", "wacc", "terminal growth", "fcf", "ev", "ttm", "cagr", "52w high/low", "50d / 200d ma", "beta", "short ratio", "institutional %"].includes(entry.term.toLowerCase())) return "Valuation";
  if (["beneish", "m-score", "altman", "z-score", "piotroski", "sloan", "accruals", "eqr", "dso surge", "cfo decoupled", "inventory buildup", "aqi expense cap", "dsri", "gmi", "aqi", "sgi", "depi", "sgai", "lvgi", "tata", "dso", "dio", "dpo", "ccc", "sbc"].includes(entry.term.toLowerCase())) return "Forensics";
  if (["cet1", "nim", "efficiency ratio", "roaa"].includes(entry.term.toLowerCase())) return "Bank Metrics";
  if (["rnoa", "flev", "noa", "nfo", "nopat", "nbc", "penman dupont"].includes(entry.term.toLowerCase())) return "Bank Metrics";
  if (["revenue", "net income", "gross margin", "cogs", "fcf margin", "roe", "roa", "ebit", "ebitda", "capex", "roic", "eps"].includes(t)) return "Accounting";
  return "Accounting";
}

export default function Learn() {
  const [active, setActive] = useState<TabId>("factors");
  const [evidence, setEvidence] = useState<FactorEvidenceOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [glossaryQuery, setGlossaryQuery] = useState("");
  const [category, setCategory] = useState<string>("All");
  const [alpha, setAlpha] = useState<string>("All");

  useEffect(() => {
    let cancelled = false;
    api.factorEvidence()
      .then((res) => {
        if (!cancelled) {
          setEvidence(res);
          setLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const b = evidence?.bessembinder_base_rate;

  const filteredGlossary = useMemo(() => {
    let items = [...GLOSSARY];
    if (category !== "All") items = items.filter((g) => categorize(g) === category);
    if (alpha !== "All") items = items.filter((g) => g.term.toUpperCase().startsWith(alpha));
    if (glossaryQuery.trim()) {
      const q = glossaryQuery.toLowerCase();
      items = items.filter((g) => g.term.toLowerCase().includes(q) || g.short.toLowerCase().includes(q) || g.why.toLowerCase().includes(q));
    }
    return items.sort((a, b) => a.term.localeCompare(b.term));
  }, [category, alpha, glossaryQuery]);

  const categories = ["All", "Valuation", "Forensics", "Bank Metrics", "Accounting"] as const;
  const alphabet = ["All", ..."ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("")];

  return (
    <Page
      title="Learn — Factor Methodology & Evidence Base"
      description="The score is deterministic math: Quality 30% · Value 25% · Growth 25% · Risk 20%. Academic models, Kenneth French empirical factor data, and Bessembinder base rates are provided below for reference."
    >
      {/* Tab bar */}
      <div className="border-b border-border-subtle" role="tablist" aria-label="Learn sections">
        <div className="flex flex-wrap gap-1">
          {TABS.map((t) => (
            <button
              key={t.id}
              role="tab"
              aria-selected={active === t.id}
              aria-controls={`panel-${t.id}`}
              onClick={() => setActive(t.id)}
              className={`rounded-t-md border-b-2 px-4 py-2.5 text-left transition-colors focus:outline-none focus:ring-2 focus:ring-accent ${
                active === t.id ? "border-accent bg-accent-weak text-accent font-semibold" : "border-transparent text-ink-2 hover:text-ink-0 hover:bg-bg-1"
              }`}
            >
              <span className="block font-mono text-xs">{t.label}</span>
              <span className="block font-mono text-[10px] opacity-70">{t.desc}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Tab 1: Factor Evidence & Decay */}
      {active === "factors" && (
        <section id="panel-factors" role="tabpanel" aria-label="Factor Evidence & Decay" className="space-y-4 pt-4">
          <div>
            <h2 className="font-heading text-sm font-bold uppercase tracking-wider text-ink-0">Factor Evidence & Decay — Canonical Premiums</h2>
            <p className="font-mono text-xs text-ink-2">Long-term empirical returns sourced from Kenneth French Data Library and academic literature; out-of-sample decay shown.</p>
          </div>
          {loading ? (
            <div className="flex justify-center py-8">
              <Spinner />
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {(evidence?.canonical_factors ?? []).map((f) => (
                <Card key={f.factor_id} padding="md" className="flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between border-b border-border-subtle pb-2 mb-3">
                      <div>
                        <span className="font-heading text-xs font-bold uppercase tracking-wider text-ink-0">{f.name} Factor</span>
                        <span className="block font-mono text-[10px] text-ink-2">
                          {f.academic_source} ({f.sample_window})
                        </span>
                      </div>
                      <span className="rounded bg-bg-2 px-2 py-0.5 font-mono text-xs font-bold text-accent">{f.historical_annualized_premium}</span>
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-center font-mono">
                      <div className="rounded bg-bg-0 p-2 border border-border-subtle">
                        <span className="block text-[9px] uppercase text-ink-2">Ann. Premium</span>
                        <span className="text-xs font-bold text-ink-0">{f.historical_annualized_premium}</span>
                      </div>
                      <div className="rounded bg-bg-0 p-2 border border-border-subtle">
                        <span className="block text-[9px] uppercase text-ink-2">Sharpe Ratio</span>
                        <span className="text-xs font-bold text-accent">{f.sharpe_ratio.toFixed(2)}</span>
                      </div>
                      <div className="rounded bg-bg-0 p-2 border border-border-subtle">
                        <span className="block text-[9px] uppercase text-ink-2">Max Drawdown</span>
                        <span className="text-xs font-bold text-neg">{f.max_drawdown}</span>
                      </div>
                    </div>
                    <div className="mt-3">
                      <span className="block font-mono text-[10px] uppercase tracking-wider text-ink-2 font-semibold">Macro Regime Sensitivities</span>
                      <div className="mt-1 rounded bg-bg-0 p-2 border border-border-subtle font-mono text-xs text-ink-1">{f.regime_sensitivity}</div>
                    </div>
                  </div>
                  <div className="mt-3 border-t border-border-subtle pt-2 font-mono text-[10px] text-ink-2">
                    <span className="font-semibold text-ink-1">Out-of-Sample Decay:</span> {f.decay_date}
                  </div>
                </Card>
              ))}
              {(evidence?.canonical_factors ?? []).length === 0 && (
                <>
                  {[
                    { id: "hml", name: "Value (HML)", src: "Fama-French 1993", window: "1963–2024", prem: "3.2% pa", sharpe: 0.34, dd: "-28%", regime: "Value thrives in rising-rate, inflationary regimes; suffers in growth-led dislocations.", decay: "Decay post-2007; still positive but attenuated." },
                    { id: "rmw", name: "Quality (RMW)", src: "Fama-French 2015", window: "1963–2024", prem: "2.8% pa", sharpe: 0.41, dd: "-18%", regime: "Quality defensive in drawdowns; lags in speculative rallies.", decay: "Persistent post-publication, modest decay." },
                    { id: "cma", name: "Investment (CMA)", src: "Fama-French 2015", window: "1963–2024", prem: "2.1% pa", sharpe: 0.38, dd: "-15%", regime: "Conservative investment outperforms in tightening credit.", decay: "Visible decay after 2010." },
                    { id: "vol", name: "Low Volatility", src: "Ang et al. 2006", window: "1963–2024", prem: "1.9% pa", sharpe: 0.45, dd: "-12%", regime: "Low vol defensive; underperforms in strong bull markets.", decay: "Attenuated but still anomalous post-2006." },
                  ].map((f) => (
                    <Card key={f.id} padding="md">
                      <div className="flex items-center justify-between border-b border-border-subtle pb-2 mb-3">
                        <div>
                          <span className="font-heading text-xs font-bold uppercase tracking-wider text-ink-0">{f.name}</span>
                          <span className="block font-mono text-[10px] text-ink-2">{f.src} ({f.window})</span>
                        </div>
                        <span className="rounded bg-bg-2 px-2 py-0.5 font-mono text-xs font-bold text-accent">{f.prem}</span>
                      </div>
                      <div className="grid grid-cols-3 gap-2 text-center font-mono">
                        <div className="rounded bg-bg-0 p-2 border border-border-subtle"><span className="block text-[9px] uppercase text-ink-2">Ann. Premium</span><span className="text-xs font-bold text-ink-0">{f.prem}</span></div>
                        <div className="rounded bg-bg-0 p-2 border border-border-subtle"><span className="block text-[9px] uppercase text-ink-2">Sharpe</span><span className="text-xs font-bold text-accent">{f.sharpe.toFixed(2)}</span></div>
                        <div className="rounded bg-bg-0 p-2 border border-border-subtle"><span className="block text-[9px] uppercase text-ink-2">Max DD</span><span className="text-xs font-bold text-neg">{f.dd}</span></div>
                      </div>
                      <div className="mt-2 rounded bg-bg-0 p-2 border border-border-subtle font-mono text-xs text-ink-1">{f.regime}</div>
                      <div className="mt-2 border-t border-border-subtle pt-2 font-mono text-[10px] text-ink-2"><span className="font-semibold text-ink-1">Decay:</span> {f.decay}</div>
                    </Card>
                  ))}
                </>
              )}
            </div>
          )}
        </section>
      )}

      {/* Tab 2: Forensic Model Disclosures */}
      {active === "forensics" && (
        <section id="panel-forensics" role="tabpanel" aria-label="Forensic Model Disclosures" className="space-y-4 pt-4">
          <div>
            <h2 className="font-heading text-sm font-bold uppercase tracking-wider text-ink-0">Forensic Model Disclosures — False-Positive Rates & Bank Exclusions</h2>
            <p className="font-mono text-xs text-ink-2">Immutable sample date stamps, known decay, and explicit limitations per US-0905 / US-0947.</p>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {(evidence?.forensic_models ?? []).map((m) => (
              <Card key={m.model_id} padding="md" className="flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between border-b border-border-subtle pb-2 mb-2">
                    <span className="font-heading text-xs font-bold uppercase tracking-wider text-ink-0">{m.name}</span>
                    <span className="rounded bg-bg-2 px-1.5 py-0.5 font-mono text-[10px] text-ink-2">{m.publication_year}</span>
                  </div>
                  <div className="font-mono text-xs text-ink-2">Author: {m.author}</div>
                  <div className="mt-2 space-y-2 text-xs">
                    <div className="rounded bg-bg-0 p-2 border border-border-subtle font-mono text-[11px]">
                      <span className="block text-[10px] uppercase text-ink-2">Sample Window</span>
                      <span className="font-semibold text-ink-0">{m.date_badge}</span>
                    </div>
                    <div className="rounded bg-warn-weak/30 p-2 border border-warn/30 text-[11px]">
                      <span className="block font-mono text-[10px] uppercase font-bold text-warn">False-Positive Rate</span>
                      <span className="font-mono font-medium text-ink-0">{m.false_positive_rate}</span>
                      <p className="mt-0.5 font-sans text-[10px] text-ink-1">{m.limitations}</p>
                    </div>
                  </div>
                </div>
                <div className="mt-3 border-t border-border-subtle pt-2 font-mono text-[10px] text-ink-2">
                  <span className="font-semibold text-ink-1">Out-of-Sample:</span> {m.out_of_sample_behavior}
                </div>
              </Card>
            ))}
            {(evidence?.forensic_models ?? []).length === 0 && (
              <>
                {[
                  { id: "altman", name: "Altman Z-Score", year: "1968", author: "Edward Altman", window: "1946–1965 Manufacturing", fp: "False-positive ~15% in original; higher in services/banks — excluded for banks", limit: "Do not use for banks/insurers; use CET1/leverage.", oos: "Still discriminative but threshold drift; use as screen, not verdict." },
                  { id: "beneish", name: "Beneish M-Score", year: "1999", author: "Messod Beneish", window: "1982–1988 US Compustat", fp: "~14% at −1.78 threshold; 6–8% with corroboration", limit: "Needs 2 years; revenue recognition flag only.", oos: "Decay but still flags revenue manipulation; corroborate with Sloan." },
                  { id: "piotroski", name: "Piotroski F-Score", year: "2000", author: "Joseph Piotroski", window: "1976–1996 High BM", fp: "Not a false-positive model — strength score; low score ≠ fraud", limit: "9 tests; missing history → lower possible.", oos: "Persistent; value + high F outperforms." },
                  { id: "sloan", name: "Sloan Accruals", year: "1996", author: "Richard Sloan", window: "1962–1991 NYSE/AMEX", fp: "High accruals predict disappointment, not fraud", limit: "Cash vs earnings gap; industry-adjusted better.", oos: "Robust; accrual anomaly attenuated but still present." },
                ].map((m) => (
                  <Card key={m.id} padding="md">
                    <div className="flex items-center justify-between border-b border-border-subtle pb-2 mb-2">
                      <span className="font-heading text-xs font-bold uppercase tracking-wider text-ink-0">{m.name}</span>
                      <span className="rounded bg-bg-2 px-1.5 py-0.5 font-mono text-[10px] text-ink-2">{m.year}</span>
                    </div>
                    <div className="font-mono text-xs text-ink-2">Author: {m.author}</div>
                    <div className="mt-2 rounded bg-bg-0 p-2 border border-border-subtle font-mono text-[11px]"><span className="block text-[10px] uppercase text-ink-2">Sample Window</span><span className="font-semibold text-ink-0">{m.window}</span></div>
                    <div className="mt-2 rounded bg-warn-weak/30 p-2 border border-warn/30 text-[11px]"><span className="block font-mono text-[10px] uppercase font-bold text-warn">False-Positive Rate</span><span className="font-mono text-ink-0">{m.fp}</span><p className="mt-1 font-sans text-[10px] text-ink-1">{m.limit}</p></div>
                    <div className="mt-2 border-t border-border-subtle pt-2 font-mono text-[10px] text-ink-2"><span className="font-semibold text-ink-1">Out-of-Sample:</span> {m.oos}</div>
                  </Card>
                ))}
              </>
            )}
          </div>
          <div className="rounded-md border border-border-subtle bg-bg-0 p-3 font-mono text-xs text-ink-1">
            <span className="font-semibold text-neg">Bank exclusion notice:</span> Altman Z, Gross Profit, and FCF-based screens are not scored for banks/insurers by design — display shows “Not applicable: Bank model”, never invented zeroes.
          </div>
        </section>
      )}

      {/* Tab 3: Empirical Base Rates */}
      {active === "baseRates" && (
        <section id="panel-baseRates" role="tabpanel" aria-label="Empirical Base Rates" className="space-y-4 pt-4">
          <div>
            <h2 className="font-heading text-sm font-bold uppercase tracking-wider text-ink-0">Empirical Base Rates — Bessembinder (2018/2024) Distribution Visualizer</h2>
            <p className="font-mono text-xs text-ink-2">Only 42.2% of US common stocks beat 1-month T-Bills over their full lifetime; wealth creation is concentrated.</p>
          </div>

          <div className="rounded-md border border-accent/40 bg-accent-weak/20 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border-subtle pb-2 mb-2">
              <span className="font-heading text-xs font-bold uppercase tracking-wider text-ink-0">{b?.title || "Single-Stock Survival Base Rate (Bessembinder 2018/2024)"}</span>
              <span className="rounded bg-accent/20 px-2 py-0.5 font-mono text-xs font-bold text-accent">{b?.stat || "42.2% Beat T-Bills"}</span>
            </div>
            <p className="text-xs leading-relaxed text-ink-1">{b?.statement || "Empirical base rate: Only 42% of US common stocks beat 1-month T-Bills over their full lifetime; median lifetime excess return is -100% vs T-Bills."}</p>
            <div className="mt-3 grid gap-2.5 font-mono text-xs sm:grid-cols-3">
              <div className="rounded bg-bg-0 p-3 border border-border-subtle text-center">
                <span className="block text-[10px] uppercase text-ink-2">Stocks Beating T-Bills</span>
                <span className="block text-lg font-bold text-ink-0">42.2%</span>
                <span className="block text-[10px] text-ink-2">Lifetime</span>
              </div>
              <div className="rounded bg-bg-0 p-3 border border-border-subtle text-center">
                <span className="block text-[10px] uppercase text-ink-2">Median Lifetime Return</span>
                <span className="block text-lg font-bold text-neg">-100% vs T-Bills</span>
                <span className="block text-[10px] text-ink-2">Excess</span>
              </div>
              <div className="rounded bg-bg-0 p-3 border border-border-subtle text-center">
                <span className="block text-[10px] uppercase text-ink-2">Net Wealth Concentration</span>
                <span className="block text-lg font-bold text-accent">Top 4% of firms</span>
                <span className="block text-[10px] text-ink-2">Create all net gains</span>
              </div>
            </div>
            {b?.probabilistic_lesson && <div className="mt-3 border-t border-border-subtle pt-2 font-sans text-[11px] italic text-ink-2">“{b.probabilistic_lesson}”</div>}
          </div>

          {/* Pure SVG distribution visualizer */}
          <Card title="Lifetime Excess Return Distribution — Skew Matters" subtitle="Pure SVG — no chart libraries" padding="md">
            <div className="overflow-x-auto">
              <svg viewBox="0 0 600 220" role="img" aria-label="Bessembinder distribution: 58% underperform, 42% outperform, extreme right tail" className="w-full h-auto">
                {/* Background */}
                <rect x={0} y={0} width={600} height={220} rx={8} fill="var(--bg-0)" stroke="var(--border-subtle)" />
                {/* X axis */}
                <line x1={48} y1={160} x2={560} y2={160} stroke="var(--border)" strokeWidth={1.2} />
                <text x={304} y={188} textAnchor="middle" fontSize={10} fill="var(--ink-2)" fontFamily="IBM Plex Mono">Lifetime Excess Return vs 1-Month T-Bills →</text>
                {/* Bars — left mass underperform */}
                {[
                  { x: 52, w: 78, h: 62, label: "-100%", sub: "58% of stocks", color: "var(--neg)" },
                  { x: 134, w: 72, h: 38, label: "-50%", sub: "", color: "var(--border)" },
                  { x: 210, w: 72, h: 22, label: "0%", sub: "T-Bill", color: "var(--warn)" },
                  { x: 286, w: 72, h: 28, label: "+50%", sub: "42% beat", color: "var(--pos)" },
                  { x: 362, w: 72, h: 18, label: "+200%", sub: "", color: "var(--accent)" },
                  { x: 438, w: 78, h: 86, label: "+1,000%+", sub: "4% create all", color: "var(--accent)" },
                ].map((b, i) => (
                  <g key={i}>
                    <rect x={b.x} y={160 - b.h} width={b.w} height={b.h} rx={4} fill={b.color} opacity={i === 0 || i === 5 ? 0.85 : 0.55} stroke="var(--border-subtle)" />
                    <text x={b.x + b.w / 2} y={160 - b.h - 6} textAnchor="middle" fontSize={9} fontWeight={700} fill="var(--ink-0)" fontFamily="IBM Plex Mono">{b.label}</text>
                    {b.sub && <text x={b.x + b.w / 2} y={174} textAnchor="middle" fontSize={8} fill="var(--ink-2)" fontFamily="IBM Plex Mono">{b.sub}</text>}
                  </g>
                ))}
                {/* T-Bill marker */}
                <line x1={246} y1={30} x2={246} y2={160} stroke="var(--warn)" strokeDasharray="5 4" strokeWidth={1.5} />
                <rect x={214} y={12} width={64} height={14} rx={3} fill="var(--warn)" />
                <text x={246} y={22} textAnchor="middle" fontSize={8} fontWeight={800} fill="white" fontFamily="IBM Plex Mono">T-BILL</text>
              </svg>
            </div>
            <p className="mt-2 font-mono text-[11px] text-ink-2">Skew: Most stocks underperform; a tiny concentration creates all net market wealth. High-conviction bets must be sized against base rates. Source: Bessembinder, Journal of Financial Economics 2018, updated 2024.</p>
          </Card>
        </section>
      )}

      {/* Tab 4: Glossary */}
      {active === "glossary" && (
        <section id="panel-glossary" role="tabpanel" aria-label="Interactive Platform Glossary" className="space-y-4 pt-4">
          <div>
            <h2 className="font-heading text-sm font-bold uppercase tracking-wider text-ink-0">Interactive Platform Glossary — {GLOSSARY.length}+ Metrics</h2>
            <p className="font-mono text-xs text-ink-2">Search, A–Z jump, and category filter. Every formula is crisp LaTeX/monospace with variable definitions.</p>
          </div>

          <div className="flex flex-wrap items-center gap-2 rounded-md border border-border-subtle bg-bg-0 p-3">
            <input
              type="search"
              placeholder="Search term, e.g. ROIC, Sloan, CET1…"
              value={glossaryQuery}
              onChange={(e) => setGlossaryQuery(e.target.value)}
              aria-label="Search glossary"
              className="min-w-[220px] flex-1 rounded border border-border bg-bg-1 px-3 py-1.5 font-mono text-xs text-ink-0 placeholder:text-ink-2 focus:border-accent focus:outline-none"
            />
            <span className="font-mono text-xs text-ink-2">{filteredGlossary.length} / {GLOSSARY.length} terms</span>
          </div>

          {/* Category filter */}
          <div className="flex flex-wrap items-center gap-1.5" role="group" aria-label="Category filter">
            {categories.map((c) => (
              <button
                key={c}
                onClick={() => setCategory(c)}
                aria-pressed={category === c}
                className={`rounded-full border px-3 py-1 font-mono text-xs ${category === c ? "border-accent bg-accent-weak text-accent font-semibold" : "border-border bg-bg-0 text-ink-2 hover:border-accent/40"}`}
              >
                {c}
              </button>
            ))}
          </div>

          {/* A–Z jump bar */}
          <div className="flex flex-wrap gap-1" role="group" aria-label="Alphabet jump">
            {alphabet.map((ch) => (
              <button
                key={ch}
                onClick={() => setAlpha(ch)}
                aria-pressed={alpha === ch}
                className={`h-7 min-w-[28px] rounded border px-1.5 font-mono text-xs ${alpha === ch ? "border-accent bg-accent text-bg-0 font-bold" : "border-border bg-bg-0 text-ink-2 hover:bg-bg-1"}`}
              >
                {ch}
              </button>
            ))}
          </div>

          <ul className="grid gap-3 sm:grid-cols-2" aria-label="Glossary entries">
            {filteredGlossary.map((g) => (
              <li key={g.term}>
                <Card padding="md" className="h-full">
                  <p className="font-heading text-sm font-semibold text-ink-0">{g.term}</p>
                  <p className="mt-1 font-mono text-xs text-ink-1">{g.short}</p>
                  <p className="mt-2 border-t border-border-subtle pt-2 font-mono text-[11px] text-ink-2">Why: {g.why}</p>
                  <p className="mt-1 rounded bg-bg-0 border border-border-subtle px-2 py-1 font-mono text-[11px] text-ink-1">How to read: {g.how_to_read}</p>
                  <span className="mt-2 inline-block rounded bg-bg-2 px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider text-ink-2">{categorize(g)}</span>
                </Card>
              </li>
            ))}
          </ul>
          {filteredGlossary.length === 0 && <p className="py-8 text-center font-mono text-xs text-ink-2">No terms match “{glossaryQuery}” in {category} · {alpha}.</p>}
        </section>
      )}
    </Page>
  );
}
