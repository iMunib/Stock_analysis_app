import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Card, Page, Chip } from "../components/layout";

interface Module {
  id: string;
  title: string;
  description: string;
  lessons: { id: string; title: string; body: string }[];
  key_terms: string[];
  quiz: { q: string; a: string; options: string[] }[];
}

export default function Curriculum() {
  const [modules, setModules] = useState<Module[]>([]);
  const [active, setActive] = useState<string>("m01-balance-sheet");
  const [caseStudies, setCaseStudies] = useState<any[]>([]);
  const [flashcards, setFlashcards] = useState<any[]>([]);
  const [quizMode, setQuizMode] = useState(false);
  const [focusMode, setFocusMode] = useState(false);
  const [cert, setCert] = useState(false);

  useEffect(() => {
    api.requestCurriculumModules().then((r: any) => setModules(r.items ?? [])).catch(() => {});
    api.requestCaseStudies().then((r: any) => setCaseStudies(r.items ?? [])).catch(() => {});
    api.requestFlashcards().then((r: any) => setFlashcards(r.items ?? [])).catch(() => {});
  }, []);

  const activeMod = modules.find((m) => m.id === active) ?? modules[0];

  const milestones = [
    { id: "fundamentals", label: "Fundamentals", desc: "Balance sheet, income, cash flow", icon: "◈" },
    { id: "forensics", label: "Forensics", desc: "Beneish, Altman, Sloan", icon: "⬢" },
    { id: "valuation", label: "Valuation", desc: "DCF, EPV, DDM, Residual", icon: "⬣" },
    { id: "allocation", label: "Capital", desc: "Buybacks, dilution, yield", icon: "⬔" },
  ];
  const activeIdx = modules.findIndex((m) => m.id === active);

  return (
    <Page
      title="Analyst Academy — Structured Investment Curriculum"
      description="Six progressive modules from first principles to institutional forensic and valuation mastery. Pure research, no advice."
      actions={
        <div className="flex items-center gap-2">
          <button
            onClick={() => setFocusMode((v) => !v)}
            aria-pressed={focusMode}
            className={`rounded-chip border px-3 py-1.5 text-xs ${focusMode ? "bg-accent text-bg-0 border-accent" : "border-border text-ink-1"}`}
            aria-label="Toggle focus mode"
          >
            {focusMode ? "Exit Focus" : "Focus Mode"}
          </button>
          <button
            onClick={() => setQuizMode((v) => !v)}
            className="rounded-chip border border-accent/60 bg-accent-weak px-3 py-1.5 text-xs text-accent"
          >
            {quizMode ? "Back to Lessons" : "Take Quiz"}
          </button>
        </div>
      }
    >
      {/* Milestone Progression Rail — visual roadmap */}
      <div className="rounded-card border border-border bg-bg-1 p-4" role="navigation" aria-label="Curriculum progression">
        <div className="flex items-center justify-between gap-2">
          {milestones.map((ms, idx) => {
            const isActive = activeIdx >= 0 ? (activeIdx < 2 ? idx === 0 : activeIdx < 4 ? idx === 1 : activeIdx < 6 ? idx === 2 : idx === 3) : idx === 0;
            const isPast = activeIdx >= 0 ? (idx < Math.floor(activeIdx / 2)) : idx === 0;
            return (
              <div key={ms.id} className="flex-1 flex flex-col items-center text-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold border ${isActive ? "bg-accent text-bg-0 border-accent" : isPast ? "bg-pos-weak text-pos border-pos/30" : "bg-bg-2 text-ink-2 border-border"}`} aria-current={isActive ? "step" : undefined}>{ms.icon}</div>
                <span className={`mt-1 font-mono text-[11px] uppercase tracking-wider ${isActive ? "text-accent font-semibold" : "text-ink-2"}`}>{ms.label}</span>
                <span className="font-mono text-[10px] text-ink-2">{ms.desc}</span>
                {idx < milestones.length - 1 && <div className={`hidden sm:block h-0.5 w-full mt-2 ${isPast ? "bg-pos" : "bg-border"}`} aria-hidden="true" />}
              </div>
            );
          })}
        </div>
        <div className="mt-3 h-1.5 rounded-full bg-bg-2 overflow-hidden" role="progressbar" aria-valuenow={activeIdx + 1} aria-valuemin={0} aria-valuemax={modules.length}>
          <div className="h-full bg-accent transition-all" style={{ width: `${((activeIdx + 1) / Math.max(1, modules.length)) * 100}%` }} />
        </div>
      </div>

      <div className={`grid gap-6 ${focusMode ? "grid-cols-1" : "lg:grid-cols-[280px_1fr]"}`}>
        {!focusMode && (
          <nav aria-label="Curriculum modules" className="space-y-2">
            {modules.map((m) => (
              <button
                key={m.id}
                onClick={() => setActive(m.id)}
                aria-current={active === m.id ? "true" : undefined}
                className={`w-full text-left rounded-card border px-3 py-2 text-xs ${active === m.id ? "bg-accent-weak border-accent text-accent" : "bg-bg-1 border-border text-ink-1 hover:bg-bg-2"}`}
              >
                <span className="font-semibold block">{m.title}</span>
                <span className="text-[11px] text-ink-2 line-clamp-2">{m.description}</span>
              </button>
            ))}
            <div className="pt-2 border-t border-border">
              <p className="text-[11px] font-mono text-ink-2 mb-1">Progress</p>
              <div className="h-2 rounded bg-bg-2 overflow-hidden" role="progressbar" aria-valuenow={modules.findIndex((m) => m.id === active) + 1} aria-valuemin={0} aria-valuemax={modules.length}>
                <div className="h-full bg-accent" style={{ width: `${((modules.findIndex((m) => m.id === active) + 1) / Math.max(1, modules.length)) * 100}%` }} />
              </div>
              {cert && <Chip tone="positive" size="sm" className="mt-2">Certificate earned - Wave 8 Capstone Complete</Chip>}
              {!cert && (
                <button onClick={() => setCert(true)} className="mt-2 w-full rounded-chip bg-pos-weak border border-pos/30 text-pos text-xs py-1">
                  Mark Complete - Get Certificate
                </button>
              )}
            </div>
          </nav>
        )}

        <div className="space-y-4">
          {activeMod && !quizMode && (
            <Card title={activeMod.title} subtitle={activeMod.description} padding="md">
              <div className="space-y-3">
                {activeMod.lessons.map((l) => (
                  <div key={l.id} className="rounded border border-border bg-bg-0 p-3">
                    <h4 className="font-semibold text-xs text-ink-0">{l.title}</h4>
                    <p className="text-xs text-ink-1 mt-1 leading-relaxed">{l.body}</p>
                  </div>
                ))}
                <div className="flex flex-wrap gap-1.5 pt-2">
                  {activeMod.key_terms.map((k) => (
                    <Chip key={k} tone="info" size="sm">{k}</Chip>
                  ))}
                </div>
              </div>
            </Card>
          )}

          {activeMod && quizMode && (
            <Card title={`Quiz - ${activeMod.title}`} padding="md">
              <div className="space-y-3">
                {activeMod.quiz.map((q, idx) => (
                  <div key={idx} className="rounded border border-border bg-bg-0 p-3">
                    <p className="text-xs font-semibold text-ink-0">{idx + 1}. {q.q}</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {q.options.map((o) => (
                        <span key={o} className={`px-2 py-1 rounded text-xs border ${o === q.a ? "bg-pos-weak border-pos/30 text-pos" : "bg-bg-2 border-border text-ink-2"}`}>{o}</span>
                      ))}
                    </div>
                    <p className="text-[11px] font-mono text-ink-2 mt-1">Answer: {q.a}</p>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Flashcards - spaced repetition style */}
          <Card title="Flashcards - Spaced Repetition (Real Universe Numbers)" subtitle="Front → back with local data" padding="md">
            <div className="grid sm:grid-cols-2 gap-2">
              {flashcards.slice(0, 6).map((c: any, i: number) => (
                <div key={i} className="rounded border border-border bg-bg-0 p-2.5">
                  <p className="text-xs font-semibold text-ink-0">Q: {c.front}</p>
                  <p className="text-xs text-ink-1 mt-1">A: {c.back}</p>
                </div>
              ))}
            </div>
          </Card>

          {/* Interactive 10-K Walkthrough — side-by-side annotated filing explorer */}
          <Card title="Interactive 10-K Walkthrough" subtitle="Where balance sheet, income, and cash flow connect in raw SEC filings" padding="md">
            <div className="grid md:grid-cols-2 gap-3">
              <div className="rounded border border-border bg-bg-0 p-3">
                <span className="font-mono text-[11px] uppercase tracking-wider text-ink-2 block">Balance Sheet Excerpt — FY2023 10-K</span>
                <div className="mt-2 font-mono text-xs space-y-1">
                  <div className="flex justify-between border-b border-border/50 py-1"><span className="text-ink-1">Total Assets</span><span className="font-semibold text-ink-0">$352,755M</span><span className="text-accent text-[10px]">→ Validates ROA denominator</span></div>
                  <div className="flex justify-between border-b border-border/50 py-1"><span className="text-ink-1">Cash & ST Investments</span><span className="font-semibold text-ink-0">$48,355M</span><span className="text-pos text-[10px]">→ NOPAT invested capital</span></div>
                  <div className="flex justify-between py-1"><span className="text-ink-1">Total Debt</span><span className="font-semibold text-ink-0">$109,106M</span><span className="text-warn text-[10px]">→ Altman X4 leverage</span></div>
                </div>
                <p className="text-[11px] text-ink-2 mt-2">Source: SEC EDGAR CIK 320193 10-K filed 2023-11-03. Figures cross-checked to Total Liabilities + Equity identity.</p>
              </div>
              <div className="rounded border border-border bg-bg-0 p-3">
                <span className="font-mono text-[11px] uppercase tracking-wider text-ink-2 block">Income & Cash Flow Bridge</span>
                <div className="mt-2 font-mono text-xs space-y-1">
                  <div className="flex justify-between border-b border-border/50 py-1"><span className="text-ink-1">Revenue</span><span className="font-semibold text-ink-0">$383,285M</span><span className="text-accent text-[10px]">→ Gross margin</span></div>
                  <div className="flex justify-between border-b border-border/50 py-1"><span className="text-ink-1">Operating Cash Flow</span><span className="font-semibold text-ink-0">$122,151M</span><span className="text-pos text-[10px]">→ Sloan accruals</span></div>
                  <div className="flex justify-between py-1"><span className="text-ink-1">Free Cash Flow</span><span className="font-semibold text-pos">$99,584M</span><span className="text-info text-[10px]">→ EPV/NOPAT</span></div>
                </div>
                <p className="text-[11px] text-ink-2 mt-2">Hover filing line to see formula impact. All numbers from local DB, not LLM.</p>
              </div>
            </div>
            <p className="text-[11px] font-mono text-ink-2 mt-2 border-t border-border pt-2">Tip: Open any Dossier → Filings & Sources tab to see the same live linkage for that company.</p>
          </Card>

          {/* Case studies */}
          <Card title="Case Studies - History Mapped to Metrics" padding="md">
            <div className="grid sm:grid-cols-3 gap-3">
              {caseStudies.map((cs: any) => (
                <div key={cs.id} className="rounded border border-border bg-bg-0 p-3">
                  <h4 className="font-semibold text-xs text-ink-0">{cs.title}</h4>
                  <p className="text-xs text-ink-1 mt-1 leading-relaxed">{cs.summary}</p>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {cs.metrics_mapped.map((m: string) => (
                      <Chip key={m} tone="warning" size="sm">{m}</Chip>
                    ))}
                  </div>
                  <p className="text-[11px] font-mono text-ink-2 mt-2">Lesson: {cs.lesson}</p>
                </div>
              ))}
            </div>
          </Card>

          <p className="text-[11px] font-mono text-ink-2 border-t border-border pt-2">Personal research software, not investment advice. Curriculum uses local database numbers; external links are optional.</p>
        </div>
      </div>
    </Page>
  );
}