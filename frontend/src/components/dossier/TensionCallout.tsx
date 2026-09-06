import type { PillarTension } from "../../api/types";

export interface TensionCalloutProps {
  tensions?: PillarTension[] | null;
  className?: string;
}

export function TensionCallout({ tensions, className = "" }: TensionCalloutProps) {
  if (!tensions || tensions.length === 0) return null;

  return (
    <div
      aria-label="Pillar disagreement radar"
      className={`space-y-2.5 rounded-card border border-warn/40 bg-warn-weak/20 p-3.5 ${className}`}
    >
      <div className="flex items-center justify-between border-b border-warn/30 pb-1.5">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-warn inline-block animate-pulse-subtle" />
          <span className="font-heading text-xs font-bold uppercase tracking-wider text-warn">
            Pillar Disagreement Radar (Core Tension Detected)
          </span>
        </div>
        <span className="font-mono text-[10px] text-ink-2">US-0064</span>
      </div>

      <div className="space-y-2">
        {tensions.map((t) => {
          const toneBorder =
            t.tone === "neg"
              ? "border-neg/40 bg-neg-weak/30 text-neg"
              : t.tone === "warn"
              ? "border-warn/40 bg-warn-weak/30 text-warn"
              : "border-info/40 bg-info-weak/30 text-info";

          return (
            <div
              key={t.tension_id}
              className={`rounded border p-2.5 ${toneBorder}`}
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold">{t.title}</span>
                  <span className="rounded bg-bg-0 px-2 py-0.5 font-mono text-[10px] font-semibold">
                    {t.chip}
                  </span>
                </div>
              </div>
              <p className="mt-1 text-xs text-ink-0 leading-relaxed font-sans">
                {t.summary}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default TensionCallout;
