import { useEffect, useState } from "react";
import type { ThemeMode } from "../styles/tokens";

const THEME_STORAGE_KEY = "investment_desk_theme";

export function getInitialTheme(): ThemeMode {
  if (typeof window === "undefined") return "dark";
  try {
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    if (stored === "light" || stored === "dark") {
      return stored;
    }
    return "dark";
  } catch {
    return "dark";
  }
}

export function applyTheme(theme: ThemeMode): void {
  if (typeof document === "undefined") return;
  document.documentElement.setAttribute("data-theme", theme);
  document.documentElement.classList.remove("theme-dark", "theme-light");
  document.documentElement.classList.add(`theme-${theme}`);
  if (theme === "light") {
    document.documentElement.style.colorScheme = "light";
  } else {
    document.documentElement.style.colorScheme = "dark";
  }
}

export function setTheme(theme: ThemeMode): void {
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // ignore storage restrictions
  }
  applyTheme(theme);
  window.dispatchEvent(new CustomEvent("themechange", { detail: theme }));
}

export function toggleTheme(): ThemeMode {
  const current = getInitialTheme();
  const next: ThemeMode = current === "dark" ? "light" : "dark";
  setTheme(next);
  return next;
}

export function useTheme(): [ThemeMode, () => void, (t: ThemeMode) => void] {
  const [theme, setLocalTheme] = useState<ThemeMode>(getInitialTheme);

  useEffect(() => {
    applyTheme(theme);

    const onThemeChange = (e: Event) => {
      const customEvent = e as CustomEvent<ThemeMode>;
      if (customEvent.detail) {
        setLocalTheme(customEvent.detail);
      } else {
        setLocalTheme(getInitialTheme());
      }
    };

    const onStorage = (e: StorageEvent) => {
      if (e.key === THEME_STORAGE_KEY && (e.newValue === "light" || e.newValue === "dark")) {
        setLocalTheme(e.newValue);
        applyTheme(e.newValue);
      }
    };

    window.addEventListener("themechange", onThemeChange);
    window.addEventListener("storage", onStorage);
    return () => {
      window.removeEventListener("themechange", onThemeChange);
      window.removeEventListener("storage", onStorage);
    };
  }, [theme]);

  const toggle = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    setLocalTheme(next);
  };

  const setSpecific = (next: ThemeMode) => {
    setTheme(next);
    setLocalTheme(next);
  };

  return [theme, toggle, setSpecific];
}
