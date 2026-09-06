import { useState } from "react";
import { Card } from "../layout";
import { getAlertForCompany, saveAlert } from "../../lib/alerts";

export default function AlertSettingsCard({
  companyId,
  currentPe,
  currentComposite,
}: {
  companyId: string;
  currentPe?: number | null;
  currentComposite?: number | null;
}) {
  const [alert, setAlertState] = useState(() => getAlertForCompany(companyId));
  const [peAbove, setPeAbove] = useState(alert?.pe_above?.toString() ?? "");
  const [compBelow, setCompBelow] = useState(alert?.composite_below?.toString() ?? "");
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    const updated = saveAlert({
      id: companyId,
      pe_above: peAbove ? parseFloat(peAbove) : null,
      composite_below: compBelow ? parseFloat(compBelow) : null,
    });
    setAlertState(updated.find((a) => a.id === companyId) ?? null);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <Card
      title="Local Alert Rule"
      subtitle="Evaluated locally on page load. No push notifications."
    >
      <form onSubmit={handleSave} className="space-y-3">
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div>
            <label className="block font-mono text-[10px] uppercase text-ink-2 mb-1">Alert if PE &gt;</label>
            <input
              type="number"
              step="1"
              placeholder={currentPe ? `Current: ${currentPe.toFixed(1)}` : "e.g. 25"}
              value={peAbove}
              onChange={(e) => setPeAbove(e.target.value)}
              className="w-full rounded-card border border-border bg-bg-0 px-2.5 py-1 font-mono text-xs text-ink-0"
            />
          </div>
          <div>
            <label className="block font-mono text-[10px] uppercase text-ink-2 mb-1">Alert if Composite &lt;</label>
            <input
              type="number"
              step="0.5"
              placeholder={currentComposite ? `Current: ${currentComposite.toFixed(1)}` : "e.g. 5.0"}
              value={compBelow}
              onChange={(e) => setCompBelow(e.target.value)}
              className="w-full rounded-card border border-border bg-bg-0 px-2.5 py-1 font-mono text-xs text-ink-0"
            />
          </div>
        </div>
        <div className="flex items-center justify-between pt-1">
          <button
            type="submit"
            className="rounded-card border border-accent/60 bg-accent-weak px-3 py-1 font-mono text-xs text-accent hover:bg-accent/20 transition-colors"
          >
            {saved ? "Saved!" : "Save Alert"}
          </button>
          {alert && (
            <span className="font-mono text-[10px] text-ink-2">
              Active: {alert.pe_above ? `PE > ${alert.pe_above}` : ""}{" "}
              {alert.composite_below ? `Comp < ${alert.composite_below}` : ""}
            </span>
          )}
        </div>
      </form>
    </Card>
  );
}
