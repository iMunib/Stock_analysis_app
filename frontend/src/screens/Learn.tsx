import { GLOSSARY } from "../api/glossary";

export default function Learn() {
  return (
    <div className="space-y-6 animate-fade-in">
      <header className="space-y-2">
        <h1 className="font-display text-3xl tracking-tight">Learn — what every header means</h1>
        <p className="max-w-2xl text-sm text-fog">
          The score is deterministic math (v1): Quality 30% · Value 25% · Growth 25% · Risk 20%.
          No AI in the score. Narration, where offered, is a language model explaining the numbers
          already on screen — labeled "Narration (not the score)".
        </p>
      </header>
      <ul className="grid gap-3 sm:grid-cols-2" aria-label="Glossary">
        {GLOSSARY.map((g) => (
          <li key={g.term} className="rounded-md border border-line bg-panel p-4">
            <p className="font-medium text-paper">{g.term}</p>
            <p className="mt-1 text-sm text-fog">{g.short}</p>
            <p className="mt-1 text-xs text-dim">Why: {g.why}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
