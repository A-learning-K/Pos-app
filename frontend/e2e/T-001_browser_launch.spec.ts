/**
 * T-001 ブラウザからの起動（IT／正常系・非機能系）
 *
 * 参照元
 * - テスト設計書 v2.19 表2-1 T-001（v2.19でBUG-003を反映し、「/」の期待値を修正済み）
 * - 設計仕様書 v2.10 1.1（Chrome のみ・すべて HTTPS）、4.1（ベースパス /api/v1）、5.2（HTTPS のみ）
 * - Week4コーディング計画 8節：frontend/app/page.tsx は SC-01（/login）への遷移リンクを持つページ
 *
 * 2026-09-29 カバレッジ点検で追加：このテストは「/」を開くと直接SC-01が表示される、という
 * BUG-003修正前の古い期待値のままだったため（バグ管理表 BUG-005）、
 * 現行の期待値（「/」はSC-01へのリンクを持つページ→リンクからSC-01に遷移）に修正した。
 */
import { expect, request, test } from "@playwright/test";
import { API_PREFIX, SC01, loginFromSc01 } from "./support";

test.describe("T-001 ブラウザからの起動", () => {
  test("【正常系】トップ（/）を開くとログイン画面（SC-01）へのリンクを持つページが表示され、そのリンクから遷移するとSC-01が表示される", async ({ page }) => {
    await page.goto("/");

    // Week4計画8節：「/」はSC-01への遷移リンクのみを持つ構成（直接ログインフォームは出ない）
    const loginLink = page.getByRole("link", { name: /ログイン/ });
    await expect(loginLink).toBeVisible();

    await loginLink.click();

    await expect(SC01.employeeId(page)).toBeVisible();
    await expect(SC01.password(page)).toBeVisible();
    await expect(SC01.loginButton(page)).toBeVisible();
  });

  test("【正常系】API が /api/v1 配下で応答する", async ({ page }) => {
    const resp = await loginFromSc01(page);
    expect(new URL(resp.url()).pathname.startsWith(`${API_PREFIX}/`)).toBe(true);
    expect(resp.status()).toBe(200);
  });

  test("【非機能系】http:// でアクセスすると https:// へリダイレクトされる", async ({ baseURL }) => {
    // HTTPS 化は App Service の設定（5.2）のため、https の環境（Azure）でのみ確認できる
    test.skip(!baseURL?.startsWith("https://"), "BASE_URL が https の環境（Azure）でのみ実施");

    const httpUrl = baseURL!.replace(/^https:/, "http:");
    const ctx = await request.newContext();
    const resp = await ctx.get(httpUrl, { maxRedirects: 0 });
    expect([301, 302, 307, 308]).toContain(resp.status());
    expect(resp.headers()["location"]).toMatch(/^https:\/\//);
    await ctx.dispose();
  });
});
