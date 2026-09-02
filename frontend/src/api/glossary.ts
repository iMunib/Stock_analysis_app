/** Locked glossary copy (grade-10). Each entry: term, short, why, how_to_read. */

export interface GlossaryEntry {
  term: string;
  short: string;
  why: string;
  how_to_read: string;
}

export const GLOSSARY: GlossaryEntry[] = [
  {
    term: "Cur",
    short: "Trading currency of the stock (USD or CAD).",
    why: "Money amounts in different currencies must never be mixed or added.",
    how_to_read: "USD for US exchanges, CAD for TSX. Ratios are cross-border comparable; cash amounts stay in native currency.",
  },
  {
    term: "Composite",
    short: "Combined 0–10 research score from four pillars. Higher is stronger on this method, not a buy order.",
    why: "One number is easier than 20 ratios, but it hides missing data.",
    how_to_read: "8.0–10.0 is Strong Candidate, 6.5–8.0 Constructive, 5.0–6.5 Mixed, 3.5–5.0 Weak, <3.5 Avoid. Reduced if data is missing.",
  },
  {
    term: "Quality",
    short: "How healthy earnings and the balance sheet look (profit, cash vs profit, margins).",
    why: "Cheap junk still fails.",
    how_to_read: "Above 7 indicates durable margins and clean accounting; below 4 signals operational weakness.",
  },
  {
    term: "Value",
    short: "How cheap the stock is versus peers in the same currency (PE, PB, earnings yield).",
    why: "A great company can be too expensive.",
    how_to_read: "10 means cheapest in peer set; 0 means most expensive. Blank if no peers, negative earnings, or currency mismatch.",
  },
  {
    term: "Growth",
    short: "How fast revenue/earnings/cash grew over years. Needs ≥3 years or it is blank.",
    why: "One good year is not a trend.",
    how_to_read: "Needs at least 3 years of audited history. Blank if history is too short or restatements exist.",
  },
  {
    term: "Risk",
    short: "How fragile the company looks (debt, coverage, volatility). In this app a higher Risk pillar means safer.",
    why: "Leverage is easy to miss.",
    how_to_read: "Higher score means safer (low debt, strong coverage). Low score means elevated leverage or solvency risk.",
  },
  {
    term: "Signal",
    short: "Bucket of the composite (Avoid → Strong candidate). Research label, not advice.",
    why: "A shared vocabulary beats a bare number.",
    how_to_read: "Strong Candidate (8-10), Constructive (6.5-8), Mixed (5-6.5), Weak (3.5-5), or Avoid (0-3.5).",
  },
  {
    term: "Peer rank",
    short: "Place among similar companies in the same industry and currency (1 = best composite in that set).",
    why: "Ranking makes the score relative, not absolute.",
    how_to_read: "#1 is highest composite in that peer set. Broad peer set (n=N) means widened comparison. Never celebrate 1 of 1.",
  },
  {
    term: "PE",
    short: "Price divided by earnings per share.",
    why: "Tells you how many years of current profit you are paying.",
    how_to_read: "26.9 means expensive vs a peer at 15 unless growth is much higher. Blank if no profit or no price.",
  },
  {
    term: "PB",
    short: "Price divided by book equity.",
    why: "Above 1 means the market pays more than accounting net assets.",
    how_to_read: "Under 1.0 means trading below book equity. High PB (>5) requires high ROE to justify.",
  },
  {
    term: "EV/EBITDA",
    short: "Enterprise value divided by operating profit before D&A. Useful peer multiple; weaker for banks.",
    why: "Debt-inclusive view of cheapness.",
    how_to_read: "Lower is cheaper. Multiples under 10x are typical for mature firms; blank for financial firms.",
  },
  {
    term: "ROE",
    short: "Profit divided by equity. How hard equity is working. Extreme values can be leverage, not skill.",
    why: "The classic profitability lens.",
    how_to_read: "15%+ indicates high efficiency, but verify high debt is not inflating it. Blank if equity is negative.",
  },
  {
    term: "ROA",
    short: "Profit divided by assets. Useful for banks; less flattered by thin equity.",
    why: "Asset efficiency without the leverage distortion.",
    how_to_read: "Above 1% for banks or 6%+ for non-financials shows strong asset productivity.",
  },
  {
    term: "FCF margin",
    short: "Free cash flow divided by revenue. Cash after capex. Often blank for banks on purpose.",
    why: "Cash is harder to flatter than profit.",
    how_to_read: "15%+ is stellar cash generation; negative means cash burn. Blank for banks by design.",
  },
  {
    term: "Coverage",
    short: "How many of the four pillars could be computed. Low coverage -> composite is penalized.",
    why: "Honesty about missing data.",
    how_to_read: "4/4 receives full composite; 3/4 gets an 8% penalty; 2/4 gets 20% penalty; 1/4 gets 35% penalty.",
  },
  {
    term: "EPS",
    short: "Diluted earnings per share from continuing operations.",
    why: "The foundational per-share unit of accounting profitability.",
    how_to_read: "Positive means profitable. Compare YoY to see if earnings growth matches revenue growth.",
  },
  {
    term: "Net debt",
    short: "Total debt minus cash and short-term investments.",
    why: "Shows true net indebtedness after accounting for immediate liquid reserves.",
    how_to_read: "Negative net debt is net cash (bulletproof balance sheet). Large positive requires scrutiny.",
  },
  {
    term: "YoY",
    short: "Year-over-Year percentage change comparing the most recent fiscal year to the prior year.",
    why: "Highlights immediate annual momentum or contraction in fundamentals.",
    how_to_read: "+10% or more indicates solid expansion. Suspect or restated years are excluded from growth.",
  },
  {
    term: "Market cap",
    short: "Total equity value: stock price multiplied by total shares outstanding.",
    why: "Determines the size category of the company (mega, large, mid, small).",
    how_to_read: "Always quoted in the trading currency. Blank if either stock price or share count is missing.",
  },
  {
    term: "Revenue",
    short: "Total top-line sales generated from business operations.",
    why: "Top-line volume determines the fundamental scale of the business.",
    how_to_read: "Check YoY trend to ensure sales are expanding. Displayed in filing reporting currency.",
  },
  {
    term: "Net income",
    short: "Bottom-line accounting profit after all expenses, taxes, and interest.",
    why: "Represents accounting earnings belonging to shareholders.",
    how_to_read: "Compare with cash flow; earnings without cash can indicate lower earnings quality.",
  },
  {
    term: "Gross margin",
    short: "Gross profit divided by revenue: (Revenue - COGS) / Revenue.",
    why: "Measures fundamental pricing power and production efficiency before overhead.",
    how_to_read: "Higher is better. Software often runs 70–85%, retail 20–35%. Blank for banks.",
  },
  {
    term: "Price",
    short: "Most recent trading price per share on the listed exchange.",
    why: "Used to compute market valuation and valuation multiples.",
    how_to_read: "Always quoted in the trading currency (USD or CAD).",
  },
  {
    term: "Total debt",
    short: "Sum of short-term and long-term interest-bearing obligations.",
    why: "Debt obligations take precedence over equity holders in liquidation.",
    how_to_read: "Compare to cash flow and cash reserves. Blank for banks/insurers on purpose.",
  },
  {
    term: "Cash + ST inv.",
    short: "Cash, bank deposits, and liquid short-term marketable securities.",
    why: "Immediate liquidity buffer protecting against market disruptions.",
    how_to_read: "High cash balances reduce net debt and solvency risk.",
  },
  {
    term: "Shares",
    short: "Total number of common shares outstanding.",
    why: "Divides company fundamentals into per-share ownership slices.",
    how_to_read: "Rising share counts indicate dilution; falling share counts indicate share buybacks.",
  },
  {
    term: "Book equity",
    short: "Total stockholders' equity: accounting assets minus liabilities.",
    why: "The historical net worth recorded on the company balance sheet.",
    how_to_read: "Positive is standard. Negative book equity can occur from heavy buybacks or accumulated losses.",
  },
  {
    term: "Currency All",
    short: "Score/ratio ranking of USD and CAD names together. Money totals stay in separate USD and CAD panels and are never added.",
    why: "Scores are unitless; money is not.",
    how_to_read: "Compares unitless scores and multiples. Never converts or combines dollar figures.",
  },
  {
    term: "Narration",
    short: "Optional free-model paragraph about the numbers already on screen. Not the rating.",
    why: "Explains, never rates.",
    how_to_read: "Summarizes the numbers already calculated on the page. Does not alter or override the math score.",
  },
  {
    term: "Q·V·G·R",
    short: "Four pillar breakdown: Quality, Value, Growth, and Risk.",
    why: "Shows the relative contribution of each component to the composite score.",
    how_to_read: "Each pillar ranges from 0 to 10. Higher Risk means safer/less fragile.",
  },
];

export function glossaryEntry(term: string): GlossaryEntry | undefined {
  const norm = term.trim().toLowerCase();
  return GLOSSARY.find((g) => {
    const gn = g.term.toLowerCase();
    if (gn === norm) return true;
    if (norm === "currency" && gn === "cur") return true;
    if (norm === "market_cap" && gn === "market cap") return true;
    if (norm === "fcf_calc" && gn === "fcf margin") return true;
    if (norm === "free cash flow" && gn === "fcf margin") return true;
    if (norm === "ev_to_ebitda" && gn === "ev/ebitda") return true;
    if (norm === "net_debt" && gn === "net debt") return true;
    if (norm === "diluted_eps" && gn === "eps") return true;
    return false;
  });
}
