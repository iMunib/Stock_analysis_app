import React, { useState } from "react";
import { api } from "../../api/client";

interface TransactionModalProps {
  isOpen: boolean;
  onClose: () => void;
  accounts: Array<{ id: string; name: string; currency: string }>;
  onCreated: () => void;
}

export const TransactionModal: React.FC<TransactionModalProps> = ({ isOpen, onClose, accounts, onCreated }) => {
  const [accountId, setAccountId] = useState(accounts[0]?.id ?? "");
  const [companyId, setCompanyId] = useState("US:AAPL:US");
  const [txnType, setTxnType] = useState<"buy" | "sell" | "dividend">("buy");
  const [quantity, setQuantity] = useState("10");
  const [price, setPrice] = useState("150");
  const [txnDate, setTxnDate] = useState(new Date().toISOString().slice(0, 10));
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const submit = async () => {
    setError(null);
    try {
      await api.createPortfolioTransaction({
        account_id: accountId,
        company_id: companyId,
        txn_type: txnType,
        quantity: parseFloat(quantity),
        price_per_share: parseFloat(price),
        txn_date: txnDate,
      });
      onCreated();
      onClose();
    } catch (e: any) {
      setError(e?.message ?? "Failed to create transaction");
    }
  };

  return (
    <div role="dialog" aria-modal="true" aria-labelledby="txn-modal-title" className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink-0/60 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-card border border-border bg-bg-1 shadow-2xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h2 id="txn-modal-title" className="font-heading font-semibold text-ink-0">Add Transaction</h2>
          <button onClick={onClose} aria-label="Close transaction modal" className="p-1 text-ink-2 hover:text-ink-0">✕</button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <label className="block">
            <span className="font-mono text-[11px] uppercase text-ink-2">Account</span>
            <select value={accountId} onChange={(e) => setAccountId(e.target.value)} className="mt-1 w-full rounded border border-border bg-bg-0 px-2 py-1.5 text-xs" aria-label="Account">
              {accounts.map((a) => <option key={a.id} value={a.id}>{a.name} ({a.currency})</option>)}
            </select>
          </label>
          <label className="block">
            <span className="font-mono text-[11px] uppercase text-ink-2">Company ID</span>
            <input value={companyId} onChange={(e) => setCompanyId(e.target.value)} placeholder="US:AAPL:US" className="mt-1 w-full rounded border border-border bg-bg-0 px-2 py-1.5 text-xs font-mono" aria-label="Company ID" />
          </label>
          <label className="block">
            <span className="font-mono text-[11px] uppercase text-ink-2">Type</span>
            <select value={txnType} onChange={(e) => setTxnType(e.target.value as any)} className="mt-1 w-full rounded border border-border bg-bg-0 px-2 py-1.5 text-xs" aria-label="Transaction type">
              <option value="buy">Buy</option>
              <option value="sell">Sell</option>
              <option value="dividend">Dividend</option>
            </select>
          </label>
          <label className="block">
            <span className="font-mono text-[11px] uppercase text-ink-2">Date</span>
            <input type="date" value={txnDate} onChange={(e) => setTxnDate(e.target.value)} className="mt-1 w-full rounded border border-border bg-bg-0 px-2 py-1.5 text-xs" aria-label="Transaction date" />
          </label>
          <label className="block">
            <span className="font-mono text-[11px] uppercase text-ink-2">Quantity</span>
            <input type="number" value={quantity} onChange={(e) => setQuantity(e.target.value)} className="mt-1 w-full rounded border border-border bg-bg-0 px-2 py-1.5 text-xs font-mono" aria-label="Quantity" />
          </label>
          <label className="block">
            <span className="font-mono text-[11px] uppercase text-ink-2">Price per share</span>
            <input type="number" value={price} onChange={(e) => setPrice(e.target.value)} className="mt-1 w-full rounded border border-border bg-bg-0 px-2 py-1.5 text-xs font-mono" aria-label="Price per share" />
          </label>
        </div>

        {error && <p role="alert" className="text-xs text-neg">{error}</p>}

        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="px-3 py-1.5 rounded border border-border text-xs">Cancel</button>
          <button onClick={submit} className="px-3 py-1.5 rounded bg-accent text-bg-0 text-xs font-mono font-semibold">Save Transaction</button>
        </div>

        <p className="text-[11px] font-mono text-ink-2 border-t border-border pt-2">Personal research software, not investment advice. Portfolio tracking and alerts run locally.</p>
      </div>
    </div>
  );
};

export default TransactionModal;
