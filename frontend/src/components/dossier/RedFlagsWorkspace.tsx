import React, { useEffect, useState } from "react";
import { api } from "../../api/client";
import type { BenfordOut, ForensicsSummaryOut, TrajectoryOut, WorkingCapitalOut, RestatementsOut, GoodwillRiskOut, DilutionOut } from "../../api/types";
import { Card, Chip } from "../layout";
import BenfordChart from "./BenfordChart";
import AsFiledToggle from "./AsFiledToggle";

interface RedFlagsWorkspaceProps {
  companyId: string;
  currency?: string | null;
}

const Disclaimer: React.FC = () => (
  <p className="text-[11px] font-mono text-ink-2 border-t border-border pt-2 mt-3">
    Personal research software, not investment advice. Forensic models are probabilistic screening tools, not legal findings.
  </p>
);

export const RedFlagsWorkspace: React.FC<RedFlagsWorkspaceProps> = ({ companyId, currency }) => {
  const [summary, setSummary] = useState<ForensicsSummaryOut | null>(null);
  const [benford, setBenford] = useState<BenfordOut | null>(null);
  const [trajectory, setTrajectory] = useState<TrajectoryOut | null>(null);
  const [wc, setWc] = useState<WorkingCapitalOut | null>(null);
  const [restatements, setRestatements] = useState<RestatementsOut | null>(null);
  const [goodwill, setGoodwill] = useState<GoodwillRiskOut | null>(null);
  const [dilution, setDilution] = useState<DilutionOut | null>(null);
  const [asFiledMode, setAsFiledMode] = useState<"filed" | "restated">("filed");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [noteDraft, setNoteDraft] = useState<string>("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    Promise.allSettled([
      api.forensicsSummary(companyId),
      api.forensicsBenford(companyId),
      api.trajectory(companyId),
      api.workingCapital(companyId),
      api.restatements(companyId),
      api.goodwillRisk(companyId),
      api.dilution(companyId),
    ]).then((results) => {
      if (cancelled) return;
      const [s, b, t, w, r, g, d] = results;
      if (s.status === "fulfilled") setSummary(s.value);
      if (b.status === "fulfilled") setBenford(b.value);
      if (t.status === "fulfilled") setTrajectory(t.value);
      if (w.status === "fulfilled") setWc(w.value);
      if (r.status === "fulfilled") setRestatements(r.value);
      if (g.status === "fulfilled") setGoodwill(g.value);
      if (d.status === "fulfilled") setDilution(d.value);
      const anyFailed = results.some((x) => x.status === "rejected");
      if (anyFailed && !s) setError("Some forensic sections failed to load");
      setLoading(false);
    });
    // Load local notes
    try {
      const saved = localStorage.getItem(`forensic_notes:${companyId}`);
      if (saved) setNoteDraft(saved);
    } catch {}
    return () => { cancelled = true; };
  }, [companyId]);

  const saveNote = () => {
    try {
      localStorage.setItem(`forensic_notes:${companyId}`, noteDraft.slice(0, 2000));
    } catch {}
  };

  if (loading) {
    return <p className="text-xs text-ink-2">Loading Red Flags workspace…</p>;
  }
  if (error && !summary) {
    return <p className="text-xs text-neg">{error}</p>;
  }

  const hasRestatement = Boolean(restatements?.items.some((it) => it.has_restatement));

  return (
    <div className="space-y-5" aria-label="Forensic Red Flags Workspace">
      {/* Header: Health score + plain-language summary */}
      {summary && (
        <Card
          title="Consolidated Forensic Summary"
          subtitle={`Health ${summary.forensic_health_score}/100 · ${summary.forensic_risk_tier} · ${summary.flag_count} flags`}
          padding="md"
        >
          <div className="flex flex-wrap items-center gap-2 mb-3">
            <span className={`px-2.5 py-1 rounded-chip text-xs font-mono font-bold border ${
              summary.forensic_health_score >= 80 ? "bg-pos-weak text-pos border-pos/30" :
              summary.forensic_health_score >= 50 ? "bg-warn-weak text-warn border-warn/30" : "bg-neg-weak text-neg border-neg/30"
            }`}>
              {summary.forensic_risk_tier}
            </span>
            <span className="font-mono text-xs text-ink-1">{summary.flag_count} active flags</span>
            {summary.cross_model_divergence && (
              <span className="px-2 py-0.5 rounded bg-warn-weak border border-warn/30 text-warn text-xs font-mono">
                Divergence: {summary.cross_model_divergence}
              </span>
            )}
          </div>

          <p className="text-sm text-ink-0 leading-relaxed font-medium bg-bg-2/40 p-2.5 rounded border border-border">
            What could go wrong: {summary.plain_language_summary}
          </p>

          <div className="mt-3 flex flex-wrap gap-1.5">
            {summary.flags.map((f) => (
              <Chip
                key={f.code}
                tone={f.severity === "critical" ? "negative" : f.severity === "elevated" ? "warning" : "info"}
                size="sm"
              >
                {f.code} · {f.severity}
              </Chip>
            ))}
            {summary.flags.length === 0 && <span className="text-xs text-ink-2">Zero red flags - clean forensic profile.</span>}
          </div>

          {summary.beneish && summary.distress && summary.sloan && (
            <div className="mt-3 grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
              <div className="p-2.5 rounded border border-border bg-bg-0">
                <span className="font-mono text-[10px] uppercase text-ink-2 block">Beneish M-Score</span>
                <span className={`font-mono font-bold text-sm ${(summary.beneish as any).is_manipulator ? "text-neg" : "text-pos"}`}>
                  {(summary.beneish as any).m_score ?? "Not reported in filing"} {(summary.beneish as any).is_manipulator ? "(Manipulator)" : "(Clean)"}
                </span>
                <span className="text-[10px] text-ink-2 block">Threshold −1.78</span>
              </div>
              <div className="p-2.5 rounded border border-border bg-bg-0">
                <span className="font-mono text-[10px] uppercase text-ink-2 block">Altman Z</span>
                <span className={`font-mono font-bold text-sm ${(summary.distress as any).zone === "Distress" ? "text-neg" : (summary.distress as any).zone === "Grey" ? "text-warn" : "text-pos"}`}>
                  {(summary.distress as any).active_z ?? "Not reported in filing"} · {(summary.distress as any).zone ?? "Not reported in filing"}
                </span>
                <span className="text-[10px] text-ink-2 block">{(summary.distress as any).model_used ?? ""}</span>
              </div>
              <div className="p-2.5 rounded border border-border bg-bg-0">
                <span className="font-mono text-[10px] uppercase text-ink-2 block">Sloan Accruals</span>
                <span className="font-mono font-bold text-sm text-ink-0">{(summary.sloan as any).accrual_ratio ?? "Not reported in filing"}</span>
                <span className="text-[10px] text-ink-2 block">{(summary.sloan as any).flag ?? (summary.sloan as any).quality_rating ?? ""}</span>
              </div>
            </div>
          )}

          {/* Local annotation */}
          <div className="mt-4 border-t border-border pt-3">
            <label htmlFor={`forensic-note-${companyId}`} className="font-mono text-[11px] uppercase text-ink-2">Investigator notes (local only, 2000 chars)</label>
            <textarea
              id={`forensic-note-${companyId}`}
              value={noteDraft}
              onChange={(e) => setNoteDraft(e.target.value.slice(0, 2000))}
              placeholder="Annotate flags with your own evidence links…"
              className="mt-1 w-full min-h-[64px] rounded border border-border bg-bg-0 p-2 text-xs text-ink-0 placeholder:text-ink-2"
              rows={2}
            />
            <div className="mt-1 flex items-center justify-between">
              <span className="font-mono text-[10px] text-ink-2">{noteDraft.length}/2000</span>
              <button type="button" onClick={saveNote} className="px-2.5 py-1 rounded border border-accent/40 bg-accent-weak text-accent text-xs font-mono hover:bg-accent/20">
                Save locally
              </button>
            </div>
          </div>

          <Disclaimer />
        </Card>
      )}

      {/* Hindenburg-style First-Pass Checklist */}
      {summary && (
        <Card title="Hindenburg-Style First-Pass Checklist" subtitle="Professional skepticism systematized - 5 lenses">
          <div className="space-y-2 text-xs">
            {[
              { label: "Related-party signals", pass: !(summary.shenanigans as any)?.triggered_flags?.includes("RELATED_PARTY"), note: "No related-party flag detected locally" },
              { label: "Revenue recognition (DSO surge)", pass: !(summary.shenanigans as any)?.triggered_flags?.includes("RED_FLAG_DSO_SURGE"), note: (summary.shenanigans as any)?.working_capital?.dso?.years?.length ? `Flagged FY ${ (summary.shenanigans as any).working_capital.dso.years.join(", ")}` : "No DSO channel-stuffing divergence" },
              { label: "Auditor change / going-concern", pass: !(summary.shenanigans as any)?.triggered_flags?.includes("GOING_CONCERN_LANGUAGE") && !(summary.shenanigans as any)?.triggered_flags?.includes("AUDITOR_CHANGE"), note: (summary.shenanigans as any)?.auditor?.going_concern_detected ? "Going-concern language flagged" : "No auditor/going-concern flag" },
              { label: "Beneish manipulation screen", pass: !(summary as any).beneish?.is_manipulator, note: (summary as any).beneish?.is_manipulator ? `M=${(summary as any).beneish.m_score} > -1.78` : "Clean (M ≤ -1.78)" },
              { label: "Distress screen", pass: (summary as any).distress?.zone !== "Distress", note: `Altman ${(summary as any).distress?.zone} zone` },
            ].map((item) => (
              <div key={item.label} className={`flex items-center justify-between p-2 rounded border ${item.pass ? "bg-pos-weak/40 border-pos/20" : "bg-neg-weak/40 border-neg/20"}`}>
                <span className="font-medium text-ink-0">{item.label}</span>
                <span className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded-chip text-[11px] font-mono font-bold border ${item.pass ? "bg-pos text-white border-pos" : "bg-neg text-white border-neg"}`}>{item.pass ? "PASS" : "FAIL"}</span>
                  <span className="text-ink-2 hidden sm:inline">{item.note}</span>
                </span>
              </div>
            ))}
          </div>
          <Disclaimer />
        </Card>
      )}

      {/* Benford Chart */}
      <BenfordChart data={benford} />

      {/* Cross-Model Divergence already in summary; dedicated card */}
      {summary?.cross_model_divergence && (
        <Card title="Cross-Model Divergence" subtitle="Beneish vs Altman vs Sloan - when lenses disagree">
          <p className="text-sm text-warn font-medium bg-warn-weak/30 p-2.5 rounded border border-warn/30">{summary.cross_model_divergence}</p>
          <p className="text-xs text-ink-1 mt-2 leading-relaxed">Divergence is informational - models have 15–20% false-positive rates and different sample windows. Multiple lenses beat one.</p>
        </Card>
      )}

      {/* Trajectory: 10-year Revenue / Margins / FCF - pure SVG */}
      {trajectory && trajectory.points.length >= 2 && (
        <Card title="10-Year Synchronized Trajectory" subtitle={`Revenue, gross/operating margins, FCF in native ${currency ?? trajectory.currency ?? ""} - inflection markers where YoY >15%`}>
          <TrajectorySVG points={trajectory.points} currency={currency ?? trajectory.currency} />
          <Disclaimer />
        </Card>
      )}

      {/* Working Capital CCC */}
      {wc && (
        <Card title="Working Capital - Cash Conversion Cycle" subtitle="DSO + DIO − DPO (days) - operational cash reality">
          {wc.data_available ? (
            <div className="space-y-3">
              <CCCSVG series={wc.series} />
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-border text-left font-mono text-[10px] uppercase text-ink-2">
                      <th className="py-1 pr-2">FY</th>
                      <th className="py-1 pr-2 text-right">DSO</th>
                      <th className="py-1 pr-2 text-right">DIO</th>
                      <th className="py-1 pr-2 text-right">DPO</th>
                      <th className="py-1 text-right font-bold">CCC</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {wc.series.slice(-5).map((r) => (
                      <tr key={r.fiscal_year}>
                        <td className="py-1 font-mono">{r.fiscal_year}</td>
                        <td className="py-1 text-right font-mono">{r.dso ?? "Not reported in filing"}</td>
                        <td className="py-1 text-right font-mono">{r.dio ?? "Not reported in filing"}</td>
                        <td className="py-1 text-right font-mono">{r.dpo ?? "Not reported in filing"}</td>
                        <td className="py-1 text-right font-mono font-bold">{r.ccc ?? "Not reported in filing"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <p className="text-xs text-ink-1">{(wc as any).reason ?? "Working-capital inputs missing for this company."} - honest NULL, not invented.</p>
          )}
          <Disclaimer />
        </Card>
      )}

      {/* Goodwill vs Tangible strip */}
      {goodwill && (
        <Card title="Goodwill vs Tangible Assets - Impairment Risk" subtitle="Proxy intangible ratio (assets − equity − cash − AR − inventory − PPE)/assets">
          <div className="space-y-2">
            <div className="flex flex-wrap gap-2 text-xs">
              <span className={`px-2 py-0.5 rounded-chip font-mono border ${ (goodwill as any).goodwill?.triggered ? "bg-neg-weak text-neg border-neg/30" : "bg-pos-weak text-pos border-pos/30"}`}>
                {(goodwill as any).goodwill?.triggered ? "GOODWILL_BLOAT ≥40%" : "No goodwill bloat"}
              </span>
              {(goodwill as any).serial_acquirer?.triggered && (
                <span className="px-2 py-0.5 rounded-chip font-mono bg-warn-weak text-warn border border-warn/30">SERIAL_ACQUIRER - asset jumps &gt;20% in 2 of last 3 FY</span>
              )}
            </div>
            {goodwill.strip.length > 0 ? (
              <GoodwillSVG strip={goodwill.strip} />
            ) : (
              <p className="text-xs text-ink-2">No strip - goodwill not separately disclosed; proxy shown informationally.</p>
            )}
            <p className="text-xs text-ink-1 leading-relaxed">{(goodwill as any).goodwill?.note ?? "Goodwill requires separate disclosure; owner workbook proxy is informational only."}</p>
          </div>
          <Disclaimer />
        </Card>
      )}

      {/* Dilution tracker */}
      {dilution && dilution.series.length > 0 && (
        <Card title="Share Dilution Tracker - SBC vs Organic Buybacks" subtitle="Share count history with per-share annotation">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border text-left font-mono text-[10px] uppercase text-ink-2">
                  <th className="py-1 pr-2">FY</th>
                  <th className="py-1 pr-2 text-right">Shares</th>
                  <th className="py-1 pr-2 text-right">Δ</th>
                  <th className="py-1 pr-2 text-right">Δ%</th>
                  <th className="py-1 pr-2">Annotation</th>
                  <th className="py-1">SBC</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {dilution.series.map((r) => (
                  <tr key={r.fiscal_year}>
                    <td className="py-1 font-mono">{r.fiscal_year}</td>
                    <td className="py-1 text-right font-mono">{r.shares != null ? Number(r.shares).toLocaleString() : "0.00"}</td>
                    <td className="py-1 text-right font-mono">{r.delta != null ? (r.delta > 0 ? `+${r.delta.toLocaleString()}` : r.delta.toLocaleString()) : "0.00"}</td>
                    <td className={`py-1 text-right font-mono ${r.delta_pct != null && r.delta_pct < 0 ? "text-pos" : r.delta_pct != null && r.delta_pct > 0 ? "text-neg" : ""}`}>{r.delta_pct ?? "0.00"}{r.delta_pct != null ? "%" : ""}</td>
                    <td className="py-1">
                      {r.annotation ? <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono border ${r.annotation === "net_buyback" ? "bg-pos-weak text-pos border-pos/30" : r.annotation === "issuance" ? "bg-neg-weak text-neg border-neg/30" : "bg-bg-0 text-ink-2"}`}>{r.annotation}</span> : "0.00"}
                    </td>
                    <td className="py-1 font-mono">{r.sbc != null ? Number(r.sbc).toLocaleString() : "0.00"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-[11px] text-ink-2 mt-2 leading-relaxed">SBC dilution is shown separately where disclosed; net buyback = gross buybacks − SBC dilution offset. Readers should reconcile per-share growth after dilution.</p>
          <Disclaimer />
        </Card>
      )}

      {/* Restatements toggle */}
      {restatements && (
        <Card title="As-Filed vs As-Restated" subtitle="Original filing vs retroactive provider rewrites - history never silently rewritten">
          <AsFiledToggle value={asFiledMode} onChange={setAsFiledMode} hasRestatement={hasRestatement} />
          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border text-left font-mono text-[10px] uppercase text-ink-2">
                  <th className="py-1 pr-2">FY</th>
                  <th className="py-1 pr-2 text-right">Revenue ({asFiledMode})</th>
                  <th className="py-1 pr-2 text-right">Net Income ({asFiledMode})</th>
                  <th className="py-1 pr-2">Source</th>
                  <th className="py-1">Delta</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {restatements.items.map((it) => {
                  const v = asFiledMode === "filed" ? it.as_filed : (it.as_restated ?? it.as_filed);
                  const delta = it.delta_pct;
                  return (
                    <tr key={it.fiscal_year} className={it.has_restatement ? "bg-warn-weak/20" : ""}>
                      <td className="py-1 font-mono">{it.fiscal_year}</td>
                      <td className="py-1 text-right font-mono">{v.revenue != null ? Number(v.revenue).toLocaleString() : "0.00"}</td>
                      <td className="py-1 text-right font-mono">{v.net_income != null ? Number(v.net_income).toLocaleString() : "0.00"}</td>
                      <td className="py-1 font-mono text-[10px]">{(it.provenance.filed_source ?? "").slice(0, 24)}</td>
                      <td className="py-1">
                        {it.has_restatement ? (
                          <span className="px-1.5 py-0.5 rounded bg-warn-weak text-warn border border-warn/30 text-[10px] font-mono">
                            {delta.revenue != null ? `${delta.revenue > 0 ? "+" : ""}${delta.revenue}% rev` : "restated"}
                          </span>
                        ) : (
                          <span className="text-ink-2 text-[11px]">-</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
                {restatements.items.length === 0 && (
                  <tr><td colSpan={5} className="py-3 text-center text-ink-2">No multi-year history - restatement check requires ≥1 FY rows.</td></tr>
                )}
              </tbody>
            </table>
          </div>
          <Disclaimer />
        </Card>
      )}
    </div>
  );
};

// Lightweight SVG helpers - pure primitives, no chart libs

const TrajectorySVG: React.FC<{ points: TrajectoryOut["points"]; currency: string | null | undefined }> = ({ points }) => {
  const W = 640, H = 180, padL = 40, padR = 12, padT = 14, padB = 28;
  const innerW = W - padL - padR, innerH = H - padT - padB;
  if (points.length < 2) return <p className="text-xs text-ink-2">Insufficient trajectory data.</p>;
  const revs = points.map((p) => p.revenue ?? 0).filter((v) => v != null);
  const maxRev = Math.max(...revs, 1);
  const minRev = Math.min(...revs, 0);
  const range = maxRev - minRev || 1;
  const x = (i: number) => padL + (i / (points.length - 1)) * innerW;
  const yRev = (v: number | null) => (v == null ? padT + innerH : padT + innerH - ((v - minRev) / range) * innerH);

  // Margins scaled -0.2..0.6 etc but we just normalize  -0.3..0.5
  const margins = points.flatMap((p) => [p.gross_margin, p.operating_margin].filter((v) => v != null) as number[]);
  const mMax = Math.max(...margins, 0.5);
  const mMin = Math.min(...margins, -0.1);
  const mRange = mMax - mMin || 1;
  const yMargin = (v: number | null) => (v == null ? padT + innerH : padT + innerH - ((v - mMin) / mRange) * innerH);

  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`10-year synchronized trajectory over ${points.length} fiscal years`} className="w-full h-auto">
      {/* grid */}
      {[0, 1, 2].map((i) => (
        <line key={i} x1={padL} x2={W - padR} y1={padT + (i / 2) * innerH} y2={padT + (i / 2) * innerH} stroke="var(--border)" strokeWidth={0.6} strokeDasharray="3 4" />
      ))}
      {/* Revenue polyline (accent) */}
      <polyline fill="none" stroke="var(--accent)" strokeWidth={1.7} points={points.map((p, i) => `${x(i).toFixed(1)},${yRev(p.revenue).toFixed(1)}`).join(" ")} />
      {points.map((p, i) => (
        <circle key={`r-${i}`} cx={x(i)} cy={yRev(p.revenue)} r={2.4} fill="var(--accent)" />
      ))}
      {/* Gross margin dashed info */}
      <polyline fill="none" stroke="var(--info)" strokeWidth={1.4} strokeDasharray="6 3" points={points.map((p, i) => `${x(i).toFixed(1)},${yMargin(p.gross_margin).toFixed(1)}`).join(" ")} />
      {/* Operating margin pos */}
      <polyline fill="none" stroke="var(--pos)" strokeWidth={1.4} points={points.map((p, i) => `${x(i).toFixed(1)},${yMargin(p.operating_margin).toFixed(1)}`).join(" ")} />
      {/* Inflection markers */}
      {points.map((p, i) =>
        p.inflections.length > 0 ? <circle key={`inf-${i}`} cx={x(i)} cy={yRev(p.revenue)} r={4.5} fill="none" stroke="var(--warn)" strokeWidth={1.5} /> : null
      )}
      {/* x labels */}
      {points.map((p, i) => (
        <text key={`xl-${i}`} x={x(i)} y={H - 6} textAnchor="middle" fontSize={8} fill="var(--ink-2)" fontFamily="IBM Plex Mono">
          {p.fiscal_year}
        </text>
      ))}
    </svg>
  );
};

const CCCSVG: React.FC<{ series: WorkingCapitalOut["series"] }> = ({ series }) => {
  const W = 520, H = 140, padL = 36, padR = 10, padT = 10, padB = 24;
  const innerW = W - padL - padR, innerH = H - padT - padB;
  const vals = series.flatMap((s) => [s.dso, s.dio, s.dpo, s.ccc].filter((v) => v != null) as number[]);
  const maxV = Math.max(...vals, 10);
  const minV = Math.min(...vals, 0);
  const range = maxV - minV || 1;
  const x = (i: number) => padL + (i / Math.max(1, series.length - 1)) * innerW;
  const y = (v: number | null) => (v == null ? padT + innerH : padT + innerH - ((v - minV) / range) * innerH);
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Cash conversion cycle over ${series.length} fiscal years`} className="w-full h-auto">
      {/* CCC bold line */}
      <polyline fill="none" stroke="var(--accent)" strokeWidth={2} points={series.map((s, i) => `${x(i).toFixed(1)},${y(s.ccc).toFixed(1)}`).join(" ")} />
      {/* DSO */}
      <polyline fill="none" stroke="var(--info)" strokeWidth={1.2} points={series.map((s, i) => `${x(i).toFixed(1)},${y(s.dso).toFixed(1)}`).join(" ")} />
      {/* DIO */}
      <polyline fill="none" stroke="var(--warn)" strokeWidth={1.2} strokeDasharray="4 3" points={series.map((s, i) => `${x(i).toFixed(1)},${y(s.dio).toFixed(1)}`).join(" ")} />
      {series.map((s, i) => (
        <text key={i} x={x(i)} y={H - 6} textAnchor="middle" fontSize={8} fill="var(--ink-2)" fontFamily="IBM Plex Mono">
          {s.fiscal_year}
        </text>
      ))}
      <g fontSize={8} fontFamily="IBM Plex Mono" fill="var(--ink-2)">
        <text x={padL} y={padT + 8}>CCC</text>
        <text x={padL} y={padT + 18} fill="var(--info)">DSO</text>
      </g>
    </svg>
  );
};

const GoodwillSVG: React.FC<{ strip: GoodwillRiskOut["strip"] }> = ({ strip }) => {
  const W = 520, H = 90, padL = 36, padR = 10, padT = 10, padB = 22;
  const innerW = W - padL - padR, innerH = H - padT - padB;
  const vals = strip.map((s) => s.proxy_intangible_ratio ?? 0);
  const maxV = Math.max(...vals, 0.45);
  const y = (v: number | null) => (v == null ? padT + innerH : padT + innerH - (v / maxV) * innerH);
  const x = (i: number) => padL + (i / Math.max(1, strip.length - 1)) * innerW;
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Goodwill proxy strip over ${strip.length} fiscal years`} className="w-full h-auto">
      {/* 40% threshold line */}
      <line x1={padL} x2={W - padR} y1={y(0.40)} y2={y(0.40)} stroke="var(--neg)" strokeWidth={1} strokeDasharray="5 4" />
      <text x={W - padR - 2} y={y(0.40) - 4} textAnchor="end" fontSize={8} fill="var(--neg)" fontFamily="IBM Plex Mono">
        40% bloat
      </text>
      {/* bars */}
      {strip.map((s, i) => {
        const v = s.proxy_intangible_ratio ?? 0;
        const barH = (v / maxV) * innerH;
        return (
          <g key={i}>
            <rect x={x(i) - 14} y={padT + innerH - barH} width={28} height={barH} rx={2} fill={v >= 0.40 ? "var(--neg)" : "var(--info)"} opacity={0.85} />
            <text x={x(i)} y={H - 6} textAnchor="middle" fontSize={8} fill="var(--ink-2)" fontFamily="IBM Plex Mono">
              {s.fiscal_year}
            </text>
          </g>
        );
      })}
    </svg>
  );
};

export default RedFlagsWorkspace;