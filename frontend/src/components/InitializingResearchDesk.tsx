export default function InitializingResearchDesk() {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-busy="true"
      aria-label="Initializing Research Desk"
      className="flex min-h-[60vh] flex-col items-center justify-center px-6 py-16 text-center"
    >
      <div
        className="h-10 w-10 rounded-full border-2 border-border border-t-accent animate-spin motion-reduce:animate-none"
        aria-hidden="true"
      />
      <h1 className="mt-6 font-heading text-lg font-semibold tracking-tight text-ink-0">
        Initializing Research Desk...
      </h1>
      <p className="mt-2 max-w-md text-sm leading-relaxed text-ink-1">
        Warming up the research API and verifying the local SQLite WAL database. This takes just a moment on first boot.
      </p>
      <p className="mt-3 font-mono text-[11px] uppercase tracking-wider text-ink-2">
        Checking /health · Retrying automatically
      </p>
    </div>
  );
}
