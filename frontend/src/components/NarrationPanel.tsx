import { useState } from "react";
import { api, ApiError } from "../api/client";
import type { NarrationResult } from "../api/types";
import { Spinner } from "./ui";

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

  return (
    <section aria-label={label} className="rounded-md border border-line bg-panel p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-display text-xl">{label}</h2>
          <p className="text-xs text-fog">
            <span className="font-mono uppercase tracking-wider text-mid">Narration (not the score)</span> — a free
            model explains the numbers already on screen. It cannot change ratings.
          </p>
        </div>
        <button
          type="button"
          onClick={generate}
          disabled={state === "loading"}
          className="rounded-md border border-gold/60 bg-gold/10 px-4 py-2 text-sm text-gold hover:bg-gold/20 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {state === "loading" ? "Writing explanation…" : "Generate explanation"}
        </button>
      </div>

      {state === "loading" && (
        <div className="mt-4 flex items-center gap-3 rounded border border-line2 bg-ink/50 p-3 text-sm text-paper">
          <Spinner label="Writing explanation… 30–90s on free models." />
        </div>
      )}

      {state === "done" && result?.narration && (
        <div className="mt-3 rounded border border-line2 bg-ink p-3 text-sm leading-relaxed text-paper">
          {result.narration}
          <p className="mt-2 font-mono text-[10px] text-dim">
            model: {result.model}
            {result.cached ? " · cached" : ""} · research notes, not investment advice
          </p>
        </div>
      )}

      {state === "unavailable" && (
        <div role="alert" className="mt-3 rounded border border-warn/60 bg-warn/10 p-3 text-sm text-paper">
          Narration unavailable — {result?.reason ?? "provider did not respond"}. The facts on this page are still
          the source of truth.
        </div>
      )}
    </section>
  );
}
