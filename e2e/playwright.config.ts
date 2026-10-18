import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: ".",
  testMatch: "*.spec.ts",
  timeout: 120_000, // CI runners are slow; a cold compose stack plus two reloads can pass 60 s
  reporter: [["list", { printSteps: true }]],
  use: {
    baseURL: process.env.SAIL_BASE_URL || `http://localhost:${process.env.HOST_PORT || "8000"}`,
  },
  projects: [{ name: "chromium", use: { browserName: "chromium" } }],
});
