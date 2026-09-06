import React, { useState } from "react";
import { api } from "../../api/client";

interface ExportCenterModalProps {
  isOpen: boolean;
  onClose: () => void;
  companyId?: string;
}

export const ExportCenterModal: React.FC<ExportCenterModalProps> = ({ isOpen, onClose, companyId }) => {
  const [downloading, setDownloading] = useState<string | null>(null);

  if (!isOpen) return null;

  const download = async (type: string) => {
    setDownloading(type);
    try {
      let url = "";
      let filename = "";
      if (type === "memo" && companyId) {
        const response = (await api.requestMemo(companyId)) as { markdown?: string };
        const blob = new Blob([response.markdown ?? ""], { type: "text/markdown" });
        url = URL.createObjectURL(blob);
        filename = `${companyId}-memo.md`;
      } else if (type === "json" && companyId) {
        const response = (await api.requestRawDump(companyId)) as unknown;
        const blob = new Blob([JSON.stringify(response, null, 2)], { type: "application/json" });
        url = URL.createObjectURL(blob);
        filename = `${companyId}-raw.json`;
      } else if (type === "batch") {
        // Batch comparison CSV for 2 companies (demo)
        const res = await fetch(`/api/v1/export/batch?ids=US:AAPL:US,US:MSFT:US&format=csv`);
        const text = await res.text();
        const blob = new Blob([text], { type: "text/csv" });
        url = URL.createObjectURL(blob);
        filename = "batch-export.csv";
      } else if (type === "factsheet" && companyId) {
        const response = (await api.requestRawDump(companyId)) as unknown;
        const blob = new Blob([JSON.stringify(response, null, 2)], { type: "application/json" });
        url = URL.createObjectURL(blob);
        filename = `${companyId}-factsheet.json`;
      }
      if (url) {
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch {}
    setDownloading(null);
  };

  return (
    <div role="dialog" aria-modal="true" aria-labelledby="export-center-title" className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink-0/60 backdrop-blur-sm">
      <div className="w-full max-w-lg bg-bg-1 rounded-card border border-border shadow-2xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h2 id="export-center-title" className="font-heading font-semibold text-ink-0">Export Center</h2>
          <button onClick={onClose} aria-label="Close export center" className="p-1 text-ink-2 hover:text-ink-0">✕</button>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <button onClick={() => download("memo")} disabled={downloading === "memo"} className="p-3 rounded border border-border bg-bg-0 text-left hover:border-accent">
            <span className="font-mono text-xs font-semibold text-ink-0">Research Memo (Markdown)</span>
            <span className="text-[11px] text-ink-2 block">Editable draft with metrics, floors, flags, provenance</span>
          </button>
          <button onClick={() => download("factsheet")} disabled={downloading === "factsheet"} className="p-3 rounded border border-border bg-bg-0 text-left hover:border-accent">
            <span className="font-mono text-xs font-semibold text-ink-0">Factsheet PDF Data (JSON)</span>
            <span className="text-[11px] text-ink-2 block">Clean print via @media print</span>
          </button>
          <button onClick={() => download("batch")} disabled={downloading === "batch"} className="p-3 rounded border border-border bg-bg-0 text-left hover:border-accent">
            <span className="font-mono text-xs font-semibold text-ink-0">Batch Comparison (CSV)</span>
            <span className="text-[11px] text-ink-2 block">Formula-transparent columns, currency-tagged</span>
          </button>
          <button onClick={() => download("json")} disabled={downloading === "json"} className="p-3 rounded border border-border bg-bg-0 text-left hover:border-accent">
            <span className="font-mono text-xs font-semibold text-ink-0">Raw JSON Dump</span>
            <span className="text-[11px] text-ink-2 block">Dossier + scores + provenance</span>
          </button>
        </div>
        <p className="text-[11px] font-mono text-ink-2 border-t border-border pt-2">Currency: native ISO per row. Personal research software, not investment advice. AI narration is an interpretation of local facts, not a financial endorsement.</p>
      </div>
    </div>
  );
};

export default ExportCenterModal;
