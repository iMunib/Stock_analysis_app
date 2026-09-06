import { useMemo, useState } from "react";
import { Card } from "../layout";
import { money } from "../../lib/format";

function computeToyDcf(fcfStr: string, gStr: string, waccStr: string, yearsStr: string) {
  const fcf = parseFloat(fcfStr);
  const g = parseFloat(gStr) / 100;
  const wacc = parseFloat(waccStr) / 100;
  const years = parseInt(yearsStr, 10);

  if (isNaN(fcf) || isNaN(g) || isNaN(wacc) || isNaN(years) || years <= 0 || wacc <= 0.02) {
    return null;
  }

  let pvSum = 0;
  let currentFcf = fcf;
  for (let i = 1; i <= years; i++) {
    currentFcf *= 1 + g;
    pvSum += currentFcf / Math.pow(1 + wacc, i);
  }
  const terminalVal = (currentFcf * 1.02) / (wacc - 0.02);
  const pvTerminal = terminalVal / Math.pow(1 + wacc, years);
  const enterpriseValue = pvSum + pvTerminal;

  return { pvSum, pvTerminal, enterpriseValue };
}

export default function ToyDcfCard({
  isBank,
  latestFcf,
  currency,
}: {
  isBank: boolean;
  latestFcf?: number | null;
  currency: string;
}) {
  const [fcf, setFcf] = useState("");
  const [growth, setGrowth] = useState("");
  const [wacc, setWacc] = useState("");
  const [years, setYears] = useState("5");

  const result = useMemo(() => computeToyDcf(fcf, growth, wacc, years), [fcf, growth, wacc, years]);

  return (
    <Card
      title="Toy DCF Calculator"
      subtitle="Output is not stored as truth. Default empty. Exploratory scratchpad only."
    >
      {isBank ? (
        <p className="text-xs text-ink-2 italic py-2">
          Banks and insurers do not report standard operating cash flow or FCF. DCF calculator disabled for financial institutions.
        </p>
      ) : (
        <div className="space-y-3 text-xs">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <div>
              <label className="block font-mono text-[10px] uppercase text-ink-2 mb-1">Base FCF ({currency})</label>
              <input
                type="number"
                placeholder={latestFcf ? `Latest: ${(latestFcf / 1e6).toFixed(0)}M` : "e.g. 1000000000"}
                value={fcf}
                onChange={(e) => setFcf(e.target.value)}
                className="w-full rounded-card border border-border bg-bg-0 px-2 py-1 font-mono text-xs text-ink-0"
              />
            </div>
            <div>
              <label className="block font-mono text-[10px] uppercase text-ink-2 mb-1">Growth (g %)</label>
              <input
                type="number"
                placeholder="e.g. 6"
                value={growth}
                onChange={(e) => setGrowth(e.target.value)}
                className="w-full rounded-card border border-border bg-bg-0 px-2 py-1 font-mono text-xs text-ink-0"
              />
            </div>
            <div>
              <label className="block font-mono text-[10px] uppercase text-ink-2 mb-1">Discount (WACC %)</label>
              <input
                type="number"
                placeholder="e.g. 9"
                value={wacc}
                onChange={(e) => setWacc(e.target.value)}
                className="w-full rounded-card border border-border bg-bg-0 px-2 py-1 font-mono text-xs text-ink-0"
              />
            </div>
            <div>
              <label className="block font-mono text-[10px] uppercase text-ink-2 mb-1">Years</label>
              <input
                type="number"
                min="1"
                max="20"
                value={years}
                onChange={(e) => setYears(e.target.value)}
                className="w-full rounded-card border border-border bg-bg-0 px-2 py-1 font-mono text-xs text-ink-0"
              />
            </div>
          </div>

          {result && (
            <div className="rounded-card bg-bg-2/60 p-3 font-mono text-xs border border-border space-y-1">
              <div className="flex justify-between text-ink-1">
                <span>PV of Projection Period:</span>
                <span className="text-ink-0">{money(result.pvSum, currency)}</span>
              </div>
              <div className="flex justify-between text-ink-1">
                <span>PV of Terminal Value (2% perp):</span>
                <span className="text-ink-0">{money(result.pvTerminal, currency)}</span>
              </div>
              <div className="flex justify-between font-semibold text-accent pt-1 border-t border-border">
                <span>Implied Value:</span>
                <span>{money(result.enterpriseValue, currency)}</span>
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}
