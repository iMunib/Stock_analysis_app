/** Locked glossary copy (grade-10). Phase 10 Stage A. Each entry: term, short, why. */

export interface GlossaryEntry {
  term: string;
  short: string;
  why: string;
}

export const GLOSSARY: GlossaryEntry[] = [
  {
    term: "Composite",
    short: "Combined 0–10 research score from four pillars. Higher is stronger on this method, not a buy order.",
    why: "One number is easier than 20 ratios, but it hides missing data.",
  },
  {
    term: "Quality",
    short: "How healthy earnings and the balance sheet look (profit, cash vs profit, margins).",
    why: "Cheap junk still fails.",
  },
  {
    term: "Value",
    short: "How cheap the stock is versus peers in the same currency (PE, PB, earnings yield).",
    why: "A great company can be too expensive.",
  },
  {
    term: "Growth",
    short: "How fast revenue/earnings/cash grew over years. Needs ≥3 years or it is blank.",
    why: "One good year is not a trend.",
  },
  {
    term: "Risk",
    short: "How fragile the company looks (debt, coverage, volatility). In this app a higher Risk pillar means safer.",
    why: "Leverage is easy to miss.",
  },
  {
    term: "Signal",
    short: "Bucket of the composite (Avoid → Strong candidate). Research label, not advice.",
    why: "A shared vocabulary beats a bare number.",
  },
  {
    term: "Peer rank",
    short: "Place among similar companies in the same industry and currency (1 = best composite in that set).",
    why: "Ranking makes the score relative, not absolute.",
  },
  {
    term: "PE",
    short: "Price ÷ earnings per share. Years of current earnings you pay. Blank if earnings ≤ 0.",
    why: "High can mean expensive or high expected growth.",
  },
  {
    term: "PB",
    short: "Price ÷ book equity. Above 1 means the market pays more than accounting net assets.",
    why: "Book value anchors the price to the balance sheet.",
  },
  {
    term: "EV/EBITDA",
    short: "Enterprise value ÷ operating profit before D&A. Useful peer multiple; weaker for banks.",
    why: "Debt-inclusive view of cheapness.",
  },
  {
    term: "ROE",
    short: "Profit ÷ equity. How hard equity is working. Extreme values can be leverage, not skill.",
    why: "The classic profitability lens.",
  },
  {
    term: "ROA",
    short: "Profit ÷ assets. Useful for banks; less flattered by thin equity.",
    why: "Asset efficiency without the leverage distortion.",
  },
  {
    term: "FCF margin",
    short: "Free cash flow ÷ revenue. Cash after capex. Often blank for banks on purpose.",
    why: "Cash is harder to flatter than profit.",
  },
  {
    term: "Coverage",
    short: "How many of the four pillars could be computed. Low coverage → composite is penalized.",
    why: "Honesty about missing data.",
  },
  {
    term: "Currency All",
    short: "Score/ratio ranking of USD and CAD names together. Money totals stay in separate USD and CAD panels and are never added.",
    why: "Scores are unitless; money is not.",
  },
  {
    term: "Narration",
    short: "Optional free-model paragraph about the numbers already on screen. Not the rating.",
    why: "Explains, never rates.",
  },
];

export function glossaryEntry(term: string): GlossaryEntry | undefined {
  return GLOSSARY.find((g) => g.term.toLowerCase() === term.toLowerCase());
}
