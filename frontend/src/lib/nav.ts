/** App-shell navigation + sector card identity helpers (pure, testable). */

export interface NavItem {
  label: string;
  to: string;
}

export function navItems(hasJobs: boolean): NavItem[] {
  const items: NavItem[] = [
    { label: "Desk", to: "/" },
    { label: "Sectors", to: "/sectors" },
    { label: "Compare", to: "/compare" },
  ];
  if (hasJobs) items.push({ label: "Jobs", to: "/jobs" });
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
