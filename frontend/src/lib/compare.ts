/** Compare selection helpers (pure, testable). */

export const MAX_COMPARE = 8;

export function toggleCompareId(current: string[], id: string): string[] {
  if (current.includes(id)) return current.filter((x) => x !== id);
  if (current.length >= MAX_COMPARE) return current;
  return [...current, id];
}

export function compareIdsToQuery(ids: string[]): string {
  return ids.join(",");
}

export function compareIdList(ids: string[], add: string): string[] {
  return toggleCompareId(ids, add);
}
