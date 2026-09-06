import { useState } from "react";
import { api, ApiError } from "../../api/client";
import type { SwotOut } from "../../api/types";
import { Card } from "../layout";
import { ErrorBanner, Spinner } from "../ui";

export default function SwotCard({ companyId }: { companyId: string }) {
  const [swot, setSwot] = useState<SwotOut | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const draft = () => {
    setLoading(true);
    setError(null);
    api
      .swotResearch(companyId)
      .then(setSwot)
      .catch((e: ApiError) => setError(e.message))
      .finally(() => setLoading(false));
  };

  return (
    <Card
      title="Moat &amp; SWOT Draft"
      subtitle="LLM draft from our facts JSON. Not a 10-K."
      action={
        !swot && !loading ? (
          <button
            onClick={draft}
            className="rounded-card border border-accent/60 bg-accent-weak px-3 py-1 font-mono text-xs text-accent hover:bg-accent/20 transition-colors"
          >
            Draft SWOT from numbers
          </button>
        ) : null
      }
    >
      {loading && <Spinner label="Drafting SWOT from numbers JSON (free model)..." />}
      {error && <ErrorBanner message={error} onRetry={draft} />}

      {swot && (
        <div className="space-y-3 text-xs leading-relaxed">
          <div className="flex items-center justify-between text-[10px] text-ink-2 font-mono">
            <span>
              {swot.model} {swot.cached && "(cached)"}
            </span>
            <span className="text-accent font-medium">{swot.label}</span>
          </div>
          <div className="whitespace-pre-line rounded-card bg-bg-2/50 p-3.5 font-mono text-xs text-ink-0 border border-border">
            {swot.swot}
          </div>
          <p className="text-[10px] text-ink-2">{swot.disclaimer}</p>
        </div>
      )}
    </Card>
  );
}
