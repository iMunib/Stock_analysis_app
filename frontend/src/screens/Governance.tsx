import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Card, Page } from "../components/layout";

export default function Governance() {
  const [risk, setRisk] = useState<any>(null);
  const [canon, setCanon] = useState<any>(null);
  const [diff, setDiff] = useState<any>(null);

  useEffect(() => {
    api.requestModelRisk().then(setRisk).catch(()=>{});
    api.requestCanonMap().then(setCanon).catch(()=>{});
    api.requestDiffMatrix().then(setDiff).catch(()=>{});
  }, []);

  return (
    <Page
      title="Governance - Model Risk Register & Canon"
      description="Assumptions, false positives, blind spots, canon cross-reference, and competitive diff matrix. Personal research software, not investment advice."
    >
      <Card title="Model Risk Register" subtitle={`${risk?.count ?? 0} models with assumptions and mitigations`} padding="md">
        <div className="space-y-3">
          {(risk?.items ?? []).map((r: any, i: number) => (
            <div key={i} className="rounded border border-border bg-bg-0 p-3">
              <h4 className="font-semibold text-xs text-ink-0">{r.model}</h4>
              <div className="grid sm:grid-cols-3 gap-2 mt-2 text-[11px] leading-relaxed">
                <div><span className="font-mono text-ink-2 uppercase text-[10px] block">Assumption</span><span className="text-ink-1">{r.assumption}</span></div>
                <div><span className="font-mono text-ink-2 uppercase text-[10px] block">False Positive</span><span className="text-warn">{r.false_positive}</span></div>
                <div><span className="font-mono text-ink-2 uppercase text-[10px] block">Blind Spot</span><span className="text-ink-1">{r.blind_spot}</span></div>
              </div>
              <p className="text-[11px] font-mono text-pos mt-2">Mitigation: {r.mitigation}</p>
            </div>
          ))}
        </div>
      </Card>

      <Card title="Canon Literature Cross-Reference" subtitle="Graham → Fisher → Lynch → Greenwald - where each lives in the app" padding="md">
        <div className="overflow-x-auto">
          <table className="w-full text-xs" role="table" aria-label="Canon cross reference">
            <thead>
              <tr className="border-b border-border font-mono text-[10px] uppercase text-ink-2 text-left">
                <th className="py-1.5 px-2">Book</th>
                <th className="py-1.5 px-2">App Feature</th>
                <th className="py-1.5 px-2">Check</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {(canon?.items ?? []).map((c: any, i: number) => (
                <tr key={i} className="hover:bg-bg-2/40">
                  <td className="py-1.5 px-2 font-semibold text-ink-0">{c.book}</td>
                  <td className="py-1.5 px-2 text-ink-1">{c.app_feature}</td>
                  <td className="py-1.5 px-2 font-mono text-accent">{c.check}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card title="Competitive Diff Matrix" subtitle="Verified differentiators vs Seeking Alpha, Simply Wall St, TIKR, GuruFocus" padding="md">
        {diff && (
          <div className="overflow-x-auto">
            <table className="w-full text-xs" role="table" aria-label="Competitive diff matrix">
              <thead>
                <tr className="border-b border-border font-mono text-[10px] uppercase text-ink-2 text-left">
                  {diff.columns.map((col: string) => <th key={col} className="py-1.5 px-2">{col}</th>)}
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {diff.rows.map((row: string[], i: number) => (
                  <tr key={i} className={i===0?"bg-accent-weak/40":"hover:bg-bg-2/40"}>
                    {row.map((cell: string, j: number) => (
                      <td key={j} className={`py-1.5 px-2 ${j===1?"font-semibold text-pos":"text-ink-1"}`}>{cell}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <p className="text-[11px] font-mono text-ink-2 mt-2">Sources: KEY_NOTES §4 market map 2025–26; verified feature checks per STORY_TRIAGE. No influencer ranks, no auto-trading (deliberately not built).</p>
      </Card>

      <p className="text-[11px] font-mono text-ink-2 border-t border-border pt-2">Personal research software, not investment advice. Governance is local and versioned; methodology lives in SCORING_SPEC.md.</p>
    </Page>
  );
}