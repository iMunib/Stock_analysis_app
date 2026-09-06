export const CONSOLIDATED_MAP: Record<string, string> = {
  Software: "Enterprise Software & Cloud",
  Networking: "Enterprise Software & Cloud",
  Internet_Platforms: "Enterprise Software & Cloud",
  Tech: "Enterprise Software & Cloud",
  Semiconductors_Components: "Semiconductors & Hardware",
  Streaming_Entertainment: "Media & Entertainment",
  Telecom: "Media & Entertainment",
  Comm_Services: "Media & Entertainment",
  Retail: "Consumer Commerce & Retail",
  Discount_Stores: "Consumer Commerce & Retail",
  Consumer_Cyclical: "Consumer Commerce & Retail",
  Fast_Food_Restaurants: "Consumer Commerce & Retail",
  Consumer_Goods: "Consumer Staples & Brands",
  Consumer_Defensive: "Consumer Staples & Brands",
  Airlines: "Industrials & Logistics",
  Railroads: "Industrials & Logistics",
  Industrials: "Industrials & Logistics",
  Autos: "Industrials & Logistics",
  Pipelines_Midstream: "Energy & Resources",
  Oil_Gas_Producers: "Energy & Resources",
  Credit_Services: "Diversified Financials",
  Financials: "Diversified Financials",
  Pharma: "Pharma & Biotech",
  Biotech: "Pharma & Biotech",
  Materials: "Materials & Chemicals",
};

export function consolidateSheet(sheet: string | null | undefined): string {
  if (!sheet) return "Unknown";
  if (Object.values(CONSOLIDATED_MAP).includes(sheet)) return sheet;
  return CONSOLIDATED_MAP[sheet] ?? sheet;
}

export function prettySheet(sheet: string): string {
  return consolidateSheet(sheet).replace(/_/g, " ");
}
