import React from "react";

export interface PageProps {
  children: React.ReactNode;
  breadcrumb?: React.ReactNode;
  title?: React.ReactNode;
  description?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}

export function Page({
  children,
  breadcrumb,
  title,
  description,
  actions,
  className = "",
}: PageProps) {
  return (
    <div
      className={`mx-auto w-full max-w-[var(--max-page-width)] space-y-5 animate-page ${className}`}
    >
      {breadcrumb && (
        <nav aria-label="Breadcrumb" className="text-xs text-ink-2 mb-2 font-mono">
          {breadcrumb}
        </nav>
      )}

      {(title || actions) && (
        <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-border">
          <div>
            {typeof title === "string" ? (
              <h1 className="font-display text-2xl sm:text-3xl font-bold tracking-tight text-ink-0">
                {title}
              </h1>
            ) : (
              title
            )}
            {description && (
              <p className="mt-1 text-sm text-ink-1 max-w-3xl">
                {description}
              </p>
            )}
          </div>
          {actions && <div className="flex items-center gap-3">{actions}</div>}
        </header>
      )}

      {children}
    </div>
  );
}

export default Page;
