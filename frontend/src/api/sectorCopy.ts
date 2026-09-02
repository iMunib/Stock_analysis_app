/** Static 2-sentence blurbs per sector sheet (not LLM). Unknown sheet → generic. */

const SECTOR_COPY: Record<string, string> = {
  Banks: "Banks take deposits and lend them out, earning the spread between interest paid and received. Watch capital (CET1), net interest margin, and credit losses rather than revenue or free cash flow.",
  Insurance: "Insurers collect premiums today and pay claims later, investing the float in between. Underwriting discipline and reserve adequacy matter more than headline revenue.",
  Credit_Services: "Credit providers earn interest and fees on consumer or commercial lending. Credit quality of the loan book drives long-term results.",
  Software: "Software firms sell licenses or subscriptions with high gross margins and low capital needs. Look for durable revenue growth and cash generation.",
  Semiconductors: "Chipmakers design or fabricate semiconductors on cyclical capital-intensive cycles. Demand timing and utilization swings matter.",
  Airlines: "Airlines fly passengers and cargo with thin margins, high fixed costs, and fuel exposure. Balance-sheet strength decides who survives downturns.",
  Oil_Gas_Producers: "Producers extract and sell oil and gas, with profits driven by commodity prices and production costs. Reserves and capital discipline are key.",
  Retail: "Retailers buy and resell goods at scale on thin margins. Inventory turns and same-store growth separate winners.",
  Pharma: "Pharmaceutical companies develop and patent drugs. Patent cliffs and pipeline success dominate the economics.",
  Autos: "Automakers manufacture vehicles with cyclical demand, heavy capital spending, and labor intensity. Watch pricing power and margins per unit.",
  Utilities: "Utilities deliver regulated electricity, gas, or water with stable cash flows and heavy debt loads. Interest rates and regulation drive returns.",
  Real_Estate: "Real estate firms own or operate property earning rent. REIT metrics (FFO/AFFO) matter more than classic EPS.",
  Materials: "Materials firms produce chemicals, metals, and construction inputs tied to industrial cycles. Cost position is the moat.",
  Industrials: "Industrial companies make machinery, equipment, and services for other businesses. Backlogs and margins through cycles tell the story.",
  Media: "Media companies produce content and advertising reach. Streaming transitions reshaped their economics.",
  Consumer_Staples: "Staples sell everyday necessities with resilient demand and modest growth. Pricing power and distribution are the moat.",
  Healthcare: "Healthcare spans providers, devices, and services with demographic demand tailwinds. Regulation and reimbursement rates shape profits.",
  Technology: "Technology firms build hardware, IT services, and platforms with scale economics. Innovation cadence and margins drive outcomes.",
  Financials: "Financial firms intermediate money: lending, investing, insurance, and payments. Leverage and trust are the twin risks.",
  Energy: "Energy companies produce and distribute power and fuels. Commodity cycles and energy transition spending dominate.",
  Telecom: "Telecoms own networks selling connectivity as a subscription. Capital intensity and spectrum costs are the hurdles.",
};

const GENERIC =
  "This group groups companies that share a business model or end market. Compare them on the same unitless metrics; money stays in each company's own currency.";

export function sectorBlurb(sheet: string): string {
  const key = sheet.replace(/^GICS_/, "").replace(/_/g, " ").trim();
  const direct = SECTOR_COPY[sheet] ?? SECTOR_COPY[key];
  if (direct) return direct;
  for (const k of Object.keys(SECTOR_COPY)) {
    if (k.toLowerCase().replace(/_/g, " ") === key.toLowerCase()) return SECTOR_COPY[k];
  }
  return GENERIC;
}
