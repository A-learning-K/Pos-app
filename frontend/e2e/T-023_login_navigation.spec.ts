/**
 * T-023 ログイン画面の遷移（IT／正常系・異常系）
 *
 * 参照元
 * - テスト設計書 v2.18 表2-1 T-023
 * - 設計仕様書 v2.10 3.1.1（成功で SC-02 へ）、3.1.3 表3-2 #4（トークンはメモリ保持・タブを閉じたら再ログイン）、
 *   2.4 画面遷移
 */
import { expect, test } from "@playwright/test";
import { SC02_PATH, expectSc01, expectSc02, loginFromSc01 } from "./support";

test.describe("T-023 ログイン画面の遷移", () => {
  test("【正常系】SC-01 でログインに成功すると SC-02 に遷移する", async ({ page }) => {
    const resp = await loginFromSc01(page);
    expect(resp.status()).toBe(200);
    await expectSc02(page);
  });

  test("【異常系】未ログインで SC-02 の URL を直接開くと SC-01 に戻る", async ({ page }) => {
    await page.goto(SC02_PATH);
    await expectSc01(page);
  });

  test("【異常系】「戻る」で SC-01 に戻っても、再度 SC-02 を開けばログイン状態が続く", async ({ page }) => {
    await loginFromSc01(page);
    await expectSc02(page);

    await page.goBack();
    await expectSc01(page);

    // 「再度 SC-02 を開く」＝ブラウザの「進む」（同じタブ・メモリ上のトークンを保持したまま）
    await page.goForward();
    await expectSc02(page);
  });

  test("【異常系】タブを閉じる（別タブで開き直す）と再ログインが必要", async ({ page, context }) => {
    await loginFromSc01(page);
    await expectSc02(page);
    await page.close();

    const newTab = await context.newPage();
    await newTab.goto(SC02_PATH);
    await expectSc01(newTab);
  });
});
