import { useState } from "react";
import { api, ApiError } from "../api/client";
import type { NarrationResult } from "../api/types";
import { Spinner } from "./ui";
import { Card } from "./layout";

/** "Generate explanation" panel. 503/504 -> honest unavailable, facts stay on screen. */
export default function NarrationPanel({
  endpoint,
  label,
}: {
  endpoint: string; // full POST path
  label: string;
}) {
  const [state, setState] = useState<"idle" | "loading" | "done" | "unavailable">("idle");
  const [result, setResult] = useState<NarrationResult | null>(null);

  const generate = async () => {
    setState("loading");
    try {
      const body = await api.narrate(endpoint);
      if (body.narration_unavailable) {
        setResult(body);
        setState("unavailable");
        return;
      }
      setResult(body);
      setState("done");
    } catch (e) {
      const message =
        e instanceof ApiError
          ? e.message
          : e instanceof Error
            ? e.message
            : "provider did not respond";
      setResult({ narration_unavailable: true, reason: message });
      setState("unavailable");
    }
  };

  const action = (
    <button
      type="button"
      onClick={generate}
      disabled={state === "loading"}
      className="rounded-card border border-accent/60 bg-accent-weak px-3.5 py-1.5 font-mono text-xs text-accent hover:bg-accent/20 disabled:cursor-not-allowed disabled:opacity-40 transition-colors"
    >
      {state === "loading" ? "Writing explanation…" : "Generate explanation"}
    </button>
  );

  return (
    <Card
      title={label}
      subtitle={
        <span>
          <span className="font-mono uppercase tracking-wider text-accent font-medium">Narration (not the score)</span> - a free
          model explains the numbers already on screen. It cannot change ratings.
        </span>
      }
      action={action}
      padding="md"
    >
      {state === "loading" && (
        <div className="mt-2 flex items-center gap-3 rounded-card border border-border bg-bg-0 p-3 text-xs text-ink-0">
          <Spinner label="Writing explanation… 30–90s on free models." />
        </div>
      )}

      {state === "done" && result?.narration && (
        <div className="mt-3 rounded-card border border-border bg-bg-0 p-3.5 text-xs leading-relaxed text-ink-0">
          <p className="whitespace-pre-line">{result.narration}</p>
          <p className="mt-2 font-mono text-[10px] text-ink-2 border-t border-border pt-2">
            model: {result.model}
            {result.cached ? " · cached" : ""} · research notes, not investment advice
          </p>
        </div>
      )}

      {state === "unavailable" && (
        <div role="alert" className="mt-3 rounded-card border border-warn/60 bg-warn-weak p-3 text-xs text-ink-0 leading-relaxed font-mono">
          Narration unavailable - {result?.reason ?? "provider did not respond"}. The facts on this page are still
          the source of truth.
        </div>
      )}
    </Card>
  );
}