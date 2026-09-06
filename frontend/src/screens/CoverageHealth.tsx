import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { CoverageHealthOut } from "../api/types";
import { Card, Page, StatTile } from "../components/layout";
import { Spinner } from "../components/ui";

export default function CoverageHealth() {
  const [data, setData] = useState<CoverageHealthOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api
      .coverageHealth()
      .then((res) => {
        if (!cancelled) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message || "Failed to load coverage health matrix");
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <Page title="Universe Data Coverage & Health Dashboard">
        <div className="py-20 flex flex-col items-center justify-center">
          <Spinner />
          <p className="mt-3 text-xs text-ink-2 font-mono">Auditing 720 universe names across SQLite snapshot tables...</p>
        </div>
      </Page>
    );
  }

  if (error || !data) {
    return (
      <Page title="Universe Data Coverage & Health Dashboard">
        <div className="rounded border border-neg/40 bg-neg-weak/30 p-4 text-xs text-neg font-mono">
          {error || "Unable to load coverage data"}
        </div>
      </Page>
    );
  }

  const u = data.universe_summary;
  const p = data.provenance_summary;
  const n = data.null_data_audit;

  return (
    <Page
      title="Universe Data Coverage & Health Dashboard"
      description="Comprehensive health matrix auditing all 720 universe names, seed vs provider backfills, per-pillar sector completeness, and NULL field density."
    >
      {/* KPI Tiles */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6" data-testid="coverage-kpi-grid">
        <StatTile
          label="Universe Coverage"
          value={`${u.total_companies} / ${u.seed_target}`}
          delta={u.total_companies >= u.seed_target ? "100%" : `${((u.total_companies / u.seed_target) * 100).toFixed(0)}%`}
          deltaLabel="target"
          tone="positive"
        />
        <StatTile
          label="Seed Completeness"
          value={`${p.seed_workbook_rows} names`}
          delta={`${p.seed_completeness_pct.toFixed(1)}%`}
          deltaLabel="seed target"
          tone="neutral"
        />
        <StatTile
          label="Provider Backfill"
          value={`${p.provider_backfill_rows} names`}
          subtext="SEC EDGAR & provider ingested"
          tone="neutral"
        />
        <StatTile
          label="NULL Field Density"
          value={`${n.null_percentage.toFixed(1)}%`}
          subtext={`${n.total_null_cells.toLocaleString()} / ${n.total_cells_audited.toLocaleString()} cells`}
          tone={n.null_percentage < 15 ? "positive" : "warning"}
        />
      </div>

      {/* Per-Pillar Sector Completeness Matrix */}
      <Card
        title="Per-Pillar Sector Completeness Matrix"
        subtitle="Verification across Quality, Value, Growth, and Risk pillars by GICS/Custom sector"
        className="mb-6"
      >
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-border text-ink-2 uppercase tracking-wider text-[10px]">
                <th className="py-2.5 px-3">Sector</th>
                <th className="py-2.5 px-3 text-right">Universe Names</th>
                <th className="py-2.5 px-3 text-right">Quality</th>
                <th className="py-2.5 px-3 text-right">Value</th>
                <th className="py-2.5 px-3 text-right">Growth</th>
                <th className="py-2.5 px-3 text-right">Risk</th>
                <th className="py-2.5 px-3 text-right">Avg Pillars</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/40">
              {data.sector_breakdown.map((sec) => (
                <tr key={sec.sector} className="hover:bg-bg-2/30 transition-colors">
                  <td className="py-2 px-3 font-sans font-medium text-ink-0">
                    {sec.sector}
                  </td>
                  <td className="py-2 px-3 text-right text-ink-1">
                    {sec.company_count}
                  </td>
                  <td className="py-2 px-3 text-right">
                    <span className={sec.quality_pct >= 90 ? "text-pos" : sec.quality_pct >= 70 ? "text-warn" : "text-neg"}>
                      {sec.quality_pct.toFixed(0)}%
                    </span>
                  </td>
                  <td className="py-2 px-3 text-right">
                    <span className={sec.value_pct >= 90 ? "text-pos" : sec.value_pct >= 70 ? "text-warn" : "text-neg"}>
                      {sec.value_pct.toFixed(0)}%
                    </span>
                  </td>
                  <td className="py-2 px-3 text-right">
                    <span className={sec.growth_pct >= 90 ? "text-pos" : sec.growth_pct >= 70 ? "text-warn" : "text-neg"}>
                      {sec.growth_pct.toFixed(0)}%
                    </span>
                  </td>
                  <td className="py-2 px-3 text-right">
                    <span className={sec.risk_pct >= 90 ? "text-pos" : sec.risk_pct >= 70 ? "text-warn" : "text-neg"}>
                      {sec.risk_pct.toFixed(0)}%
                    </span>
                  </td>
                  <td className="py-2 px-3 text-right">
                    <div className="inline-flex items-center gap-2 justify-end">
                      <div
                        className="h-2 w-16 bg-bg-2 rounded overflow-hidden"
                        role="progressbar"
                        aria-valuenow={(sec.average_pillars / 4) * 100}
                        aria-valuemin={0}
                        aria-valuemax={100}
                      >
                        <div
                          className="h-full bg-accent transition-all duration-300"
                          style={{ width: `${Math.min(100, Math.max(0, (sec.average_pillars / 4) * 100))}%` }}
                        />
                      </div>
                      <span className="font-semibold text-ink-0 w-10 text-right">
                        {sec.average_pillars.toFixed(1)}/4
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* NULL Field Audit Matrix */}
      <Card
        title="NULL Field Audit & Provenance Health"
        subtitle="Inspection of frequently missing statement line items and ratio inputs across snapshot records"
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 className="font-heading text-xs font-bold uppercase tracking-wider text-ink-1 mb-2">
              Most Frequent NULL Fields
            </h4>
            <div className="space-y-1.5 font-mono text-xs">
              {n.top_missing_fields.map((fn) => (
                <div
                  key={fn.field}
                  className="flex items-center justify-between p-2 rounded bg-bg-0 border border-border/50"
                >
                  <span className="font-medium text-ink-0">{fn.field}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-ink-2 text-[11px]">{fn.missing_count} rows</span>
                    <span className="rounded bg-bg-2 px-1.5 py-0.2 text-[10px] text-ink-1">
                      {fn.pct.toFixed(1)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded border border-border/70 bg-bg-0 p-3.5 flex flex-col justify-between text-xs">
            <div>
              <div className="font-heading font-semibold text-ink-0 uppercase tracking-wider mb-2">
                Audit Policy &amp; Non-Reporting Standards
              </div>
              <ul className="space-y-2 text-ink-1 list-disc list-inside leading-relaxed font-sans">
                <li>
                  <strong className="text-ink-0">Financial Institutions:</strong> Corporate debt, FCF margin, and gross profit are legitimately NULL for banks and insurers per accounting standards.
                </li>
                <li>
                  <strong className="text-ink-0">No Imputed Data:</strong> Missing statement line items are never backfilled with fake zeroes or sector averages; coverage penalties are applied transparently.
                </li>
                <li>
                  <strong className="text-ink-0">Provenance Traceability:</strong> All ingested values maintain source provenance tags traceable to SEC EDGAR accessions.
                </li>
              </ul>
            </div>
            <div className="mt-4 pt-3 border-t border-border/50 text-[11px] font-mono text-ink-2">
              Policy: {n.honest_null_policy}
            </div>
          </div>
        </div>
      </Card>
    </Page>
  );
}
