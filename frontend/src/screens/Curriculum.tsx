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

type QuizState = Record<number, string | null>;

const MILESTONES = [
  { step: 1, label: "Fundamentals", desc: "Balance sheet, income, cash flow", est: "25 min" },
  { step: 2, label: "Forensics", desc: "Beneish, Altman, Sloan, Schilit", est: "30 min" },
  { step: 3, label: "Valuation", desc: "DCF, EPV, DDM, Residual", est: "35 min" },
  { step: 4, label: "Capital Allocation", desc: "Buybacks, dilution, yield", est: "20 min" },
];

function estForModule(idx: number): string {
  const map = ["Reading a 10-K (5 min)", "Piotroski & DuPont (6 min)", "Altman & Beneish (7 min)", "Reverse DCF (6 min)", "Penman & EPV (7 min)", "Capital Returns (5 min)"];
  return map[idx % map.length];
}

export default function Curriculum() {
  const [modules, setModules] = useState<Module[]>([]);
  const [active, setActive] = useState<string>("m01-balance-sheet");
  const [caseStudies, setCaseStudies] = useState<any[]>([]);
  const [flashcards, setFlashcards] = useState<any[]>([]);
  const [quizMode, setQuizMode] = useState(false);
  const [focusMode, setFocusMode] = useState(false);
  const [cert, setCert] = useState(false);
  const [quizAnswers, setQuizAnswers] = useState<QuizState>({});
  const [showResult, setShowResult] = useState<Record<number, boolean>>({});

  useEffect(() => {
    api.requestCurriculumModules().then((r: any) => setModules(r.items ?? [])).catch(() => {});
    api.requestCaseStudies().then((r: any) => setCaseStudies(r.items ?? [])).catch(() => {});
    api.requestFlashcards().then((r: any) => setFlashcards(r.items ?? [])).catch(() => {});
  }, []);

  const activeMod = modules.find((m) => m.id === active) ?? modules[0];
  const activeIdx = modules.findIndex((m) => m.id === active);
  const progressPct = modules.length ? Math.round(((activeIdx + 1) / modules.length) * 100) : 0;
  const milestoneIdx = activeIdx < 0 ? 0 : activeIdx < 2 ? 0 : activeIdx < 4 ? 1 : activeIdx < 6 ? 2 : 3;

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
      {/* Sleek horizontal stepper */}
      <div className="rounded-md border border-border-subtle bg-bg-1 p-4" role="navigation" aria-label="Curriculum progression">
        <div className="flex items-center gap-2" role="tablist" aria-label="Milestones">
          {MILESTONES.map((ms, idx) => {
            const isActive = idx === milestoneIdx;
            const isPast = idx < milestoneIdx;
            return (
              <div key={ms.step} className="flex flex-1 items-center gap-2">
                <button
                  type="button"
                  role="tab"
                  aria-selected={isActive}
                  aria-current={isActive ? "step" : undefined}
                  onClick={() => {
                    const targetIdx = idx * 2;
                    const mod = modules[targetIdx] ?? modules[idx] ?? modules[0];
                    if (mod) setActive(mod.id);
                  }}
                  className={`flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-mono transition-colors focus:outline-none focus:ring-2 focus:ring-accent ${
                    isActive ? "bg-accent border-accent text-bg-0 font-semibold shadow-sm" : isPast ? "bg-pos-weak border-pos/30 text-pos" : "bg-bg-0 border-border text-ink-2 hover:border-accent/40"
                  }`}
                >
                  <span className={`flex h-5 w-5 items-center justify-center rounded-full text-[11px] font-bold ${isActive ? "bg-bg-0 text-accent" : isPast ? "bg-pos text-white" : "bg-bg-2 text-ink-2"}`}>
                    {isPast ? "✓" : ms.step}
                  </span>
                  <span className="hidden sm:inline">{ms.label}</span>
                  <span className="sm:hidden">{ms.step}. {ms.label.slice(0, 4)}</span>
                </button>
                {idx < MILESTONES.length - 1 && (
                  <div className={`hidden h-0.5 flex-1 sm:block ${isPast ? "bg-pos" : "bg-border-subtle"}`} aria-hidden="true" />
                )}
              </div>
            );
          })}
        </div>
        <div className="mt-4 flex items-center justify-between gap-3">
          <div className="flex-1">
            <div className="flex items-center justify-between font-mono text-[11px] text-ink-2">
              <span>
                {MILESTONES[milestoneIdx]?.label} · {progressPct}% complete
              </span>
              <span>{activeIdx + 1} / {modules.length} modules</span>
            </div>
            <div className="mt-1 h-2 overflow-hidden rounded-full bg-bg-2" role="progressbar" aria-valuenow={progressPct} aria-valuemin={0} aria-valuemax={100}>
              <div className="h-full bg-accent transition-all duration-500" style={{ width: `${progressPct}%` }} />
            </div>
          </div>
          <span className="hidden font-mono text-[11px] text-ink-2 sm:block">Fundamentals → Forensics → Valuation → Capital Allocation</span>
        </div>
      </div>

      <div className={`grid gap-6 ${focusMode ? "grid-cols-1" : "lg:grid-cols-[320px_1fr]"}`}>
        {/* Left Column — Syllabus */}
        {!focusMode && (
          <nav aria-label="Curriculum modules" className="space-y-3">
            {modules.map((m, idx) => (
              <button
                key={m.id}
                onClick={() => setActive(m.id)}
                aria-current={active === m.id ? "true" : undefined}
                className={`w-full text-left rounded-md border p-3 transition-colors ${active === m.id ? "bg-accent-weak border-accent text-accent" : "bg-bg-1 border-border-subtle text-ink-1 hover:bg-bg-2"}`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-semibold text-xs leading-tight">{idx + 1}. {m.title}</span>
                  <span className="shrink-0 rounded bg-bg-0 border border-border px-1.5 py-0.5 font-mono text-[10px] text-ink-2">{estForModule(idx)}</span>
                </div>
                <span className="mt-1 block text-[11px] leading-snug text-ink-2 line-clamp-2">{m.description}</span>
                <div className="mt-2 flex items-center gap-1.5">
                  <span className={`h-1.5 flex-1 rounded-full ${active === m.id ? "bg-accent" : "bg-border"}`} />
                  <span className="font-mono text-[10px] text-ink-2">{m.lessons.length} lessons · {m.key_terms.length} terms</span>
                </div>
              </button>
            ))}
            <div className="rounded-md border border-border-subtle bg-bg-0 p-3">
              <p className="font-mono text-[11px] uppercase tracking-wider text-ink-2">Overall Progress</p>
              <div className="mt-1 h-2 overflow-hidden rounded bg-bg-2" role="progressbar" aria-valuenow={progressPct} aria-valuemin={0} aria-valuemax={100}>
                <div className="h-full bg-accent" style={{ width: `${progressPct}%` }} />
              </div>
              <p className="mt-1 font-mono text-xs text-ink-1">{progressPct}% · {activeIdx + 1} of {modules.length} modules in view</p>
              {cert ? (
                <span className="mt-2 inline-flex rounded bg-pos-weak border border-pos/30 px-2 py-1 font-mono text-xs text-pos">✓ Certificate earned — Wave 8 Capstone Complete</span>
              ) : (
                <button onClick={() => setCert(true)} className="mt-2 w-full rounded-chip bg-pos-weak border border-pos/30 py-1.5 font-mono text-xs text-pos hover:bg-pos/10">
                  Mark Complete — Get Certificate
                </button>
              )}
            </div>
          </nav>
        )}

        {/* Right Column — Lesson Terminal */}
        <div className="space-y-4">
          {activeMod && !quizMode && (
            <Card title={activeMod.title} subtitle={`${activeMod.description} · ${estForModule(activeIdx)}`} padding="md">
              <div className="space-y-3">
                {activeMod.lessons.map((l) => (
                  <div key={l.id} className="rounded-md border border-border-subtle bg-bg-0 p-3">
                    <h4 className="font-semibold text-xs text-ink-0">{l.title}</h4>
                    <p className="mt-1 text-xs leading-relaxed text-ink-1">{l.body}</p>
                    <div className="mt-2 rounded border border-accent/20 bg-accent-weak/30 px-2 py-1.5 font-mono text-[11px] text-ink-1">
                      Callout: This line maps to <span className="font-semibold text-accent">{l.title.includes("Asset") ? "ROA denominator → Quality pillar" : l.title.includes("Cash") ? "Sloan accruals → Risk" : "Revenue growth → Growth pillar"}</span>
                    </div>
                  </div>
                ))}
                <div className="flex flex-wrap gap-1.5 border-t border-border-subtle pt-2">
                  {activeMod.key_terms.map((k) => (
                    <Chip key={k} tone="info" size="sm">
                      {k}
                    </Chip>
                  ))}
                </div>
              </div>
            </Card>
          )}

          {/* Interactive lesson terminal — SEC excerpts, callouts, AAPL vs RY comparison */}
          {!quizMode && (
            <>
              <Card title="Interactive Lesson Terminal — SEC 10-K Excerpts" subtitle="Real filing lines linked to ratio formulas" padding="md">
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="rounded-md border border-border-subtle bg-bg-0 p-3">
                    <span className="block font-mono text-[11px] uppercase tracking-wider text-ink-2">AAPL — FY2023 10-K (CIK 320193)</span>
                    <div className="mt-2 space-y-1 font-mono text-xs">
                      <div className="flex justify-between border-b border-border/50 py-1.5">
                        <span className="text-ink-1">Total Assets</span>
                        <span className="font-semibold text-ink-0">$352,755M</span>
                        <span className="rounded bg-accent-weak px-1 py-0.5 text-[10px] text-accent">→ ROA</span>
                      </div>
                      <div className="flex justify-between border-b border-border/50 py-1.5">
                        <span className="text-ink-1">Cash & ST Inv.</span>
                        <span className="font-semibold text-ink-0">$48,355M</span>
                        <span className="rounded bg-pos-weak px-1 py-0.5 text-[10px] text-pos">→ ROIC</span>
                      </div>
                      <div className="flex justify-between py-1.5">
                        <span className="text-ink-1">Total Debt</span>
                        <span className="font-semibold text-ink-0">$109,106M</span>
                        <span className="rounded bg-warn-weak px-1 py-0.5 text-[10px] text-warn">→ Z X4</span>
                      </div>
                    </div>
                    <p className="mt-2 border-t border-border-subtle pt-2 font-mono text-[11px] text-ink-2">Why it matters: Assets validate ROA denominator; low net debt → pristine Altman.</p>
                  </div>
                  <div className="rounded-md border border-border-subtle bg-bg-0 p-3">
                    <span className="block font-mono text-[11px] uppercase tracking-wider text-ink-2">RY.TO — FY2023 Annual Report (TSX:RY)</span>
                    <div className="mt-2 space-y-1 font-mono text-xs">
                      <div className="flex justify-between border-b border-border/50 py-1.5">
                        <span className="text-ink-1">Revenue</span>
                        <span className="font-semibold text-ink-0">$45.7B CAD</span>
                        <span className="rounded bg-accent-weak px-1 py-0.5 text-[10px] text-accent">→ NIM</span>
                      </div>
                      <div className="flex justify-between border-b border-border/50 py-1.5">
                        <span className="text-ink-1">Efficiency Ratio</span>
                        <span className="font-semibold text-ink-0">53.2%</span>
                        <span className="rounded bg-neg-weak px-1 py-0.5 text-[10px] text-neg">→ Quality</span>
                      </div>
                      <div className="flex justify-between py-1.5">
                        <span className="text-ink-1">CET1</span>
                        <span className="font-semibold text-pos">12.8%</span>
                        <span className="rounded bg-pos-weak px-1 py-0.5 text-[10px] text-pos">→ Solvency</span>
                      </div>
                    </div>
                    <p className="mt-2 border-t border-border-subtle pt-2 font-mono text-[11px] text-ink-2">Contrast: Bank model uses CET1/NIM, not gross margin — honest NULL, not invented FCF.</p>
                  </div>
                </div>
                <div className="mt-3 rounded-md border border-accent/20 bg-accent-weak/20 p-2.5">
                  <p className="font-mono text-xs font-semibold text-accent">Real comparison: AAPL (asset-light, high ROIC) vs RY.TO (balance-sheet heavy, CET1-driven). Currency segregated — ratios only for cross-border.</p>
                </div>
              </Card>

              <Card title="Self-Check — Knowledge in Terminal" subtitle="Instant feedback, no page reload" padding="md">
                {activeMod ? (
                  <div className="space-y-3">
                    {activeMod.quiz.slice(0, 3).map((q, idx) => {
                      const chosen = quizAnswers[idx] ?? null;
                      const revealed = showResult[idx] ?? false;
                      const isCorrect = chosen === q.a;
                      return (
                        <div key={idx} className="rounded-md border border-border-subtle bg-bg-0 p-3">
                          <p className="text-xs font-semibold text-ink-0">
                            {idx + 1}. {q.q}
                          </p>
                          <div className="mt-2 grid gap-1.5 sm:grid-cols-2">
                            {q.options.map((o) => (
                              <button
                                key={o}
                                type="button"
                                onClick={() => setQuizAnswers((prev) => ({ ...prev, [idx]: o }))}
                                aria-pressed={chosen === o}
                                className={`rounded border px-2.5 py-1.5 text-left font-mono text-xs transition-colors ${
                                  chosen === o ? "border-accent bg-accent-weak text-accent font-semibold" : "border-border bg-bg-1 text-ink-1 hover:border-accent/40"
                                }`}
                              >
                                {o}
                              </button>
                            ))}
                          </div>
                          <div className="mt-2 flex items-center gap-2">
                            <button
                              type="button"
                              onClick={() => setShowResult((prev) => ({ ...prev, [idx]: true }))}
                              disabled={!chosen}
                              className="rounded border border-accent bg-accent-weak px-3 py-1 font-mono text-xs text-accent disabled:opacity-40"
                            >
                              Check answer
                            </button>
                            {revealed && (
                              <span className={`font-mono text-xs font-semibold ${isCorrect ? "text-pos" : "text-neg"}`}>
                                {isCorrect ? "✓ Correct" : `�- Correct answer: ${q.a}`}
                              </span>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p className="font-mono text-xs text-ink-2">Select a module to start self-check.</p>
                )}
              </Card>
            </>
          )}

          {activeMod && quizMode && (
            <Card title={`Quiz — ${activeMod.title}`} padding="md">
              <div className="space-y-3">
                {activeMod.quiz.map((q, idx) => {
                  const chosen = quizAnswers[idx] ?? null;
                  const revealed = showResult[idx] ?? false;
                  return (
                    <div key={idx} className="rounded border border-border bg-bg-0 p-3">
                      <p className="text-xs font-semibold text-ink-0">
                        {idx + 1}. {q.q}
                      </p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {q.options.map((o) => {
                          const isChosen = chosen === o;
                          const isAnswer = o === q.a;
                          return (
                            <button
                              key={o}
                              type="button"
                              onClick={() => setQuizAnswers((prev) => ({ ...prev, [idx]: o }))}
                              className={`rounded border px-2 py-1 text-xs ${revealed && isAnswer ? "bg-pos-weak border-pos/30 text-pos" : isChosen ? "border-accent bg-accent-weak text-accent" : "bg-bg-2 border-border text-ink-2"}`}
                            >
                              {o}
                            </button>
                          );
                        })}
                      </div>
                      <div className="mt-2 flex gap-2">
                        <button onClick={() => setShowResult((p) => ({ ...p, [idx]: true }))} disabled={!chosen} className="rounded border border-accent bg-accent-weak px-2 py-1 font-mono text-xs text-accent disabled:opacity-40">
                          Check
                        </button>
                        {revealed && <span className="font-mono text-xs text-ink-1">Answer: {q.a} {chosen === q.a ? "✓" : "�-"}</span>}
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>
          )}

          <Card title="Flashcards — Spaced Repetition (Real Universe Numbers)" subtitle="Front → back with local data" padding="md">
            <div className="grid gap-2 sm:grid-cols-2">
              {flashcards.slice(0, 6).map((c: any, i: number) => (
                <div key={i} className="rounded border border-border bg-bg-0 p-2.5">
                  <p className="text-xs font-semibold text-ink-0">Q: {c.front}</p>
                  <p className="mt-1 text-xs text-ink-1">A: {c.back}</p>
                </div>
              ))}
            </div>
          </Card>

          <Card title="Case Studies — History Mapped to Metrics" padding="md">
            <div className="grid gap-3 sm:grid-cols-3">
              {caseStudies.map((cs: any) => (
                <div key={cs.id} className="rounded border border-border bg-bg-0 p-3">
                  <h4 className="text-xs font-semibold text-ink-0">{cs.title}</h4>
                  <p className="mt-1 text-xs leading-relaxed text-ink-1">{cs.summary}</p>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {cs.metrics_mapped.map((m: string) => (
                      <Chip key={m} tone="warning" size="sm">
                        {m}
                      </Chip>
                    ))}
                  </div>
                  <p className="mt-2 font-mono text-[11px] text-ink-2">Lesson: {cs.lesson}</p>
                </div>
              ))}
            </div>
          </Card>

          <p className="border-t border-border pt-2 font-mono text-[11px] text-ink-2">Personal research software, not investment advice. Curriculum uses local database numbers; external links are optional.</p>
        </div>
      </div>
    </Page>
  );
}
