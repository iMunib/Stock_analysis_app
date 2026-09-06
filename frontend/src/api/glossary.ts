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
  // --- Penman Reformulated Statements ---
  {
    term: "RNOA",
    short: "Return on Net Operating Assets - operating profit divided by net operating assets.",
    why: "Isolates operating performance from financing decisions, neutralizing buyback/leverage distortion.",
    how_to_read: "Positive RNOA above cost of capital signals durable operating efficiency. Blank for banks.",
  },
  {
    term: "FLEV",
    short: "Financial leverage - net financial obligations divided by common equity.",
    why: "Measures how much of a company's return is borrowed from creditors vs. earned operationally.",
    how_to_read: "FLEV > 3 is high leverage distortion. Negative FLEV means net cash position.",
  },
  {
    term: "NOA",
    short: "Net Operating Assets - total assets minus cash minus operating liabilities.",
    why: "The Penman reformulation base: the assets the business genuinely needs to operate.",
    how_to_read: "Rising NOA vs. NOPAT can signal asset inefficiency or aggressive growth.",
  },
  {
    term: "NFO",
    short: "Net Financial Obligations - total debt minus cash equivalents.",
    why: "True net debt burden excluding operating payables.",
    how_to_read: "Negative NFO means net cash (positive to creditors). Large NFO relative to NOA is risky.",
  },
  {
    term: "NOPAT",
    short: "Net Operating Profit After Tax - operating income after a blended tax estimate.",
    why: "Cash-equivalent operating earnings before financing costs.",
    how_to_read: "The numerator of RNOA. Should grow with revenue.",
  },
  {
    term: "NBC",
    short: "Net Borrowing Cost - after-tax cost of net debt financing.",
    why: "Spread RNOA – NBC determines whether leverage helps or hurts shareholders.",
    how_to_read: "RNOA > NBC is good; leverage amplifies returns. RNOA < NBC means debt destroys value.",
  },
  {
    term: "Penman DuPont",
    short: "ROE = RNOA + FLEV × (RNOA − NBC) - splits return into operating and financing components.",
    why: "Traditional DuPont mixes leverage and margin; Penman separates them clearly.",
    how_to_read: "If ROE >> RNOA, returns are leverage-driven. Prefer RNOA > 10% for organic quality.",
  },
  // --- Graham / Malkiel ---
  {
    term: "Graham Number",
    short: "√(22.5 × EPS × BVPS) - Benjamin Graham's intrinsic value formula.",
    why: "Quick-and-dirty floor value: assumes no more than 15x PE and 1.5x PB.",
    how_to_read: "If price > Graham Number the stock is above Graham's fair value floor.",
  },
  {
    term: "NCAV",
    short: "Net Current Asset Value - current assets minus total liabilities.",
    why: "Graham's deep-value screen: company worth more dead than alive if NCAV > price.",
    how_to_read: "NCAV/share > price per share is a 'net-net' - extremely rare and often distressed.",
  },
  {
    term: "NNWC",
    short: "Net-Net Working Capital - NCAV with haircuts: 0.75× receivables, 0.5× inventory.",
    why: "More conservative NCAV that discounts less liquid current assets.",
    how_to_read: "NNWC/share > price is the most conservative Graham net-net screen.",
  },
  {
    term: "Margin of Safety",
    short: "% discount of current price to intrinsic value (e.g., Graham Number or DCF).",
    why: "Graham's central principle: buy cheap enough that errors of analysis still produce profits.",
    how_to_read: "Negative MoS means price exceeds the value estimate; positive means upside cushion.",
  },
  {
    term: "FCF Growth Hurdle",
    short: "Whether FCF CAGR exceeds the 8.0% index rate used as a Malkiel benchmark.",
    why: "Malkiel: an equity is attractive only if its long-run FCF growth beats the market alternative.",
    how_to_read: "Green = beats 8% hurdle; red = below. Not advice; historical growth may not persist.",
  },
  // --- Forensic / Schilit ---
  {
    term: "EQR",
    short: "Earnings Quality Rating (0–100) - composite forensic score. Higher is cleaner.",
    why: "Aggregates multiple manipulation risk signals from the Schilit forensic framework.",
    how_to_read: "EQR > 70 is clean; 50–70 is mixed; < 50 warrants forensic scrutiny.",
  },
  {
    term: "DSO Surge",
    short: "Days Sales Outstanding rising faster than revenue - possible channel stuffing.",
    why: "Inflated receivables can front-load reported revenue before cash is collected.",
    how_to_read: "A yellow flag on its own; combined with slowing cash conversion it is serious.",
  },
  {
    term: "CFO Decoupled",
    short: "Operating cash flow growing much slower than reported net income.",
    why: "Accrual-heavy earnings without matching cash are a textbook Schilit signal.",
    how_to_read: "Isolated year: normal. Multi-year pattern: investigate accrual quality.",
  },
  {
    term: "Inventory Buildup",
    short: "Inventory growing significantly faster than revenue - possible demand weakness.",
    why: "Rising inventory can mask demand deterioration or production inefficiency.",
    how_to_read: "Relevant for manufacturers and retailers; less meaningful for pure-service businesses.",
  },
  {
    term: "AQI Expense Cap",
    short: "Asset Quality Index flag - rising asset base vs. revenue may signal expense capitalization.",
    why: "Companies can inflate assets (and suppress expenses) by capitalizing costs that should be expensed.",
    how_to_read: "A red flag alongside weak CFO and high accruals suggests earnings manipulation risk.",
  },
  {
    term: "Accruals",
    short: "Net income minus operating cash flow - the portion of earnings not yet received in cash.",
    why: "High accruals often precede earnings disappointments (Sloan anomaly).",
    how_to_read: "Positive accruals mean earnings exceed cash. A small amount is normal; large sustained accruals are a caution.",
  },
  // --- Valuation / DCF ---
  {
    term: "Reverse DCF",
    short: "What FCF growth rate the current price implicitly assumes over 10 years.",
    why: "Shows what you must believe to justify today's price - not a prediction of growth.",
    how_to_read: "High implied growth (>20%) requires extraordinary confidence. It is not a target price.",
  },
  {
    term: "WACC",
    short: "Weighted Average Cost of Capital - the discount rate used in the reverse DCF.",
    why: "WACC is a conservative baseline; actual hurdle rates vary by business risk.",
    how_to_read: "App uses 9% default. Lower WACC inflates present value; higher deflates it.",
  },
  {
    term: "Terminal Growth",
    short: "Long-run FCF growth rate assumed beyond the 10-year explicit period.",
    why: "Terminal value can dominate DCF outputs; small changes have large effects.",
    how_to_read: "App uses 2.5% default. Debate the terminal rate before debating the price target.",
  },
  {
    term: "FCF",
    short: "Free Cash Flow - operating cash flow minus capital expenditures.",
    why: "The real cash available to pay down debt, buy back shares, or pay dividends.",
    how_to_read: "Positive and growing FCF sustains buybacks and dividends without new debt.",
  },
  {
    term: "EV",
    short: "Enterprise Value - market cap + net debt + minority interests.",
    why: "Debt-inclusive price; compares the cost of buying the whole business.",
    how_to_read: "Use EV multiples (EV/EBITDA) when comparing businesses with different debt levels.",
  },
  {
    term: "PEG",
    short: "PE ratio divided by expected earnings growth rate.",
    why: "Adjusts the PE for growth: PEG < 1 can indicate relative value for fast-growers.",
    how_to_read: "Blank or unreliable when PE < 0 or growth is undefined. Rule of thumb only.",
  },
  // --- Market / Risk ---
  {
    term: "Beta",
    short: "Correlation of the stock's price moves vs. the S&P 500 market.",
    why: "Measures systematic market sensitivity; does not predict idiosyncratic risk.",
    how_to_read: "Beta > 1 means more volatile than the market. Beta < 1 means more stable.",
  },
  {
    term: "Short Ratio",
    short: "Days to cover short interest - shares short divided by average daily volume.",
    why: "High short ratios can indicate either deserved skepticism or squeeze potential.",
    how_to_read: "Above 10 days is high. It is neither bullish nor bearish alone; research the reason.",
  },
  {
    term: "52w High/Low",
    short: "Highest and lowest closing prices over the past 52 weeks.",
    why: "Establishes the recent price range context.",
    how_to_read: "Near 52w high can mean momentum; near 52w low can mean distress or value. Context matters.",
  },
  {
    term: "50d / 200d MA",
    short: "50-day and 200-day moving average prices.",
    why: "Widely watched technical levels; price vs. MA is used as a momentum filter.",
    how_to_read: "Below 200d MA means the stock has underperformed its own 10-month average.",
  },
  {
    term: "Institutional %",
    short: "Percentage of shares owned by funds, ETFs, and institutional investors.",
    why: "High institutional ownership means professional scrutiny; low means less coverage.",
    how_to_read: "Neither good nor bad alone; very low can mean undiscovered, very high can mean crowded.",
  },
  // --- Bank-specific ---
  {
    term: "CET1",
    short: "Common Equity Tier 1 ratio - core capital buffer as a % of risk-weighted assets.",
    why: "Regulatory minimum capital for banks; main measure of bank solvency.",
    how_to_read: "Above 12% is well-capitalized. Below regulatory minimum is a crisis signal.",
  },
  {
    term: "NIM",
    short: "Net Interest Margin - net interest income divided by earning assets.",
    why: "Primary profitability driver for banks; shows spread between lending and funding costs.",
    how_to_read: "Above 3% is healthy for most North American banks; rising NIM favors profitability.",
  },
  {
    term: "Efficiency Ratio",
    short: "Non-interest expense divided by revenue. For banks: lower is more efficient.",
    why: "Cost control metric - opposite sign to other margins (lower = better for banks).",
    how_to_read: "Below 55% is excellent. Above 65% signals cost pressure. Blank for non-financials.",
  },
  {
    term: "ROAA",
    short: "Return on Average Assets - net income over average total assets.",
    why: "Cross-bank profitability metric that adjusts for balance sheet size differences.",
    how_to_read: "Above 1% for large banks is healthy; below 0.5% is weak. Blank for non-financials.",
  },
  // --- Confidence / Provenance ---
  {
    term: "Data Confidence",
    short: "Freshness and completeness rating of the underlying data: High / Medium / Low / Insufficient.",
    why: "Stale or sparse data degrades score reliability.",
    how_to_read: "High: price ≤1d, filings ≤15mo, 4/4 pillars. Medium: some gaps. Low: act with caution.",
  },
  {
    term: "Provenance",
    short: "Where a data point came from and when it was last verified.",
    why: "Distinguishes seed workbook data from live provider data.",
    how_to_read: "'Seed' rows are the owner-verified workbook baseline. Provider rows are live-fetched.",
  },
  {
    term: "Halal Flag",
    short: "AAOIFI-style screening result: Compliant / Non-Compliant / Doubtful / Unknown.",
    why: "Informational only - not a religious ruling. Based on debt ratios and business activity.",
    how_to_read: "Non-compliant may include banks, insurers, and highly-leveraged firms. Consult a scholar.",
  },
  {
    term: "Anti-FOMO",
    short: "Amber warning banner triggered when PE or EV exceeds 2σ above its 5-year average.",
    why: "Behavioral guardrail: extreme multiples often coincide with peak sentiment, not peak value.",
    how_to_read: "An amber banner is not a sell signal; it is a reminder to stress-test the thesis.",
  },
  {
    term: "Safety Verdict",
    short: "60-second summary: Moat pass/fail · Solvency pass/fail · Valuation pass/fail.",
    why: "Distils the dossier into three yes/no questions a new investor can check in one minute.",
    how_to_read: "All three green = investigates further. Any red = understand why before proceeding.",
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
    if (norm === "fcf" && gn === "fcf") return true;
    if (norm === "rnoa" && gn === "rnoa") return true;
    if (norm === "flev" && gn === "flev") return true;
    if (norm === "noa" && gn === "noa") return true;
    if (norm === "nfo" && gn === "nfo") return true;
    if (norm === "eqr" && gn === "eqr") return true;
    if (norm === "graham_number" && gn === "graham number") return true;
    if (norm === "cet1_ratio" && gn === "cet1") return true;
    if (norm === "efficiency_ratio" && gn === "efficiency ratio") return true;
    if (norm === "nim_fy2025" && gn === "nim") return true;
    if (norm === "beta" && gn === "beta") return true;
    if (norm === "reverse_dcf" && gn === "reverse dcf") return true;
    return false;
  });
}