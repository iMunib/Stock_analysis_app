import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  retries: 1, // absorb load-order timing flakes (documented in PHASE9_REPORT)
  use: {
    baseURL: "http://localhost:5173",
    headless: true,
  },
  // UI must be up (docker compose --profile frontend up --build -d); no webServer here.
});
