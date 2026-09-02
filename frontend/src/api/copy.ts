/** Deterministic copy templates (no LLM). Grade-10 language. */

export function signalLabel(signal: string | null | undefined): string {
  switch (signal) {
    case "strong_candidate":
      return "Strong candidate";
    case "constructive":
      return "Constructive";
    case "mixed":
      return "Mixed";
    case "weak":
      return "Weak";
    case "avoid":
      return "Avoid";
    case "insufficient_data":
      return "Insufficient data";
    default:
      return "Not scored";
  }
}

export function growthCopy(growth: number | null | undefined): string {
  return growth === null || growth === undefined
    ? "Growth not scored — fewer than 3 years of history in the database."
    : `Growth scored ${growth.toFixed(1)}/10 from the years on file.`;
}

export function coveragePenaltyCopy(coverage: number | null | undefined, penalty: number | null | undefined): string | null {
  if (coverage === null || coverage === undefined) return null;
  if (coverage >= 4) return null;
  return penalty != null && penalty < 1
    ? `Composite reduced because one or more pillars are missing (${coverage} of 4 scored; ×${penalty}).`
    : "Composite reduced because one or more pillars are missing.";
}

export function signalCopy(signal: string | null | undefined): string {
  switch (signal) {
    case "mixed":
      return "Neither cheap nor clearly high-quality versus peers in the same currency.";
    case "strong_candidate":
      return "Scores well on most pillars versus peers in the same currency.";
    case "constructive":
      return "More strengths than weaknesses versus peers in the same currency.";
    case "weak":
      return "More weaknesses than strengths versus peers in the same currency.";
    case "avoid":
      return "Weak on several pillars versus peers in the same currency.";
    default:
      return "Not enough data to compare against peers.";
  }
}

export function halalCopy(status: string | null | undefined): string {
  switch (status) {
    case "not_halal":
      return "Flagged on business-activity screen (e.g. conventional finance). Not a religious ruling.";
    case "halal_candidate":
      return "Activity and ratio screens passed (approximation, not a religious ruling).";
    default:
      return "Halal status unknown — missing inputs (often interest income).";
  }
}

export function bankPathCopy(isFinancial: boolean): string | null {
  return isFinancial ? "Bank/insurer metrics used (not FCF/gross margin)." : null;
}

export function money(v: number | null | undefined, currency: string | null | undefined): string {
  if (v === null || v === undefined) return "—";
  const sign = v < 0 ? "-" : "";
  const abs = Math.abs(v);
  const suffix = currency ? ` ${currency}` : "";
  if (abs >= 1e12) return `${sign}$${(abs / 1e12).toFixed(2)}T${suffix}`;
  if (abs >= 1e9) return `${sign}$${(abs / 1e9).toFixed(2)}B${suffix}`;
  if (abs >= 1e6) return `${sign}$${(abs / 1e6).toFixed(1)}M${suffix}`;
  return `${sign}$${abs.toLocaleString()}${suffix}`;
}

export function ratio(v: number | null | undefined, digits = 1): string {
  if (v === null || v === undefined) return "—";
  return v.toFixed(digits);
}

export function pct(v: number | null | undefined, digits = 1): string {
  if (v === null || v === undefined) return "—";
  return `${(v * 100).toFixed(digits)}%`;
}

export function gapLabel(gap: string): string {
  const map: Record<string, string> = {
    growth_history: "fewer than 3 years of history on file",
    valuation_multiples: "no PE or PB available",
    bank_capital: "no regulatory capital figures",
    gross_profit: "no gross profit (typical for lenders)",
    total_debt: "no corporate debt figure (typical for insurers)",
    market_cap: "no market cap (shares not on file)",
    fcf: "no free cash flow (typical for lenders)",
  };
  return map[gap] ?? gap.replace(/_/g, " ");
}
