import React from "react";

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  body: string;
  cta?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  icon,
  title,
  body,
  cta,
  className = "",
}: EmptyStateProps) {
  return (
    <div
      role="status"
      className={`rounded-card border border-border bg-bg-1 p-8 text-center space-y-3 max-w-lg mx-auto my-6 ${className}`}
    >
      {icon && (
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-bg-2 text-accent text-xl" aria-hidden="true">
          {icon}
        </div>
      )}
      <h3 className="font-heading text-lg font-semibold text-ink-0">
        {title}
      </h3>
      <p className="text-xs sm:text-sm text-ink-1 leading-relaxed">
        {body}
      </p>
      {cta && <div className="pt-2">{cta}</div>}
    </div>
  );
}

export default EmptyState;
