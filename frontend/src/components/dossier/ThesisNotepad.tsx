import { useEffect, useState } from "react";
import { Card } from "../layout";
import { getThesis, saveThesis } from "../../lib/thesis";

export default function ThesisNotepad({ companyId }: { companyId: string }) {
  const [thesis, setThesis] = useState(() => getThesis(companyId));
  const [draft, setDraft] = useState(thesis.text);
  const [preMortemDraft, setPreMortemDraft] = useState(thesis.preMortem || "");
  const [savedAt, setSavedAt] = useState<string | null>(thesis.savedAt);

  useEffect(() => {
    const t = getThesis(companyId);
    setThesis(t);
    setDraft(t.text);
    setPreMortemDraft(t.preMortem || "");
    setSavedAt(t.savedAt);
  }, [companyId]);

  const handleThesisChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value.slice(0, 1000);
    setDraft(val);
    const updated = saveThesis(companyId, val, preMortemDraft);
    setSavedAt(updated.savedAt);
  };

  const handlePreMortemChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value.slice(0, 1000);
    setPreMortemDraft(val);
    const updated = saveThesis(companyId, draft, val);
    setSavedAt(updated.savedAt);
  };

  return (
    <div className="space-y-4">
      {/* 5-Line Thesis Card */}
      <Card
        title="5-Line Investment Thesis"
        subtitle="Your notes stay encrypted on this browser."
        action={
          <span className="font-mono text-[10px] text-ink-2">
            {savedAt ? `Saved ${new Date(savedAt).toLocaleTimeString()}` : "Not saved"} · {draft.length}/1000
          </span>
        }
      >
        <textarea
          value={draft}
          onChange={handleThesisChange}
          maxLength={1000}
          rows={5}
          placeholder="Write your 5-line thesis: 1) What they do, 2) Growth catalyst, 3) Valuation vs peers, 4) Major risk, 5) Target entry price..."
          className="w-full rounded-card border border-border bg-bg-0 p-3 font-mono text-xs text-ink-0 placeholder:text-ink-2 focus:border-accent focus:outline-none"
        />
      </Card>

      {/* Pre-Mortem Thesis Challenge Prompt (US-0725) */}
      <Card
        title="Pre-Mortem Thesis Challenge"
        subtitle="Counter confirmation bias before allocating capital."
        className="border-warn/40"
        action={
          <span className="rounded-chip bg-warn-weak border border-warn/40 px-2 py-0.5 font-mono text-[10px] font-bold text-warn">
            Anti-Fragility Check
          </span>
        }
      >
        <div className="rounded border border-warn/30 bg-warn-weak/20 p-3 mb-3" data-testid="pre-mortem-prompt">
          <div className="flex items-center gap-2 font-mono text-xs font-semibold text-warn mb-1">
            <span>⚠️ Probabilistic Stress Test (Pre-Mortem)</span>
          </div>
          <p className="text-xs text-ink-1 italic leading-relaxed">
            "Assume you bought this stock today and over the next 24 months it suffered a catastrophic 50% drawdown. Looking backward from 2026, what was the obvious reason this investment failed?"
          </p>
        </div>

        <textarea
          value={preMortemDraft}
          onChange={handlePreMortemChange}
          maxLength={1000}
          rows={4}
          placeholder="Document the exact failure mode here: e.g., Pricing power collapsed under competition, debt maturity roll-over failure, structural margin compression..."
          className="w-full rounded-card border border-border bg-bg-0 p-3 font-mono text-xs text-ink-0 placeholder:text-ink-2 focus:border-warn focus:outline-none"
        />
        <div className="mt-1.5 flex justify-between items-center text-[10px] font-mono text-ink-2">
          <span>Forces explicit consideration of failure modes before committing capital.</span>
          <span>{preMortemDraft.length}/1000</span>
        </div>
      </Card>
    </div>
  );
}
