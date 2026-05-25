import { defineConfig } from "vitest/config";
import vue from "@vitejs/plugin-vue";
import vueJsx from "@vitejs/plugin-vue-jsx";
import { alias } from "./build/utils";

export default defineConfig({
  plugins: [vue(), vueJsx()],
  resolve: { alias },
  test: {
    globals: true,
    environment: "happy-dom",
    include: ["src/**/*.{test,spec}.{ts,tsx}"],
    coverage: {
      provider: "v8",
      reporter: ["text", "lcov"],
      include: ["src/**/*.{ts,tsx}"],
      exclude: [
        "src/**/*.d.ts",
        "src/**/*.test.{ts,tsx}",
        "src/**/*.spec.{ts,tsx}",
        "src/main.ts",
        "src/style/**",
        "src/assets/**",
        "src/types/**",
        "src/views/**",
        "src/components/**",
        "src/layout/**",
        "src/plugins/**",
        "src/directives/**",
        "src/router/modules/**",
        "src/router/index.ts",
        "src/utils/chinaArea.ts",
        "src/utils/print.ts"
      ]
    },
    setupFiles: ["tests/setup.ts"]
  }
});
