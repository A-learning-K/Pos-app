/**
 * Playwright 共通：代表値・画面の探し方・ログイン操作。
 *
 * 画面要素は設計仕様書の項目名・ボタン名（表3-3・表3-9）と role で探す（実装コードは参照しない）。
 * 画面側の実装と名前が合わない場合は、このファイルの SC01/SC02 だけを直せばよい。
 */
import { expect, type Page } from "@playwright/test";

// --- 代表値（テスト設計書 v2.18 T-012・T-022：db/seed.sql の一般担当者） ---
export const E001 = { id: "E001", name: "山田太郎", password: "Passw0rd1" };

export const API_URL = process.env.API_URL ?? "http://localhost:8000";
export const API_PREFIX = "/api/v1"; // 設計仕様書 4.1 ベースパス

// --- 画面のURL（Week4コーディング計画 8節のフォルダ構成：app/login・app/pos） ---
export const SC01_PATH = "/login";
export const SC02_PATH = "/pos";

// --- SC-01 ログイン画面（設計仕様書 3.1.4 表3-3） ---
export const SC01 = {
  employeeId: (page: Page) => page.getByLabel("担当者ID"),
  password: (page: Page) => page.getByLabel("パスワード"),
  loginButton: (page: Page) => page.getByRole("button", { name: "ログイン" }),
};

// --- SC-02 POSレジ画面（設計仕様書 3.3.4 表3-9） ---
export const SC02 = {
  logoutButton: (page: Page) => page.getByRole("button", { name: "ログアウト" }), // #3
  masterLink: (page: Page) => page.getByRole("link", { name: "マスタ管理" }), // #2（is_admin のみ）
};

/** SC-01 が表示されていること（担当者ID・パスワード・ログインボタン）。 */
export async function expectSc01(page: Page) {
  await expect(page).toHaveURL(new RegExp(`${SC01_PATH}$`));
  await expect(SC01.employeeId(page)).toBeVisible();
  await expect(SC01.password(page)).toBeVisible();
  await expect(SC01.loginButton(page)).toBeVisible();
}

/** SC-02 が表示されていること（ログイン中の担当者ID・氏名：表3-9 #1）。 */
export async function expectSc02(page: Page, who = E001) {
  await expect(page).toHaveURL(new RegExp(`${SC02_PATH}$`));
  await expect(page.getByText(who.id, { exact: false }).first()).toBeVisible();
  await expect(page.getByText(who.name, { exact: false }).first()).toBeVisible();
}

/** SC-01 で入力してログインし、A-01 の応答を返す。 */
export async function loginFromSc01(page: Page, who = E001) {
  await page.goto(SC01_PATH);
  await SC01.employeeId(page).fill(who.id);
  await SC01.password(page).fill(who.password);
  const [resp] = await Promise.all([
    page.waitForResponse((r) => r.url().endsWith(`${API_PREFIX}/auth/login`) && r.request().method() === "POST"),
    SC01.loginButton(page).click(),
  ]);
  return resp;
}

/** T-024 用：DB 接続情報（実DB）。 */
export function dbConfig() {
  const host = process.env.TEST_DB_HOST;
  if (!host) throw new Error("T-024 には TEST_DB_HOST / TEST_DB_USER / TEST_DB_PASSWORD / TEST_DB_NAME の設定が必要です");
  return {
    host,
    port: Number(process.env.TEST_DB_PORT ?? 3306),
    user: process.env.TEST_DB_USER,
    password: process.env.TEST_DB_PASSWORD,
    database: process.env.TEST_DB_NAME,
    // Azure MySQL は require_secure_transport=ON（設計仕様書 5.2）。ローカルDockerなら TEST_DB_SSL=false
    ssl: process.env.TEST_DB_SSL === "false" ? undefined : { rejectUnauthorized: true },
  };
}
