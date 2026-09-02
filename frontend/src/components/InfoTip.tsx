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
        className="inline-flex h-3.5 w-3.5 items-center justify-center rounded-full border border-line2 text-[8px] font-mono leading-none text-dim hover:border-gold hover:text-gold focus:border-gold focus:text-gold focus:outline-none cursor-pointer"
      >
        ?
      </button>
      <span
        id={tipId}
        role="tooltip"
        className={`${
          open ? "block" : "hidden"
        } absolute bottom-full left-1/2 z-50 mb-2 w-72 -translate-x-1/2 rounded-md border border-line2 bg-panel p-3 text-left text-xs leading-relaxed text-paper shadow-2xl pointer-events-none`}
      >
        <span className="block font-semibold text-gold">{entry.term}</span>
        <span className="mt-1 block text-paper">{entry.short}</span>
        <span className="mt-1.5 block text-fog text-[11px]">
          <strong className="text-dim">Why:</strong> {entry.why}
        </span>
        <span className="mt-1 block text-fog text-[11px]">
          <strong className="text-dim">How to read:</strong> {entry.how_to_read}
        </span>
      </span>
    </span>
  );
}
