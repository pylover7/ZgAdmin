import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: "html",
  timeout: 30000,
  use: {
    baseURL: "http://localhost:7000",
    trace: "on-first-retry",
    screenshot: "only-on-failure"
  },
  projects: [
    {
      name: "chromium",
      use: { browserName: "chromium" }
    }
  ],
  webServer: [
    {
      command: "cd /workspace/backend && uv run python main.py",
      port: 7001,
      reuseExistingServer: true,
      timeout: 30000
    },
    {
      command: "cd /workspace/frontend && bun dev",
      port: 7000,
      reuseExistingServer: true,
      timeout: 60000
    }
  ]
});
