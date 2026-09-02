import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  use: {
    baseURL: "http://localhost:5173",
    headless: true,
  },
  // UI must be up (docker compose --profile frontend up --build -d); no webServer here.
});
