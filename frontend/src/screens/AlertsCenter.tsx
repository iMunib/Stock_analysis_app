import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Card, Page, Chip } from "../components/layout";

export default function AlertsCenter() {
  const [rules, setRules] = useState<unknown[]>([]);
  const [events, setEvents] = useState<unknown[]>([]);
  const [calendar, setCalendar] = useState<unknown[]>([]);
  const [heartbeat, setHeartbeat] = useState<Record<string, unknown> | null>(null);
  const [newRuleType, setNewRuleType] = useState("distress");
  const [newCompany, setNewCompany] = useState("US:AAPL:US");
  const [newFair, setNewFair] = useState("200");

  const load = async () => {
    const rulesResponse = (await api.alertRules().catch(() => ({ rules: [] }))) as { rules?: unknown[] };
    setRules((rulesResponse.rules as unknown[]) ?? []);
    const eventsResponse = (await api.alertsEvents().catch(() => ({ events: [] }))) as { events?: unknown[] };
    setEvents((eventsResponse.events as unknown[]) ?? []);
    const calendarResponse = (await api.alertsCalendar().catch(() => ({ items: [] }))) as { items?: unknown[] };
    setCalendar((calendarResponse.items as unknown[]) ?? []);
    setHeartbeat((await api.alertsHeartbeat().catch(() => null)) as Record<string, unknown> | null);
  };

  useEffect(() => { load(); }, []);

  const createRule = async () => {
    const params: Record<string, unknown> = {};
    if (newRuleType === "price_below_fair_value") params.fair_value = parseFloat(newFair);
    params.min_change_pct = 2;
    params.severity = "elevated";
    await api.createAlertRule({ company_id: newCompany, rule_type: newRuleType, params });
    load();
  };

  const evaluate = async () => {
    const response = (await api.evaluateAlerts().catch(() => ({ events: [] }))) as { events?: unknown[] };
    setEvents((response.events as unknown[]) ?? []);
  };

  return (
    <Page
      title="Alerts Center"
      description="Local monitoring daemon - price/score/filing triggers, calendar, heartbeat. Quiet hours and de-noising supported."
      actions={
        <div className="flex items-center gap-2">
          <button onClick={evaluate} className="px-3 py-1.5 rounded bg-accent text-bg-0 text-xs font-mono">Evaluate Now</button>
          <span className="text-[11px] font-mono text-ink-2">Local - no cloud push</span>
        </div>
      }
    >
      {/* Create rule */}
      <Card padding="md" className="space-y-3">
        <h3 className="font-heading text-sm font-semibold text-ink-0">Create Alert Rule (Local)</h3>
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-2">
          <label className="block">
            <span className="font-mono text-[11px] uppercase text-ink-2">Company ID</span>
            <input value={newCompany} onChange={(e) => setNewCompany(e.target.value)} className="mt-1 w-full rounded border border-border bg-bg-0 px-2 py-1 text-xs font-mono" aria-label="Alert company ID" />
          </label>
          <label className="block">
            <span className="font-mono text-[11px] uppercase text-ink-2">Rule Type</span>
            <select value={newRuleType} onChange={(e) => setNewRuleType(e.target.value)} className="mt-1 w-full rounded border border-border bg-bg-0 px-2 py-1 text-xs" aria-label="Rule type">
              <option value="distress">distress (Altman Z)</option>
              <option value="forensic">forensic (Beneish)</option>
              <option value="price_below_fair_value">price_below_fair_value</option>
              <option value="earnings">earnings (next 7d)</option>
              <option value="dividend">dividend (ex-div 7d)</option>
            </select>
          </label>
          <label className="block">
            <span className="font-mono text-[11px] uppercase text-ink-2">Fair Value (for price trigger)</span>
            <input value={newFair} onChange={(e) => setNewFair(e.target.value)} className="mt-1 w-full rounded border border-border bg-bg-0 px-2 py-1 text-xs font-mono" aria-label="Fair value" />
          </label>
          <div className="flex items-end">
            <button onClick={createRule} className="w-full px-3 py-1.5 rounded bg-accent text-bg-0 text-xs font-mono">Create Rule</button>
          </div>
        </div>
        <p className="text-[11px] font-mono text-ink-2">De-noising: min 2% change; quiet hours respected locally. Rules stored in SQLite `alert_rules`.</p>
      </Card>

      {/* Active rules + events */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card title="Active Rules" subtitle={`${rules.length} rules`} padding="md">
          <div className="space-y-1 text-xs max-h-64 overflow-y-auto">
            {rules.map((rule) => {
              const typedRule = rule as Record<string, unknown>;
              return (
                <div key={String(typedRule.id)} className="flex justify-between border-b border-border py-1">
                  <span className="font-mono">{(typedRule.company_id as string) ?? "global"} · {String(typedRule.rule_type)}</span>
                  <span className={`px-1.5 py-0.5 rounded text-[10px] ${typedRule.enabled ? "bg-pos-weak text-pos" : "bg-bg-2 text-ink-2"}`}>{typedRule.enabled ? "enabled" : "disabled"}</span>
                </div>
              );
            })}
            {rules.length === 0 && <span className="text-ink-2">No rules - create one above.</span>}
          </div>
        </Card>

        <Card title="Triggered Events (Local Evaluation)" subtitle="Distress, forensic, intrinsic value triggers" padding="md">
          <div className="space-y-1 text-xs max-h-64 overflow-y-auto">
            {events.map((event) => {
              const typedEvent = event as Record<string, unknown>;
              return (
                <div key={String(typedEvent.id)} className="flex justify-between border-b border-border py-1">
                  <span className="font-mono">{(typedEvent.ticker as string) ?? (typedEvent.company_id as string)} · {String(typedEvent.rule_type)}</span>
                  <span className="flex items-center gap-1">
                    <Chip tone={typedEvent.severity === "critical" ? "negative" : typedEvent.severity === "elevated" ? "warning" : "info"} size="sm">{String(typedEvent.severity)}</Chip>
                    <span className="text-ink-2 truncate max-w-[160px]">{String(typedEvent.detail ?? "")}</span>
                  </span>
                </div>
              );
            })}
            {events.length === 0 && <span className="text-ink-2">No triggers - daemon evaluated clean.</span>}
          </div>
        </Card>
      </div>

      {/* Calendar timeline */}
      <Card title="Unified Calendar - Earnings / Ex-Dividend / Filings (30d)" subtitle="SEDAR+/EDGAR milestones" padding="md">
          <div className="space-y-1 text-xs max-h-48 overflow-y-auto">
            {calendar.map((entry, i: number) => {
              const typedEntry = entry as Record<string, unknown>;
              return (
                <div key={`${String(typedEntry.company_id)}-${String(typedEntry.event_date)}-${i}`} className="flex justify-between border-b border-border py-1 font-mono">
                  <span>{String(typedEntry.company_id)} · {String(typedEntry.event_type)}</span>
                  <span className="text-ink-1">{String(typedEntry.event_date)} ({String(typedEntry.days_ahead)}d)</span>
                </div>
              );
            })}
          {calendar.length === 0 && <span className="text-ink-2">No upcoming events in next 30 days.</span>}
        </div>
      </Card>

      {/* Heartbeat */}
      {heartbeat && (
        <Card title="System Heartbeat - Daemon Operational" subtitle="Fail-safe weekly status proving monitoring is alive">
          <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
            <Chip tone="positive" size="sm">operational</Chip>
            <span>Daemon: {String((heartbeat as Record<string, unknown>).daemon ?? "")}</span>
            <span>Last evaluated: {String((heartbeat as Record<string, unknown>).last_evaluated_at ?? "").slice(0, 19)}</span>
            <span className="text-ink-2">{String((heartbeat as Record<string, unknown>).uptime ?? "")}</span>
          </div>
        </Card>
      )}

      <p className="text-[11px] font-mono text-ink-2 border-t border-border pt-2">Personal research software, not investment advice. Portfolio tracking and alerts run locally.</p>
    </Page>
  );
}