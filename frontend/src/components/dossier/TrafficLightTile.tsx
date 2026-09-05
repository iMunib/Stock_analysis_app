export type TrafficLightStatus = "green" | "amber" | "red" | "neutral";

export interface TrafficLightTileProps {
  number: number;
  title: string;
  statusText: string;
  status: TrafficLightStatus;
  description: React.ReactNode;
  metrics?: { label: string; value: string | number | null }[];
  className?: string;
}

export function TrafficLightTile({
  number,
  title,
  statusText,
  status,
  description,
  metrics,
  className = "",
}: TrafficLightTileProps) {
  const statusStyles: Record<
    TrafficLightStatus,
    { dot: string; badge: string; text: string; border: string }
  > = {
    green: {
      dot: "bg-pos",
      badge: "bg-pos-weak text-pos border-pos/40",
      text: "text-pos",
      border: "border-l-pos",
    },
    amber: {
      dot: "bg-warn",
      badge: "bg-warn-weak text-warn border-warn/40",
      text: "text-warn",
      border: "border-l-warn",
    },
    red: {
      dot: "bg-neg",
      badge: "bg-neg-weak text-neg border-neg/40",
      text: "text-neg",
      border: "border-l-neg",
    },
    neutral: {
      dot: "bg-info",
      badge: "bg-info-weak text-info border-info/40",
      text: "text-info",
      border: "border-l-info",
    },
  };

  const current = statusStyles[status] || statusStyles.green;

  return (
    <div
      className={`rounded-card border border-border border-l-[3px] ${current.border} bg-bg-1 p-4 shadow-card flex flex-col justify-between transition-colors ${className}`}
    >
      <div>
        <div className="flex items-center justify-between gap-2 border-b border-border/70 pb-2.5 mb-2.5">
          <span className="font-heading text-xs font-bold uppercase tracking-wider text-ink-2">
            {number}. {title}
          </span>
          <span
            className={`inline-flex items-center gap-1.5 rounded-chip border px-2 py-0.5 font-mono text-[11px] font-semibold ${current.badge}`}
          >
            <span className={`h-1.5 w-1.5 rounded-full ${current.dot}`} aria-hidden="true" />
            <span>{statusText}</span>
          </span>
        </div>

        <div className="text-xs text-ink-0 leading-relaxed font-sans mb-3">
          {description}
        </div>
      </div>

      {metrics && metrics.length > 0 && (
        <div className="mt-2 pt-2.5 border-t border-border/50 grid grid-cols-2 gap-2">
          {metrics.map((m, i) => (
            <div key={i} className="flex flex-col">
              <span className="text-[10px] font-mono uppercase text-ink-2 truncate">
                {m.label}
              </span>
              <span className="font-mono text-xs font-semibold text-ink-0">
                {m.value != null ? m.value : "—"}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default TrafficLightTile;
