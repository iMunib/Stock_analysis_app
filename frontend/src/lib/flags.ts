/** Deterministic pill flags for the dossier verdict strip (max 6, 2-3 words). */
import type { DossierOut } from "../api/types";

export interface Flag {
  key: string;
  label: string;
  tone: "good" | "mid" | "bad" | "info";
}

const FIN_CUSTOM = ["banks", "insurance", "credit_services"];

export function dossierFlags(d: DossierOut): Flag[] {
  const flags: Flag[] = [];
  const p = d.score?.pillars;
  const signal = d.score?.signal;

  if (p) {
    if (p.quality != null && p.quality >= 7) flags.push({ key: "q_hi", label: "Quality", tone: "good" });
    if (p.quality != null && p.quality <= 3) flags.push({ key: "q_lo", label: "Weak quality", tone: "bad" });
    if (p.value != null && p.value >= 7) flags.push({ key: "v_hi", label: "Cheaper vs peers", tone: "good" });
    if (p.value != null && p.value <= 3) flags.push({ key: "v_lo", label: "Expensive vs peers", tone: "bad" });
    if (p.growth != null && p.growth >= 7) flags.push({ key: "g_hi", label: "Growth history", tone: "good" });
    if (p.growth == null) flags.push({ key: "g_null", label: "Not enough history", tone: "mid" }); // amber, never red
    if (p.risk != null && p.risk >= 7) flags.push({ key: "r_hi", label: "Lower risk", tone: "good" });
    if (p.risk != null && p.risk <= 3) flags.push({ key: "r_lo", label: "Higher risk", tone: "bad" });
  }
  if (signal === "avoid") flags.push({ key: "sig", label: "Avoid", tone: "bad" });
  if (d.halal?.status === "not_halal")
    flags.push({ key: "halal", label: "Activity/ratio flag - not a ruling", tone: "mid" });

  const toneOrder: Record<Flag["tone"], number> = { bad: 0, good: 1, mid: 2, info: 3 };
  return flags.sort((a, b) => toneOrder[a.tone] - toneOrder[b.tone]).slice(0, 6);
}

export function isFinancialSector(d: DossierOut): boolean {
  return (
    (d.identity.gics_sector ?? "").toLowerCase() === "financials" ||
    FIN_CUSTOM.includes((d.identity.custom_industry_sheet ?? "").toLowerCase())
  );
}

/** Provenance sentence: math, not AI. */
export function provenanceSentence(d: DossierOut): string {
  if (!d.score) return "No score computed yet.";
  return "Score is math (v1), not AI. Quality 30% · Value 25% · Growth 25% · Risk 20%.";
}