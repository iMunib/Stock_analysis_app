import { useId, useState } from "react";
import { glossaryEntry } from "../api/glossary";

/** Term with a "?" tooltip wired to the locked glossary copy. Keyboard focus, hover, and tap supported. */
export default function InfoTip({ term, inline }: { term: string; inline?: boolean }) {
  const [open, setOpen] = useState(false);
  const tipId = useId();
  const entry = glossaryEntry(term);
  if (!entry) return null;

  const accessibleText = `${entry.short} Why it matters: ${entry.why} How to read: ${entry.how_to_read}`;

  return (
    <span
      className={`relative ${inline ? "inline" : "inline-block"} ml-1.5 align-middle normal-case tracking-normal`}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        type="button"
        aria-label={`About ${entry.term}: ${entry.short}`}
        aria-describedby={tipId}
        title={accessibleText}
        onClick={() => setOpen((prev) => !prev)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        className="inline-flex h-3.5 w-3.5 items-center justify-center rounded-full border border-border text-[8px] font-mono leading-none text-ink-2 hover:border-accent hover:text-accent focus:border-accent focus:text-accent focus:outline-none cursor-pointer transition-colors"
      >
        ?
      </button>
      <span
        id={tipId}
        role="tooltip"
        className={`${
          open ? "block" : "hidden"
        } absolute bottom-full left-1/2 z-50 mb-2 w-72 -translate-x-1/2 rounded-card border border-border bg-bg-1 p-3 text-left text-xs leading-relaxed text-ink-0 shadow-modal pointer-events-none`}
      >
        <span className="block font-semibold text-accent">{entry.term}</span>
        <span className="mt-1 block text-ink-0">{entry.short}</span>
        <span className="mt-1.5 block text-ink-1 text-[11px]">
          <strong className="text-ink-2 font-mono uppercase text-[9px]">Why:</strong> {entry.why}
        </span>
        <span className="mt-1 block text-ink-1 text-[11px]">
          <strong className="text-ink-2 font-mono uppercase text-[9px]">How to read:</strong> {entry.how_to_read}
        </span>
      </span>
    </span>
  );
}
