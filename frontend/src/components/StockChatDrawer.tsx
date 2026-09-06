import React, { useEffect, useRef, useState } from "react";
import { api } from "../api/client";

interface Message {
  role: "user" | "assistant";
  content: string;
  model?: string;
  citations?: Array<{ key: string; value: string; source: string }>;
  error?: boolean;
}

const STARTER_CHIPS = [
  "What are the biggest accounting red flags?",
  "Is the dividend covered by real free cash flow?",
  "Explain the difference between its naive ROIC and Penman RNOA.",
  "How does this company justify beating an 8% index hurdle?",
];

const DISCLAIMER =
  "AI Narration (not the score) - Personal research software, not investment advice. AI narration is an interpretation of local facts, not a financial endorsement.";

function renderMarkdown(text: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\n)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("*") && part.endsWith("*")) {
      return <em key={i}>{part.slice(1, -1)}</em>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code key={i} className="rounded bg-bg-2 px-1 py-0.5 text-[11px] font-mono text-accent">
          {part.slice(1, -1)}
        </code>
      );
    }
    if (part === "\n") {
      return <br key={i} />;
    }
    return <span key={i}>{part}</span>;
  });
}

function CitationChips({ citations }: { citations?: Array<{ key: string; value: string; source: string }> }) {
  if (!citations || citations.length === 0) return null;
  return (
    <div className="mt-2 flex flex-wrap gap-1">
      {citations.slice(0, 6).map((c, i) => (
        <span
          key={i}
          title={`${c.key}: ${c.value} - source: ${c.source}`}
          className="inline-flex items-center gap-1 rounded-chip border border-accent/30 bg-accent-weak px-1.5 py-0.5 text-[10px] font-mono text-accent hover:bg-accent/20 cursor-help"
          aria-label={`Citation ${c.key} ${c.value}`}
        >
          {c.key}: {c.value}
        </span>
      ))}
    </div>
  );
}

interface StockChatDrawerProps {
  companyId: string;
  companyName?: string;
  isOpen: boolean;
  onClose: () => void;
}

const StockChatDrawer: React.FC<StockChatDrawerProps> = ({
  companyId,
  companyName,
  isOpen,
  onClose,
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"default" | "100w" | "bullets" | "memo">("default");
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 150);
    }
  }, [isOpen]);

  useEffect(() => {
    setMessages([]);
    setInput("");
    setError(null);
  }, [companyId]);

  const sendMessage = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    // Apply view mode suffix for multi-format toggles (US-0702/US-0716)
    let promptText = trimmed;
    if (viewMode === "100w") promptText = `${trimmed} - Please respond in exactly 100 words, as a 100-word executive summary.`;
    if (viewMode === "bullets") promptText = `${trimmed} - Please respond with bullet points, 50/50 bull/bear.`;
    if (viewMode === "memo") promptText = `${trimmed} - Please respond as a formal board memo with headings.`;

    const userMsg: Message = { role: "user", content: promptText };
    const nextMessages = [...messages, userMsg];
    setMessages(nextMessages);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const apiMessages = nextMessages
        .filter((m) => !m.error)
        .map((m) => ({ role: m.role, content: m.content }));

      const resp = await api.chat(companyId, apiMessages);
      const assistantMsg: Message = {
        role: "assistant",
        content: resp.content,
        model: resp.model_used,
        citations: (resp as any).citations ?? undefined,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Chat request failed.";
      setError(msg);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `⚠️ ${msg} All deterministic financial data on screen remains valid.`,
          error: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
    if (e.key === "Escape") {
      onClose();
    }
  };

  const clearChat = () => {
    setMessages([]);
    setError(null);
    setInput("");
  };

  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-[2px] no-print"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      <aside
        role="dialog"
        aria-modal="true"
        aria-label={`AI research chat for ${companyName ?? companyId}`}
        className={[
          "fixed top-0 right-0 z-50 flex h-full w-full max-w-[420px] flex-col border-l border-border",
          "bg-bg-0 shadow-2xl transition-transform duration-300 ease-out no-print",
          isOpen ? "translate-x-0" : "translate-x-full pointer-events-none invisible",
        ].join(" ")}
      >
        <div className="flex items-center justify-between border-b border-border px-4 py-3 shrink-0">
          <div>
            <p className="text-xs font-mono uppercase tracking-wider text-ink-2">
              AI Research Chat
            </p>
            <p className="text-sm font-semibold text-ink-0 mt-0.5">
              {companyName ?? companyId}
            </p>
            <p className="text-[10px] font-mono text-accent mt-0.5">AI Narration (not the score) - minimax/minimax-m3:free</p>
          </div>
          <div className="flex items-center gap-2">
            {messages.length > 0 && (
              <button
                onClick={clearChat}
                className="rounded px-2 py-1 text-[11px] text-ink-2 hover:text-ink-1 hover:bg-bg-2 transition-colors"
                aria-label="Clear conversation"
              >
                Clear
              </button>
            )}
            <button
              onClick={onClose}
              className="rounded p-1.5 text-ink-2 hover:bg-bg-2 hover:text-ink-0 transition-colors"
              aria-label="Close chat"
            >
              <svg
                viewBox="0 0 16 16"
                width="16"
                height="16"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
              >
                <line x1="3" y1="3" x2="13" y2="13" />
                <line x1="13" y1="3" x2="3" y2="13" />
              </svg>
            </button>
          </div>
        </div>

        <div className="border-b border-border bg-bg-1 px-4 py-2 shrink-0">
          <p className="text-[10px] text-ink-2 leading-relaxed">{DISCLAIMER}</p>
          <div className="mt-2 flex flex-wrap gap-1.5" role="tablist" aria-label="Narration format">
            <button role="tab" aria-selected={viewMode === "default"} onClick={() => setViewMode("default")} className={`px-2 py-1 rounded-chip text-[10px] font-mono border ${viewMode === "default" ? "bg-accent text-bg-0 border-accent" : "bg-bg-0 text-ink-2 border-border"}`}>Default</button>
            <button role="tab" aria-selected={viewMode === "100w"} onClick={() => setViewMode("100w")} className={`px-2 py-1 rounded-chip text-[10px] font-mono border ${viewMode === "100w" ? "bg-accent text-bg-0 border-accent" : "bg-bg-0 text-ink-2 border-border"}`}>100-word</button>
            <button role="tab" aria-selected={viewMode === "bullets"} onClick={() => setViewMode("bullets")} className={`px-2 py-1 rounded-chip text-[10px] font-mono border ${viewMode === "bullets" ? "bg-accent text-bg-0 border-accent" : "bg-bg-0 text-ink-2 border-border"}`}>Bullets</button>
            <button role="tab" aria-selected={viewMode === "memo"} onClick={() => setViewMode("memo")} className={`px-2 py-1 rounded-chip text-[10px] font-mono border ${viewMode === "memo" ? "bg-accent text-bg-0 border-accent" : "bg-bg-0 text-ink-2 border-border"}`}>Board Memo</button>
          </div>
        </div>

        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto px-4 py-4 space-y-4 scroll-smooth"
        >
          {messages.length === 0 && (
            <div className="space-y-3">
              <p className="text-xs text-ink-2 text-center pt-4">
                Ask the AI analyst anything about{" "}
                <span className="text-ink-1 font-medium">
                  {companyName ?? companyId}
                </span>
                . Responses are grounded in deterministic financials only.
              </p>
              <div className="grid grid-cols-1 gap-2 mt-4">
                {STARTER_CHIPS.map((chip, i) => (
                  <button
                    key={i}
                    onClick={() => sendMessage(chip)}
                    className="text-left text-xs rounded-card border border-border bg-bg-1 px-3 py-2.5 text-ink-1 hover:border-accent/50 hover:bg-accent-weak hover:text-ink-0 transition-all duration-150"
                  >
                    {chip}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((m, i) => (
            <MessageBubble key={i} message={m} />
          ))}
          {loading && (
            <div className="flex items-center gap-2 text-xs text-ink-2">
              <LoadingDots />
              <span>Analysing facts… (minimax/minimax-m3:free, 45s timeout)</span>
            </div>
          )}
        </div>

        <div className="border-t border-border px-4 py-3 shrink-0">
          <div className="flex items-center gap-2">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about financials, risks, thesis…"
              disabled={loading}
              className={[
                "flex-1 rounded-card border border-border bg-bg-1 px-3 py-2 text-sm text-ink-0",
                "placeholder:text-ink-2 focus:outline-none focus:ring-1 focus:ring-accent/50",
                "disabled:opacity-60 transition-colors",
              ].join(" ")}
              maxLength={500}
              aria-label="Chat message input"
            />
            <button
              onClick={() => sendMessage(input)}
              disabled={!input.trim() || loading}
              className={[
                "flex shrink-0 items-center justify-center rounded-card border px-3 py-2",
                "text-xs font-medium transition-all",
                input.trim() && !loading
                  ? "border-accent bg-accent text-white hover:bg-accent/90"
                  : "border-border bg-bg-2 text-ink-2 cursor-not-allowed",
              ].join(" ")}
              aria-label="Send message"
            >
              Send
            </button>
          </div>
          {error && (
            <p className="mt-2 text-[10px] text-red-400">{error}</p>
          )}
          <p className="mt-2 text-[10px] font-mono text-ink-2">Model: minimax/minimax-m3:free → mistralai/mistral-small-24b-instruct-2501:free (fallback), 45s timeout, llm_cache.</p>
        </div>
      </aside>
    </>
  );
};

const MessageBubble: React.FC<{ message: Message }> = ({ message }) => {
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={[
          "max-w-[85%] rounded-card px-3 py-2.5 text-sm leading-relaxed",
          isUser
            ? "bg-accent text-white"
            : message.error
              ? "border border-red-500/30 bg-red-900/20 text-red-300"
              : "border border-border bg-bg-1 text-ink-0",
        ].join(" ")}
      >
        <div className="text-[13px]">{renderMarkdown(message.content)}</div>
        {!isUser && message.citations && <CitationChips citations={message.citations} />}
        {!isUser && message.model && !message.error && (
          <p className="mt-1.5 text-[9px] text-ink-2 font-mono truncate">
            {message.model} · deterministic facts · <span className="text-accent">AI Narration (not the score)</span>
          </p>
        )}
      </div>
    </div>
  );
};

const LoadingDots: React.FC = () => (
  <div className="flex items-center gap-1" aria-hidden="true">
    {[0, 1, 2].map((i) => (
      <div
        key={i}
        className="h-1.5 w-1.5 rounded-full bg-accent/60 animate-bounce"
        style={{ animationDelay: `${i * 150}ms` }}
      />
    ))}
  </div>
);

export default StockChatDrawer;