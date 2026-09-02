import { GLOSSARY } from "../api/glossary";
import { Card, Page } from "../components/layout";

export default function Learn() {
  return (
    <Page
      title="Learn — what every header means"
      description='The score is deterministic math (v1): Quality 30% · Value 25% · Growth 25% · Risk 20%. No AI in the score. Narration, where offered, is a language model explaining the numbers already on screen — labeled "Narration (not the score)".'
    >
      <ul className="grid gap-3 sm:grid-cols-2" aria-label="Glossary">
        {GLOSSARY.map((g) => (
          <li key={g.term}>
            <Card padding="md" className="h-full">
              <p className="font-semibold text-ink-0 text-sm font-heading">{g.term}</p>
              <p className="mt-1 text-xs text-ink-1 leading-relaxed">{g.short}</p>
              <p className="mt-2 text-[11px] text-ink-2 font-mono border-t border-border pt-2">Why: {g.why}</p>
            </Card>
          </li>
        ))}
      </ul>
    </Page>
  );
}
