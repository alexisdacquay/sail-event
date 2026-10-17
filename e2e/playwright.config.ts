import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: ".",
  testMatch: "*.spec.ts",
  timeout: 60_000,
  use: {
    baseURL: process.env.SAIL_BASE_URL || `http://localhost:${process.env.HOST_PORT || "8000"}`,
  },
  projects: [{ name: "chromium", use: { browserName: "chromium" } }],
});
