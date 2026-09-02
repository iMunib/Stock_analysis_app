import React from "react";

export type CardTone = "neutral" | "positive" | "negative" | "warning" | "info";

export interface CardProps extends Omit<React.HTMLAttributes<HTMLDivElement>, "title"> {
  children?: React.ReactNode;
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  infoTip?: React.ReactNode;
  action?: React.ReactNode;
  tone?: CardTone;
  staggerIndex?: 1 | 2 | 3 | 4 | 5 | 6;
  interactive?: boolean;
  padding?: "none" | "sm" | "md" | "lg";
  className?: string;
}

const toneBorders: Record<CardTone, string> = {
  neutral: "",
  positive: "border-l-[3px] border-l-pos",
  negative: "border-l-[3px] border-l-neg",
  warning: "border-l-[3px] border-l-warn",
  info: "border-l-[3px] border-l-info",
};

const paddingClasses = {
  none: "p-0",
  sm: "p-3",
  md: "p-4 sm:p-5",
  lg: "p-6",
};

export function Card({
  children,
  title,
  subtitle,
  infoTip,
  action,
  tone = "neutral",
  staggerIndex,
  interactive = false,
  padding = "md",
  className = "",
  ...rest
}: CardProps) {
  const toneBorder = toneBorders[tone] || "";
  const pad = paddingClasses[padding] || paddingClasses.md;
  const stagger = staggerIndex ? `animate-rise stagger-${staggerIndex}` : "";
  const hoverClass = interactive ? "interactive-card cursor-pointer" : "";

  return (
    <div
      className={`rounded-card border border-border bg-bg-1 shadow-card transition-colors ${toneBorder} ${pad} ${stagger} ${hoverClass} ${className}`}
      {...rest}
    >
      {(title || action || infoTip) && (
        <div className="flex items-start justify-between gap-3 border-b border-border pb-3 mb-4">
          <div>
            <div className="flex items-center gap-1.5 font-heading text-sm sm:text-base font-semibold text-ink-0">
              {title}
              {infoTip}
            </div>
            {subtitle && (
              <p className="mt-0.5 text-xs text-ink-1 leading-relaxed">
                {subtitle}
              </p>
            )}
          </div>
          {action && <div className="shrink-0">{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
}
