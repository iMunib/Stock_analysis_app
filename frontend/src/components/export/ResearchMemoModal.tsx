import React, { useEffect, useState } from "react";
import { api } from "../../api/client";

interface ResearchMemoModalProps {
  companyId: string;
  isOpen: boolean;
  onClose: () => void;
}

export const ResearchMemoModal: React.FC<ResearchMemoModalProps> = ({ companyId, isOpen, onClose }) => {
  const [markdown, setMarkdown] = useState("");
  const [loading, setLoading] = useState(false);
  const [editing, setEditing] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    setLoading(true);
    api.requestMemo(companyId)
      .then((res: any) => setMarkdown(res.markdown ?? res.content ?? ""))
      .catch(() => setMarkdown(`# Research Memo - ${companyId}\n\nNo memo available - insufficient data.`))
      .finally(() => setLoading(false));
  }, [companyId, isOpen]);

  if (!isOpen) return null;

  const download = () => {
    const blob = new Blob([markdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${companyId}-research-memo.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div role="dialog" aria-modal="true" aria-labelledby="memo-title" className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink-0/60 backdrop-blur-sm overflow-y-auto">
      <div className="w-full max-w-3xl bg-bg-1 rounded-card border border-border shadow-2xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between px-5 py-3 border-b border-border bg-bg-0 sticky top-0">
          <h2 id="memo-title" className="font-heading font-semibold text-ink-0">Research Memo Draft - Editable Markdown</h2>
          <button onClick={onClose} aria-label="Close memo modal" className="p-2 text-ink-2 hover:text-ink-0" onKeyDown={(e) => { if (e.key === "Escape") onClose(); }}>✕</button>
        </div>
        <div className="flex-1 overflow-y-auto p-5 space-y-3">
          {loading ? <p className="text-xs text-ink-2">Generating memo…</p> : (
            <>
              <div className="flex gap-2">
                <button onClick={() => setEditing((v) => !v)} className="px-3 py-1 rounded border border-border text-xs font-mono">{editing ? "Preview" : "Edit"}</button>
                <button onClick={download} className="px-3 py-1 rounded bg-accent text-bg-0 text-xs font-mono">Download .md</button>
              </div>
              {editing ? (
                <textarea
                  value={markdown}
                  onChange={(e) => setMarkdown(e.target.value)}
                  className="w-full h-[50vh] rounded border border-border bg-bg-0 p-3 text-xs font-mono"
                  aria-label="Research memo markdown"
                />
              ) : (
                <pre className="whitespace-pre-wrap rounded border border-border bg-bg-0 p-3 text-xs font-mono max-h-[50vh] overflow-y-auto" aria-label="Research memo preview">{markdown}</pre>
              )}
              <p className="text-[11px] font-mono text-ink-2">Currency: native ISO per row. Provenance per metric included. Personal research software, not investment advice.</p>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResearchMemoModal;