import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Card, Chip, Page } from "../components/layout";
import TransactionModal from "../components/portfolio/TransactionModal";
import DecisionJournalModal from "../components/portfolio/DecisionJournalModal";

type PortfolioSummary = {
  holdings_count?: number;
  total_market_value_by_currency?: Record<string, number>;
  currency_note?: string;
  weighted_pillar_avg?: Record<string, number | null>;
  weighted_composite?: number | null;
  sector_concentration?: Array<{ sector: string; weight_pct: number }>;
};

type DividendSummary = {
  trailing_12m_by_currency?: Record<string, number>;
  forward_12m_by_currency?: Record<string, number>;
};

type RebalanceSummary = {
  holdings?: Array<{ company_id: string; ticker?: string | null; weight_pct: number; drift_pct: number; warning?: string | null }>;
};

type HeatmapSummary = {
  heatmap?: Array<{ company_id: string; ticker?: string | null; severity: number; flags?: string[] }>;
};

type JournalSummary = {
  avg_confidence?: number | null;
  count?: number;
  entries?: Array<{ id: string; company_id: string; strategy_tag?: string | null; confidence?: number | null; thesis?: string | null }>;
};

type HoldingRow = {
  account_id: string;
  company_id: string;
  ticker?: string | null;
  quantity: number;
  avg_cost_per_share?: number | null;
  market_price?: number | null;
  market_value?: number | null;
  unrealized_pnl?: number | null;
  currency: string;
};

export default function Portfolio() {
  const [accounts, setAccounts] = useState<Array<{ id: string; name: string; account_type: string; currency: string }>>([]);
  const [activeAccount, setActiveAccount] = useState<string | null>(null);
  const [holdings, setHoldings] = useState<HoldingRow[]>([]);
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [dividends, setDividends] = useState<DividendSummary | null>(null);
  const [rebalance, setRebalance] = useState<RebalanceSummary | null>(null);
  const [heat, setHeat] = useState<HeatmapSummary | null>(null);
  const [journal, setJournal] = useState<JournalSummary | null>(null);
  const [showTxn, setShowTxn] = useState(false);
  const [showJournal, setShowJournal] = useState(false);
  const [newAccountName, setNewAccountName] = useState("");
  const [newAccountType, setNewAccountType] = useState("TFSA");
  const [newAccountCcy, setNewAccountCcy] = useState("CAD");

  const load = async () => {
    const accountsResponse = (await api.portfolioAccounts().catch(() => ({ accounts: [] }))) as { accounts?: Array<{ id: string; name: string; account_type: string; currency: string }> };
    setAccounts(accountsResponse.accounts ?? []);
    const holdingsResponse = (await api.portfolioHoldings(activeAccount ?? undefined).catch(() => ({ holdings: [] }))) as { holdings?: HoldingRow[] };
    setHoldings(holdingsResponse.holdings ?? []);
    setSummary((await api.portfolioSummary(activeAccount ?? undefined).catch(() => null)) as PortfolioSummary | null);
    setDividends((await api.portfolioDividends(activeAccount ?? undefined).catch(() => null)) as DividendSummary | null);
    setRebalance((await api.portfolioRebalance(activeAccount ?? undefined).catch(() => null)) as RebalanceSummary | null);
    setHeat((await api.portfolioHeatmap(activeAccount ?? undefined).catch(() => null)) as HeatmapSummary | null);
    setJournal((await api.journalEntries().catch(() => null)) as JournalSummary | null);
  };

  useEffect(() => { load(); }, [activeAccount]);

  const createAccount = async () => {
    if (!newAccountName.trim()) return;
    await api.createPortfolioAccount({ name: newAccountName.trim(), account_type: newAccountType, currency: newAccountCcy });
    setNewAccountName("");
    load();
  };

  return (
    <Page
      title="Portfolio & Holdings"
      description="Local ledger - TFSA/RRSP/FHSA/Taxable/Paper with currency isolation (CAD vs USD). Holdings, dividends, rebalancing, tax lots, and forensic heatmap."
      actions={
        <div className="flex items-center gap-2">
          <button onClick={() => setShowTxn(true)} className="px-3 py-1.5 rounded bg-accent text-bg-0 text-xs font-mono">Add Transaction</button>
          <button onClick={() => setShowJournal(true)} className="px-3 py-1.5 rounded border border-border text-xs">Journal Buy</button>
        </div>
      }
    >
      <TransactionModal isOpen={showTxn} onClose={() => setShowTxn(false)} accounts={accounts} onCreated={load} />
      <DecisionJournalModal isOpen={showJournal} onClose={() => setShowJournal(false)} onCreated={load} />

      {/* Account filters + creation */}
      <Card padding="md" className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-mono text-[11px] uppercase text-ink-2">Account Filter:</span>
          <button onClick={() => setActiveAccount(null)} className={`px-2.5 py-1 rounded-chip text-xs border ${!activeAccount ? "bg-accent text-bg-0 border-accent" : "bg-bg-0 border-border"}`}>All Accounts</button>
          {accounts.map((a) => (
            <button key={a.id} onClick={() => setActiveAccount(a.id)} className={`px-2.5 py-1 rounded-chip text-xs border ${activeAccount === a.id ? "bg-accent text-bg-0 border-accent" : "bg-bg-0 border-border"}`}>
              {a.name} ({a.account_type} · {a.currency})
            </button>
          ))}
        </div>
        <div className="flex flex-wrap items-end gap-2 border-t border-border pt-3">
          <label className="block">
            <span className="font-mono text-[11px] uppercase text-ink-2">New Account Name</span>
            <input value={newAccountName} onChange={(e) => setNewAccountName(e.target.value)} placeholder="e.g., TFSA - Questrade" className="mt-1 rounded border border-border bg-bg-0 px-2 py-1 text-xs" aria-label="New account name" />
          </label>
          <label className="block">
            <span className="font-mono text-[11px] uppercase text-ink-2">Type</span>
            <select value={newAccountType} onChange={(e) => setNewAccountType(e.target.value)} className="mt-1 rounded border border-border bg-bg-0 px-2 py-1 text-xs" aria-label="Account type">
              <option>TFSA</option><option>RRSP</option><option>FHSA</option><option>Taxable</option><option>Paper</option>
            </select>
          </label>
          <label className="block">
            <span className="font-mono text-[11px] uppercase text-ink-2">Currency</span>
            <select value={newAccountCcy} onChange={(e) => setNewAccountCcy(e.target.value)} className="mt-1 rounded border border-border bg-bg-0 px-2 py-1 text-xs" aria-label="Account currency">
              <option>CAD</option><option>USD</option>
            </select>
          </label>
          <button onClick={createAccount} className="px-3 py-1.5 rounded bg-accent text-bg-0 text-xs font-mono">Create Account</button>
          <span className="text-[11px] text-ink-2">Currency isolation: CAD and USD totals never blended.</span>
        </div>
      </Card>

      {/* Summary */}
      {summary && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <Card title="Holdings Count" padding="md"><span className="font-mono text-2xl font-bold">{summary.holdings_count}</span></Card>
          <Card title="Market Value by Currency" padding="md">
            {Object.entries(summary.total_market_value_by_currency ?? {}).map(([ccy, val]) => (
              <div key={ccy} className="flex justify-between font-mono text-sm"><span>{ccy}</span><span>${Number(val).toLocaleString()}</span></div>
            ))}
            {Object.keys(summary.total_market_value_by_currency ?? {}).length === 0 && <span className="text-xs text-ink-2">No holdings yet - add a transaction.</span>}
            <p className="text-[11px] text-ink-2 mt-1">{summary.currency_note}</p>
          </Card>
          <Card title="Weighted Pillars (Quality/Value/Growth/Risk)" padding="md">
            {summary.weighted_pillar_avg && Object.entries(summary.weighted_pillar_avg as Record<string, number | null>).map(([k, v]) => (
              <div key={k} className="flex justify-between font-mono text-xs"><span className="uppercase">{k}</span><span>{v != null ? String(v) : "Not reported in filing"}</span></div>
            ))}
            <div className="text-xs mt-1">Composite: <strong>{summary.weighted_composite ?? "Not reported in filing"}</strong></div>
          </Card>
        </div>
      )}

      {/* Allocation SVG - sector concentration */}
      {summary?.sector_concentration && summary.sector_concentration.length > 0 && (
        <Card title="Sector Concentration - Pure SVG" subtitle="Allocation by sector (market value)">
          <svg width={520} height={120} viewBox="0 0 520 120" role="img" aria-label="Sector concentration bar chart" className="w-full h-auto">
            {summary.sector_concentration.slice(0, 6).map((sectorEntry, i: number) => {
              const w = (sectorEntry.weight_pct / 100) * 480;
              return (
                <g key={sectorEntry.sector}>
                  <text x={10} y={16 + i * 18} fontSize={10} fill="var(--ink-1)" fontFamily="IBM Plex Mono">{sectorEntry.sector.slice(0, 18)}</text>
                  <rect x={140} y={8 + i * 18} width={w} height={10} rx={3} fill="var(--accent)" />
                  <text x={145 + w} y={16 + i * 18} fontSize={9} fill="var(--ink-2)" fontFamily="IBM Plex Mono">{sectorEntry.weight_pct}%</text>
                </g>
              );
            })}
          </svg>
        </Card>
      )}

      {/* Holdings table */}
      <Card title="Holdings" subtitle="Average cost, market value, unrealized P&L - currency-segregated" padding="none">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-border text-left font-mono text-[10px] uppercase text-ink-2">
                <th className="px-3 py-2">Company</th><th className="px-3 py-2">Qty</th><th className="px-3 py-2 text-right">Avg Cost</th><th className="px-3 py-2 text-right">Price</th><th className="px-3 py-2 text-right">Market Value</th><th className="px-3 py-2 text-right">Unrealized</th><th className="px-3 py-2">Currency</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {holdings.map((holding) => (
                <tr key={`${holding.account_id}-${holding.company_id}`}>
                  <td className="px-3 py-2 font-mono">{holding.ticker ?? holding.company_id}</td>
                  <td className="px-3 py-2">{holding.quantity}</td>
                  <td className="px-3 py-2 text-right font-mono">${holding.avg_cost_per_share ?? "0.00"}</td>
                  <td className="px-3 py-2 text-right font-mono">{holding.market_price ?? "Not reported in filing"}</td>
                  <td className="px-3 py-2 text-right font-mono">{holding.market_value != null ? `$${holding.market_value.toLocaleString()}` : "0.00"}</td>
                  <td className={`px-3 py-2 text-right font-mono ${holding.unrealized_pnl != null && holding.unrealized_pnl < 0 ? "text-neg" : "text-pos"}`}>{holding.unrealized_pnl ?? "0.00"}</td>
                  <td className="px-3 py-2"><Chip tone={holding.currency === "USD" ? "info" : "warning"} size="sm">{holding.currency}</Chip></td>
                </tr>
              ))}
              {holdings.length === 0 && <tr><td colSpan={7} className="px-3 py-6 text-center text-ink-2">No holdings - add a Buy transaction.</td></tr>}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Dividends / Rebalance / Heatmap */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card title="Dividend Income Planner" subtitle="Trailing 12m vs forward 12m by currency">
          {dividends ? (
            <div className="space-y-1 font-mono text-xs">
              <div>Trailing: {Object.entries(dividends.trailing_12m_by_currency ?? {}).map(([k, v]) => `${k}: $${Number(v).toFixed(2)}`).join(" · ") || "0.00"}</div>
              <div>Forward: {Object.entries(dividends.forward_12m_by_currency ?? {}).map(([k, v]) => `${k}: $${Number(v).toFixed(2)}`).join(" · ") || "0.00"}</div>
            </div>
          ) : <span className="text-xs text-ink-2">Loading…</span>}
        </Card>

        <Card title="Position Sizing & Rebalancing" subtitle="Target equal weight, drift >5pp, max >25% flagged">
          {rebalance ? (
            <div className="space-y-1 text-xs">
              {rebalance.holdings?.slice(0, 4).map((rebalanceEntry) => (
                <div key={rebalanceEntry.company_id} className="flex justify-between font-mono">
                  <span>{rebalanceEntry.ticker ?? rebalanceEntry.company_id}</span>
                  <span className={rebalanceEntry.warning ? "text-warn" : "text-ink-1"}>{rebalanceEntry.weight_pct}% (drift {rebalanceEntry.drift_pct}%) {rebalanceEntry.warning ? `· ${rebalanceEntry.warning}` : ""}</span>
                </div>
              ))}
              {(!rebalance.holdings || rebalance.holdings.length === 0) && <span className="text-ink-2">No holdings</span>}
            </div>
          ) : <span className="text-xs text-ink-2">Loading…</span>}
        </Card>

        <Card title="Forensic Heatmap - Holdings" subtitle="Distress & red-flag exposure">
          {heat ? (
            <div className="space-y-1 text-xs font-mono">
              {heat.heatmap?.slice(0, 4).map((heatEntry) => (
                <div key={heatEntry.company_id} className="flex justify-between">
                  <span>{heatEntry.ticker ?? heatEntry.company_id}</span>
                  <span className={heatEntry.severity > 20 ? "text-neg" : heatEntry.severity > 10 ? "text-warn" : "text-pos"}>Severity {heatEntry.severity} · {heatEntry.flags?.join(", ") || "clean"}</span>
                </div>
              ))}
              {(!heat.heatmap || heat.heatmap.length === 0) && <span className="text-ink-2">No forensic flags on holdings</span>}
            </div>
          ) : <span className="text-xs text-ink-2">Loading…</span>}
        </Card>
      </div>

      {/* Journal calibration */}
      {journal && (
        <Card title="Decision Journal - Calibration" subtitle="Confidence vs theses and current composite">
          <div className="space-y-1 text-xs">
            <div>Avg confidence: <strong>{journal.avg_confidence ?? "Not reported in filing"}</strong> · Entries: {journal.count}</div>
            {journal.entries?.slice(0, 3).map((journalEntry) => (
              <div key={journalEntry.id} className="border-t border-border pt-1 flex justify-between">
                <span className="font-mono">{journalEntry.company_id} · {journalEntry.strategy_tag} · conf {journalEntry.confidence}</span>
                <span className="text-ink-2">{(journalEntry.thesis ?? "").slice(0, 40)}…</span>
              </div>
            ))}
          </div>
        </Card>
      )}

      <p className="text-[11px] font-mono text-ink-2 border-t border-border pt-2">Personal research software, not investment advice. Portfolio tracking and alerts run locally.</p>
    </Page>
  );
}