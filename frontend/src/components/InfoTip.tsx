import { useState } from "react";
import { glossaryEntry } from "../api/glossary";

/** Term with a "?" tooltip wired to the locked glossary copy. */
export default function InfoTip({ term }: { term: string }) {
  const [open, setOpen] = useState(false);
  const entry = glossaryEntry(term);
  if (!entry) return null;
  return (
    <span className="relative inline-block ml-1">
      <button
        type="button"
        aria-label={`What is ${entry.term}?`}
        onClick={() => setOpen(!open)}
        onBlur={() => setOpen(false)}
        className="inline-flex h-4 w-4 items-center justify-center rounded-full border border-line2 text-[9px] leading-none text-dim hover:border-gold hover:text-gold"
      >
        ?
      </button>
      {open && (
        <span className="absolute bottom-full left-1/2 z-40 mb-2 w-72 -translate-x-1/2 rounded-md border border-line2 bg-panel p-3 text-xs leading-relaxed text-paper shadow-xl">
          <strong className="text-gold">{entry.term}</strong> — {entry.short}
          <br />
          <span className="text-fog">Why: {entry.why}</span>
        </span>
      )}
    </span>
  );
}
