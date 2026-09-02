import React from "react";

export type ChipTone = "neutral" | "positive" | "negative" | "warning" | "info";

export interface ChipProps {
  children: React.ReactNode;
  tone?: ChipTone;
  icon?: React.ReactNode;
  showIcon?: boolean;
  size?: "sm" | "md";
  className?: string;
  title?: string;
}

const toneStyles: Record<ChipTone, { badge: string; defaultIcon: string }> = {
  neutral: {
    badge: "border-border text-ink-1 bg-bg-2/50",
    defaultIcon: "•",
  },
  positive: {
    badge: "border-pos/40 text-pos bg-pos-weak",
    defaultIcon: "✓",
  },
  negative: {
    badge: "border-neg/40 text-neg bg-neg-weak",
    defaultIcon: "✕",
  },
  warning: {
    badge: "border-warn/40 text-warn bg-warn-weak",
    defaultIcon: "!",
  },
  info: {
    badge: "border-info/40 text-info bg-info-weak",
    defaultIcon: "ℹ",
  },
};

export function Chip({
  children,
  tone = "neutral",
  icon,
  showIcon = true,
  size = "md",
  className = "",
  title,
}: ChipProps) {
  const style = toneStyles[tone] ?? toneStyles.neutral;
  const renderedIcon =
    !showIcon
      ? null
      : icon !== undefined
      ? icon
      : <span aria-hidden="true" className="font-bold text-[9px]">{style.defaultIcon}</span>;
  const sizeClasses = size === "sm" ? "px-1.5 py-0.5 text-[9px]" : "px-2 py-0.5 text-[10px]";

  return (
    <span
      title={title}
      className={`inline-flex items-center gap-1.5 rounded-chip border font-mono uppercase tracking-wider font-medium animate-chip ${style.badge} ${sizeClasses} ${className}`}
    >
      {renderedIcon}
      <span>{children}</span>
    </span>
  );
}

export default Chip;
