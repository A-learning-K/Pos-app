import { defineConfig, devices } from "@playwright/test";

/**
 * 結合テスト（IT）：実ブラウザ → 実API → 実DB（テスト設計書 1.1）。
 * 事前に backend（uvicorn）と frontend（next dev）を起動し、DB に db/seed.sql を投入しておく。
 *
 * 環境変数（未指定時はローカル既定値）
 *   BASE_URL     フロントのURL（既定 http://localhost:3000）
 *   API_URL      バックエンドのURL（既定 http://localhost:8000）
 *   TEST_DB_*    T-024 で employees を直接読むための接続情報（e2e/support.ts 参照）
 */
export default defineConfig({
  testDir: "./e2e",
  // macOS の AppleDouble ファイル（外部SSD等でファイル操作時に自動生成される「._」始まりの影ファイル）を除外
  // 例：e2e/._T-001_browser_launch.spec.ts が SyntaxError で落ちる問題への対策（jest.config.js と同種の対応）
  testIgnore: ["**/._*"],
  timeout: 30_000,
  retries: 0,
  reporter: [["list"], ["html", { open: "never" }]], // 実行ログを残す（テスト設計書 1.6 証跡）
  use: {
    baseURL: process.env.BASE_URL ?? "http://localhost:3000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    // 設計仕様書 1.1：対応ブラウザは Google Chrome のみ
    { name: "chrome", use: { ...devices["Desktop Chrome"], channel: "chrome" } },
  ],
});
