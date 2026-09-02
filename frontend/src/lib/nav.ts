/** App-shell navigation + sector card identity helpers (pure, testable). */

export interface NavItem {
  label: string;
  to: string;
}

export function navItems(hasJobs: boolean): NavItem[] {
  // Stage C: Jobs is always in the nav if the route exists (the page itself shows a
  // setup hint if the API is unreachable). hasJobs keeps back-compat for older callers.
  const items: NavItem[] = [
    { label: "Desk", to: "/" },
    { label: "Screen", to: "/screen" },
    { label: "Sectors", to: "/sectors" },
    { label: "Compare", to: "/compare" },
    { label: "Jobs", to: "/jobs" },
    { label: "Learn", to: "/learn" },
  ];
  void hasJobs;
  return items;
}

export type SectorGroup = "custom" | "gics";

export function sectorCardKey(group: SectorGroup, name: string): string {
  return `${group}:${name}`;
}

/** GICS sector sheets are addressed as GICS_<Sector> on the API. */
export function gicsSheetParam(name: string): string {
  return `GICS_${name}`;
}
