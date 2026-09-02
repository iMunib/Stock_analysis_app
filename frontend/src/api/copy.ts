import type { DossierOut } from "./types";

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

export function mixedCurrencyWarning(currencies: string[] | null | undefined): string | null {
  const uniq = Array.from(new Set((currencies ?? []).filter((c) => c)));
  if (uniq.length <= 1) return null;
  return `Mixed currencies: ${uniq.join(" vs ")}. Scores and ratios stay comparable, but money amounts stay in each company's own currency — never converted.`;
}

/** Deterministic "why" bullets built only from payload fields. 3-6 bullets, grade-10. */
export function whyBullets(d: DossierOut): string[] {
  const bullets: string[] = [];
  const s = d.score;
  const snap = d.latest_snapshot ?? {};

  if (s?.peer_rank != null && s?.peer_n != null) {
    const peer = s.peer_set_type === "custom_industry_currency" ? "same industry" : "same sector";
    bullets.push(`Ranks ${s.peer_rank} of ${s.peer_n} among ${peer} peers in the same currency.`);
  }
  if (s && s.pillars.growth != null) {
    bullets.push(`Growth scored ${s.pillars.growth.toFixed(1)}/10 from the years on file.`);
  } else if (s) {
    bullets.push("Growth not scored — fewer than three years of history in the database.");
  }

  const pe = typeof snap.pe_calc === "number" ? snap.pe_calc : null;
  if (pe != null && pe > 0) bullets.push(`Trades at ${pe.toFixed(1)}× earnings.`);
  else if (pe != null && pe <= 0) bullets.push("Earnings are negative, so no price-to-earnings multiple applies.");

  const pb = typeof snap.pb_calc === "number" ? snap.pb_calc : null;
  if (pb != null && pb > 0) bullets.push(`Trades at ${pb.toFixed(1)}× book value.`);

  const roe = typeof snap.roe_calc === "number" ? snap.roe_calc : null;
  if (roe != null) bullets.push(`${(roe * 100).toFixed(1)}% return on equity.`);

  const fcfm = typeof snap.fcfmargin_calc === "number" ? snap.fcfmargin_calc : null;
  if (fcfm != null) bullets.push(`${(fcfm * 100).toFixed(1)}% free-cash-flow margin.`);

  const sheet = (d.identity.custom_industry_sheet ?? "").toLowerCase();
  const sector = (d.identity.gics_sector ?? "").toLowerCase();
  if (sector === "financials" || ["banks", "insurance", "credit_services"].includes(sheet)) {
    bullets.push("Bank/insurer metrics used (not FCF/gross margin).");
  }

  if (d.halal) bullets.push(`Halal: ${d.halal.status.replace(/_/g, " ")}.`);

  return bullets.slice(0, 6);
}

export function money(v: number | null | undefined, currency: string | null | undefined): string {
  if (v === null || v === undefined) return "—";
  const sign = v < 0 ? "-" : "";
  const abs = Math.abs(v);
  const cur = (currency ?? "").trim().toUpperCase();
  const isDollar = !cur || cur === "USD" || cur === "CAD";
  const sym = isDollar ? "$" : `${cur} `;
  const suffix = isDollar && cur ? ` ${cur}` : "";
  if (abs >= 1e12) return `${sign}${sym}${(abs / 1e12).toFixed(2)}T${suffix}`;
  if (abs >= 1e9) return `${sign}${sym}${(abs / 1e9).toFixed(2)}B${suffix}`;
  if (abs >= 1e6) return `${sign}${sym}${(abs / 1e6).toFixed(1)}M${suffix}`;
  return `${sign}${sym}${abs.toLocaleString()}${suffix}`;
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

export const ERROR_CATALOG: Record<string, string> = {
  SYMBOL_NOT_FOUND: "We could not find that ticker. Try AMD, BABA, SHOP.TO, or KITS.TO.",
  LISTING_AMBIGUOUS: "Multiple listings. Pick US ADR or HK/TSX (show choices).",
  PROVIDER_TIMEOUT: "Data source timed out. Retry.",
  RATE_LIMIT: "Source is busy. Wait a minute and retry.",
  NO_STATEMENTS: "Listed, but no annual statements. We stored the price only.",
  CURRENCY_UNCLEAR: "Statements exist but currency is unclear. We did not label CNY as USD.",
  SCORE_PARTIAL: "Saved, but some pillars missing (shares/price). See “What is missing”.",
  INTERNAL: "Something broke on our side. Retry.",
};

export function errorCatalogCopy(code: string | null | undefined, fallback?: string | null): string {
  if (code && ERROR_CATALOG[code]) return ERROR_CATALOG[code];
  return fallback ?? ERROR_CATALOG.INTERNAL;
}
