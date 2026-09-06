import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../../api/client";
import { Card, Page } from "../layout";

export default function DossierNotFound({ companyId }: { companyId: string }) {
  const [ingesting, setIngesting] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [stepText, setStepText] = useState<string>("Initializing ingestion pipeline…");
  const [activeStep, setActiveStep] = useState<number>(0);
  const [secondsElapsed, setSecondsElapsed] = useState<number>(0);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  const parts = companyId.split(":");
  const ticker = (parts.length >= 2 ? parts[1] : companyId).toUpperCase();

  const steps = [
    "Connecting to SEC EDGAR & Yahoo Finance API",
    "Extracting multi-year 10-K / 10-Q financial statements",
    "Computing 3NF financial ratios, Altman Z, Beneish M-Score & ROIC",
    "Calibrating peer percentiles and composite scores",
  ];

  // Auto-tick elapsed timer while ingesting
  useEffect(() => {
    let timer: ReturnType<typeof setInterval> | undefined;
    if (ingesting && !done) {
      timer = setInterval(() => {
        setSecondsElapsed((s) => s + 1);
      }, 1000);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [ingesting, done]);

  // Advance step animation while job is running
  useEffect(() => {
    let stepTimer: ReturnType<typeof setInterval> | undefined;
    if (ingesting && !done) {
      stepTimer = setInterval(() => {
        setActiveStep((prev) => (prev < steps.length - 1 ? prev + 1 : prev));
      }, 3500);
    }
    return () => {
      if (stepTimer) clearInterval(stepTimer);
    };
  }, [ingesting, done, steps.length]);

  const handleFetch = () => {
    setIngesting(true);
    setErrorMsg(null);
    setDone(false);
    setSecondsElapsed(0);
    setActiveStep(0);
    setStepText("Contacting ingest queue…");

    api
      .ingest(ticker)
      .then((res) => {
        if (res.job_id) {
          setJobId(res.job_id);
          setStepText("Pipeline running in background…");
          const interval = setInterval(async () => {
            try {
              const j = await api.job(res.job_id!);
              if (j.status === "succeeded" || j.step === "done") {
                clearInterval(interval);
                setDone(true);
                setActiveStep(steps.length);
                setStepText("Enrichment complete! Loading complete fundamentals…");
                setTimeout(() => window.location.reload(), 1500);
              } else if (j.status === "failed") {
                clearInterval(interval);
                setIngesting(false);
                setErrorMsg(j.message || "Ingestion pipeline encountered an error.");
              } else if (j.step) {
                setStepText(`Step: ${j.step}`);
              }
            } catch {
              // Fallback reload if job completed and was cleared
              clearInterval(interval);
              setTimeout(() => window.location.reload(), 2000);
            }
          }, 1500);
        } else {
          setDone(true);
          setTimeout(() => window.location.reload(), 1200);
        }
      })
      .catch((e: ApiError) => {
        setErrorMsg(e.message || "Network error queueing ingestion.");
        setIngesting(false);
      });
  };

  return (
    <Page>
      <div className="max-w-2xl mx-auto py-8 space-y-6">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-accent-weak text-accent border border-accent/40">
              {ticker}
            </span>
            <span className="font-mono text-xs text-ink-2">{companyId}</span>
          </div>
          <h1 className="font-display text-3xl font-bold tracking-tight text-ink-0">
            {ingesting ? `Enriching ${ticker} Fundamentals…` : `${ticker} Not Yet in Library`}
          </h1>
          <p className="text-sm text-ink-1">
            {ingesting
              ? "The automated Python ingestion and calculation pipeline is running in the background. Multi-year SEC filings and financial ratios are being computed."
              : "This stock is not currently indexed in the local 720-company universe. You can dynamically ingest and calculate all fundamentals right now."}
          </p>
        </div>

        {ingesting ? (
          <Card padding="lg" className="border-accent/40 bg-bg-1 shadow-card space-y-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-accent"></span>
                </span>
                <span className="font-mono text-xs font-semibold text-ink-0">
                  {done ? "Completed!" : stepText}
                </span>
              </div>
              <span className="font-mono text-xs text-ink-2">
                {secondsElapsed}s elapsed
              </span>
            </div>

            {/* Stepper */}
            <div className="space-y-3">
              {steps.map((s, idx) => {
                const isPassed = activeStep > idx || done;
                const isCurrent = activeStep === idx && !done;
                return (
                  <div key={s} className="flex items-center gap-3 text-xs">
                    <div
                      className={`h-5 w-5 rounded-full flex items-center justify-center font-mono text-[10px] font-bold shrink-0 transition-colors ${
                        isPassed
                          ? "bg-pos/20 text-pos border border-pos/40"
                          : isCurrent
                          ? "bg-accent text-bg-0 animate-pulse font-bold"
                          : "bg-bg-2 text-ink-2 border border-border"
                      }`}
                    >
                      {isPassed ? "✓" : idx + 1}
                    </div>
                    <span
                      className={`font-medium transition-colors ${
                        isPassed
                          ? "text-ink-0"
                          : isCurrent
                          ? "text-accent font-semibold"
                          : "text-ink-2"
                      }`}
                    >
                      {s}
                    </span>
                  </div>
                );
              })}
            </div>

            {jobId && (
              <div className="pt-2 border-t border-border flex items-center justify-between text-[11px] font-mono text-ink-2">
                <span>Job ID: {jobId}</span>
                <span>Auto-refreshing on completion…</span>
              </div>
            )}
          </Card>
        ) : (
          <Card padding="lg" className="space-y-4">
            <div className="space-y-1">
              <h3 className="text-sm font-semibold text-ink-0">
                1-Click Python Ingestion Pipeline
              </h3>
              <p className="text-xs text-ink-1 leading-relaxed">
                Will extract multi-year financials from SEC EDGAR (or Yahoo Finance for TSX), compute 3NF ratios (Altman Z, Beneish M-Score, ROIC, CAGRs), calibrate peer percentiles, and generate the full 7-tab institutional dossier.
              </p>
            </div>

            {errorMsg && (
              <div className="rounded-card border border-neg/40 bg-neg/10 p-3 text-xs text-neg font-mono">
                {errorMsg}
              </div>
            )}

            <div className="flex items-center gap-3 pt-2">
              <button
                onClick={handleFetch}
                className="inline-flex items-center gap-2 rounded-card border border-accent/60 bg-accent px-4 py-2 text-xs font-semibold text-bg-0 hover:bg-accent/90 transition-colors shadow-sm"
              >
                <span>⚡</span>
                <span>Fetch & Enrich {ticker}</span>
              </button>
              <Link
                to="/"
                className="rounded-card border border-border bg-bg-2 px-3 py-2 text-xs font-medium text-ink-1 hover:text-ink-0 transition-colors"
              >
                Return to Desk
              </Link>
            </div>
          </Card>
        )}

        <div className="flex gap-4 text-xs font-mono pt-2">
          <Link to="/screen" className="text-accent hover:underline">Go to screener →</Link>
          <Link to="/sectors" className="text-accent hover:underline">Browse sectors →</Link>
          <Link to="/" className="text-accent hover:underline">Back to desk →</Link>
        </div>
      </div>
    </Page>
  );
}
