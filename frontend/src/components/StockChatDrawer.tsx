import React, { useEffect, useRef, useState } from "react";
import { api } from "../api/client";

/**
 * StockChatDrawer — Fact-grounded AI chat for a single company (Workstream 6).
 *
 * Rules (enforced by backend):
 * - LLM can only reference facts from deterministic DB columns.
 * - LLM cannot alter fundamentals, scores, or any numerical value.
 * - Scores are labelled as "deterministic math" in the system prompt.
 * - CAD/USD money is never mixed.
 * - Final disclaimer is appended to every response.
 *
 * UI: slide-over drawer from the right side, 4 starter chips, markdown-style
 * response rendering (bold/italic/code), no third-party chat library.
 */

interface Message {
  role: "user" | "assistant";
  content: string;
  model?: string;
  error?: boolean;
}

const STARTER_CHIPS = [
  "What are the biggest accounting red flags?",
  "Is the dividend covered by real free cash flow?",
  "Explain the difference between its naive ROIC and Penman RNOA.",
  "How does this company justify beating an 8% index hurdle?",
];

const DISCLAIMER =
  "AI draft grounded in verified local facts. Not investment advice.";

/** Simple inline markdown renderer: **bold**, *italic*, `code`, newlines. */
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
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Scroll to bottom on new messages.
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // Focus input when drawer opens.
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 150);
    }
  }, [isOpen]);

  // Reset when company changes.
  useEffect(() => {
    setMessages([]);
    setInput("");
    setError(null);
  }, [companyId]);

  const sendMessage = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    const userMsg: Message = { role: "user", content: trimmed };
    const nextMessages = [...messages, userMsg];
    setMessages(nextMessages);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      // Pass conversation history (excluding error messages).
      const apiMessages = nextMessages
        .filter((m) => !m.error)
        .map((m) => ({ role: m.role, content: m.content }));

      const resp = await api.chat(companyId, apiMessages);
      const assistantMsg: Message = {
        role: "assistant",
        content: resp.content,
        model: resp.model_used,
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
      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-[2px] no-print"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Drawer panel */}
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
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-4 py-3 shrink-0">
          <div>
            <p className="text-xs font-mono uppercase tracking-wider text-ink-2">
              AI Research Chat
            </p>
            <p className="text-sm font-semibold text-ink-0 mt-0.5">
              {companyName ?? companyId}
            </p>
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

        {/* Disclaimer chip */}
        <div className="border-b border-border bg-bg-1 px-4 py-2 shrink-0">
          <p className="text-[10px] text-ink-2 leading-relaxed">{DISCLAIMER}</p>
        </div>

        {/* Messages */}
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
              <span>Analysing facts…</span>
            </div>
          )}
        </div>

        {/* Input bar */}
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
        {!isUser && message.model && !message.error && (
          <p className="mt-1.5 text-[9px] text-ink-2 font-mono truncate">
            {message.model} · deterministic facts
          </p>
        )}
      </div>
    </div>
  );
};

/** Three-dot loading animation. */
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
