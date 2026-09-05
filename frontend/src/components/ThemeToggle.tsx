import { useTheme } from "../lib/theme";

export function ThemeToggle({ className = "" }: { className?: string }) {
  const [theme, toggle] = useTheme();
  const isDark = theme === "dark";

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      title={isDark ? "Switch to Light Mode (Ivory Desk)" : "Switch to Dark Mode (Night Desk)"}
      className={`relative inline-flex items-center gap-1.5 rounded-card border border-border bg-bg-0 hover:bg-bg-2 px-2.5 py-1.5 text-xs font-mono text-ink-1 hover:text-ink-0 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent ${className}`}
    >
      <span className="flex items-center justify-center w-4 h-4">
        {isDark ? (
          // Moon icon
          <svg
            className="w-3.5 h-3.5 text-accent transition-transform duration-200"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth="2"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
            />
          </svg>
        ) : (
          // Sun icon
          <svg
            className="w-3.5 h-3.5 text-accent transition-transform duration-200"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth="2"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
            />
          </svg>
        )}
      </span>
      <span className="text-[11px] font-medium uppercase tracking-wider hidden sm:inline">
        {isDark ? "Dark" : "Light"}
      </span>
    </button>
  );
}

export default ThemeToggle;
