import React, { useState } from "react";
import { api } from "../../api/client";

interface DecisionJournalModalProps {
  isOpen: boolean;
  onClose: () => void;
  companyId?: string;
  onCreated: () => void;
}

export const DecisionJournalModal: React.FC<DecisionJournalModalProps> = ({ isOpen, onClose, companyId: initialId, onCreated }) => {
  const [companyId, setCompanyId] = useState(initialId ?? "US:AAPL:US");
  const [confidence, setConfidence] = useState("3");
  const [strategy, setStrategy] = useState("quality");
  const [thesis, setThesis] = useState("");
  const [kill, setKill] = useState("");
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const submit = async () => {
    setError(null);
    try {
      await api.createJournalEntry({
        company_id: companyId,
        confidence: parseInt(confidence, 10),
        strategy_tag: strategy,
        thesis: thesis.slice(0, 2000),
        kill_conditions: kill.slice(0, 1000),
        purchase_date: new Date().toISOString().slice(0, 10),
      });
      onCreated();
      onClose();
    } catch (e: any) {
      setError(e?.message ?? "Failed to save journal");
    }
  };

  return (
    <div role="dialog" aria-modal="true" aria-labelledby="journal-modal-title" className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink-0/60 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-card border border-border bg-bg-1 shadow-2xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h2 id="journal-modal-title" className="font-heading font-semibold text-ink-0">Buy Decision Journal</h2>
          <button onClick={onClose} aria-label="Close journal modal" className="p-1 text-ink-2 hover:text-ink-0">✕</button>
        </div>

        <div className="space-y-3">
          <label className="block">
            <span className="font-mono text-[11px] uppercase text-ink-2">Company ID</span>
            <input value={companyId} onChange={(e) => setCompanyId(e.target.value)} className="mt-1 w-full rounded border border-border bg-bg-0 px-2 py-1.5 text-xs font-mono" aria-label="Company ID" />
          </label>

          <div className="grid grid-cols-2 gap-3">
            <label className="block">
              <span className="font-mono text-[11px] uppercase text-ink-2">Confidence (1-5)</span>
              <input type="range" min={1} max={5} step={1} value={confidence} onChange={(e) => setConfidence(e.target.value)} className="mt-1 w-full accent-[var(--accent)]" aria-label="Confidence" />
              <span className="font-mono text-xs text-accent">{confidence} / 5</span>
            </label>
            <label className="block">
              <span className="font-mono text-[11px] uppercase text-ink-2">Strategy Tag</span>
              <select value={strategy} onChange={(e) => setStrategy(e.target.value)} className="mt-1 w-full rounded border border-border bg-bg-0 px-2 py-1.5 text-xs" aria-label="Strategy tag">
                <option value="quality">quality</option>
                <option value="turnaround">turnaround</option>
                <option value="income">income</option>
                <option value="value">value</option>
                <option value="growth">growth</option>
              </select>
            </label>
          </div>

          <label className="block">
            <span className="font-mono text-[11px] uppercase text-ink-2">Purchase Thesis (why you bought)</span>
            <textarea value={thesis} onChange={(e) => setThesis(e.target.value.slice(0, 2000))} rows={3} className="mt-1 w-full rounded border border-border bg-bg-0 px-2 py-1.5 text-xs" aria-label="Thesis" placeholder="Moat, valuation, catalyst…" />
          </label>

          <label className="block">
            <span className="font-mono text-[11px] uppercase text-ink-2">Kill Conditions (pre-commitment thresholds that require selling)</span>
            <textarea value={kill} onChange={(e) => setKill(e.target.value.slice(0, 1000))} rows={2} className="mt-1 w-full rounded border border-border bg-bg-0 px-2 py-1.5 text-xs" aria-label="Kill conditions" placeholder="e.g., Altman Z falls to Distress, dividend cut, DSO surge >15%…" />
          </label>

          <div className="rounded border border-warn/30 bg-warn-weak p-2 text-xs text-ink-1">
            <strong>Pre-mortem:</strong> Assume this position failed in 2 years - what was the obvious reason? Document it above.
          </div>
        </div>

        {error && <p role="alert" className="text-xs text-neg">{error}</p>}

        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="px-3 py-1.5 rounded border border-border text-xs">Cancel</button>
          <button onClick={submit} className="px-3 py-1.5 rounded bg-accent text-bg-0 text-xs font-mono font-semibold">Save Journal</button>
        </div>

        <p className="text-[11px] font-mono text-ink-2 border-t border-border pt-2">Personal research software, not investment advice. Portfolio tracking and alerts run locally.</p>
      </div>
    </div>
  );
};

export default DecisionJournalModal;