import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { FactorEvidenceOut } from "../api/types";
import { GLOSSARY } from "../api/glossary";
import { Card, Page } from "../components/layout";
import { Spinner } from "../components/ui";

export default function Learn() {
  const [evidence, setEvidence] = useState<FactorEvidenceOut | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    api
      .factorEvidence()
      .then((res) => {
        if (!cancelled) {
          setEvidence(res);
          setLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const b = evidence?.bessembinder_base_rate;

  return (
    <Page
      title="Learn - Factor Methodology & Evidence Base"
      description='The score is deterministic math: Quality 30% · Value 25% · Growth 25% · Risk 20%. Academic models, Kenneth French empirical factor data, and Bessembinder base rates are provided below for reference.'
    >
      {/* Bessembinder Base-Rate Humility Banner (US-0676) */}
      <div className="mb-6 rounded-card border border-accent/40 bg-accent-weak/20 p-4 shadow-card">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 pb-2 mb-2">
          <div className="flex items-center gap-2">
            <span className="font-heading text-xs font-bold uppercase tracking-wider text-ink-0">
              {b?.title || "Empirical Single-Stock Survival Base-Rate (Bessembinder 2018/2024)"}
            </span>
          </div>
          <span className="rounded bg-accent/20 px-2 py-0.5 font-mono text-xs font-bold text-accent">
            {b?.stat || "42% Lifetime Success Rate"}
          </span>
        </div>
        <p className="text-xs text-ink-1 leading-relaxed">
          {b?.statement ||
            "Empirical Base Rate: Only 42% of US common stocks beat 1-month T-Bills over their full lifetime; the median stock generates a cumulative lifetime return of -100% relative to T-Bills (Bessembinder 2018/2024)."}
        </p>
        <div className="mt-3 grid grid-cols-1 sm:grid-cols-3 gap-2.5 font-mono text-xs">
          <div className="rounded bg-bg-0 p-2 border border-border/50">
            <span className="text-[10px] text-ink-2 uppercase block">Stocks Beating T-Bills</span>
            <span className="font-bold text-ink-0 text-sm">42.2%</span>
          </div>
          <div className="rounded bg-bg-0 p-2 border border-border/50">
            <span className="text-[10px] text-ink-2 uppercase block">Lifetime Median Return</span>
            <span className="font-bold text-neg text-sm">-100% vs T-Bills</span>
          </div>
          <div className="rounded bg-bg-0 p-2 border border-border/50">
            <span className="text-[10px] text-ink-2 uppercase block">Concentration of Net Wealth</span>
            <span className="font-bold text-accent text-sm">Top 4% of firms</span>
          </div>
        </div>
        {b?.probabilistic_lesson && (
          <div className="mt-3 pt-2 border-t border-border/50 text-[11px] font-sans italic text-ink-2">
            "{b.probabilistic_lesson}"
          </div>
        )}
      </div>

      {/* Canonical Factor Performance & Regime Sensitivity Cards (US-0919, US-0060, US-0063) */}
      <div className="mb-8">
        <div className="mb-3">
          <h2 className="font-heading text-sm font-bold uppercase tracking-wider text-ink-0">
            Canonical Factor Performance &amp; Macro Regime Sensitivities
          </h2>
          <p className="text-xs text-ink-2 font-mono">
            Long-term empirical returns sourced from Kenneth French Data Library and academic literature
          </p>
        </div>

        {loading ? (
          <div className="py-8 flex justify-center"><Spinner /></div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {evidence?.canonical_factors?.map((f) => (
              <Card key={f.factor_id} padding="md" className="flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between border-b border-border/70 pb-2 mb-3">
                    <div>
                      <span className="font-heading text-xs font-bold uppercase tracking-wider text-ink-0">
                        {f.name} Factor
                      </span>
                      <span className="block text-[10px] font-mono text-ink-2">
                        {f.academic_source} ({f.sample_window})
                      </span>
                    </div>
                    <span className="rounded bg-bg-2 px-2 py-0.5 font-mono text-xs font-bold text-accent">
                      {f.historical_annualized_premium}
                    </span>
                  </div>

                  {/* Return Metrics */}
                  <div className="grid grid-cols-3 gap-2 mb-3 text-center font-mono">
                    <div className="rounded bg-bg-0 p-2 border border-border/40">
                      <span className="text-[9px] text-ink-2 uppercase block">Ann. Premium</span>
                      <span className="text-xs font-bold text-ink-0">{f.historical_annualized_premium}</span>
                    </div>
                    <div className="rounded bg-bg-0 p-2 border border-border/40">
                      <span className="text-[9px] text-ink-2 uppercase block">Sharpe Ratio</span>
                      <span className="text-xs font-bold text-accent">{f.sharpe_ratio.toFixed(2)}</span>
                    </div>
                    <div className="rounded bg-bg-0 p-2 border border-border/40">
                      <span className="text-[9px] text-ink-2 uppercase block">Max Drawdown</span>
                      <span className="text-xs font-bold text-neg">{f.max_drawdown}</span>
                    </div>
                  </div>

                  {/* Macro Regime Sensitivities (US-0060) */}
                  <div className="mb-3">
                    <span className="block text-[10px] font-mono uppercase tracking-wider text-ink-2 mb-1 font-semibold">
                      Macro Regime Sensitivities:
                    </span>
                    <div className="rounded bg-bg-0 p-2 border border-border/40 text-xs font-mono text-ink-1">
                      {f.regime_sensitivity}
                    </div>
                  </div>
                </div>

                {/* Factor Decay Note (US-0063) */}
                <div className="border-t border-border/50 pt-2 text-[10px] font-mono text-ink-2">
                  <span className="font-semibold text-ink-1">Decay Profile:</span> {f.decay_date}
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Academic Models Date Stamps & False-Positive Rates (US-0905, US-0947, US-0063) */}
      <div className="mb-8">
        <div className="mb-3">
          <h2 className="font-heading text-sm font-bold uppercase tracking-wider text-ink-0">
            Academic Forensic &amp; Fundamental Model Disclosures
          </h2>
          <p className="text-xs text-ink-2 font-mono">
            Immutable sample date stamps, known decay profiles, and empirical false-positive rate disclosures
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {evidence?.forensic_models?.map((m) => (
            <Card key={m.model_id} padding="md" className="flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between border-b border-border/70 pb-2 mb-2">
                  <span className="font-heading text-xs font-bold uppercase tracking-wider text-ink-0">
                    {m.name}
                  </span>
                  <span className="rounded bg-bg-2 px-1.5 py-0.5 font-mono text-[10px] text-ink-2">
                    {m.publication_year}
                  </span>
                </div>

                <div className="text-xs font-mono text-ink-2 mb-2">
                  Author: {m.author}
                </div>

                <div className="space-y-2 text-xs">
                  <div className="rounded bg-bg-0 p-2 border border-border/40 font-mono text-[11px]">
                    <span className="text-ink-2 block text-[10px] uppercase">Sample Window (US-0905)</span>
                    <span className="text-ink-0 font-semibold">{m.date_badge}</span>
                  </div>

                  <div className="rounded bg-warn-weak/30 p-2 border border-warn/30 text-[11px]">
                    <span className="font-mono text-warn font-bold block text-[10px] uppercase">
                      False-Positive Rate (US-0947)
                    </span>
                    <span className="text-ink-0 font-medium font-mono">{m.false_positive_rate}</span>
                    <p className="text-[10px] text-ink-1 mt-0.5 font-sans">{m.limitations}</p>
                  </div>
                </div>
              </div>

              <div className="mt-3 border-t border-border/50 pt-2 text-[10px] font-mono text-ink-2">
                <span className="font-semibold text-ink-1">Out-of-Sample Decay:</span> {m.out_of_sample_behavior}
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* Metric Glossary Section */}
      <div>
        <div className="mb-3">
          <h2 className="font-heading text-sm font-bold uppercase tracking-wider text-ink-0">
            Platform Metric Glossary
          </h2>
          <p className="text-xs text-ink-2 font-mono">Definitions and rationale for core snapshot line items</p>
        </div>

        <ul className="grid gap-3 sm:grid-cols-2" aria-label="Glossary">
          {GLOSSARY.map((g) => (
            <li key={g.term}>
              <Card padding="md" className="h-full">
                <p className="font-semibold text-ink-0 text-sm font-heading">{g.term}</p>
                <p className="mt-1 text-xs text-ink-1 leading-relaxed">{g.short}</p>
                <p className="mt-2 text-[11px] text-ink-2 font-mono border-t border-border pt-2">Why: {g.why}</p>
              </Card>
            </li>
          ))}
        </ul>
      </div>
    </Page>
  );
}