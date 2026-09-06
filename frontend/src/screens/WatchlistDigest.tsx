import Watchlist from "./Watchlist";

/**
 * WatchlistDigest – alias for Watchlist / Morning Brief.
 * Route: /digest (spec requirement: accessible via route /digest and navigation)
 * This re-exports the full Watchlist screen which embeds the MorningBrief
 * component (1-page fundamental deltas, re-ratings, post-earnings actuals,
 * SEDAR+/EDGAR routing). Kept as a dedicated file to satisfy the
 * Phase 1 Wave 2 execution protocol's file-structure contract.
 */
export default function WatchlistDigest() {
  return <Watchlist />;
}
