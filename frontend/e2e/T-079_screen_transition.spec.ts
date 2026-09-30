/**
 * T-079 画面遷移（IT／正常系）
 *
 * 参照元
 * - テスト設計書 v2.18 表2-1 T-079：SC-01〜05 を 2.4 の遷移図どおりに操作でき、
 *   遷移図にない遷移（一般担当者→SC-05）が起きない
 * - 設計仕様書 v2.10 2.4（表2-10）、3.3.4 表3-9 #2（マスタ管理リンクは is_admin のみ）・#3（ログアウト→SC-01）、4.3 A-02
 *
 * SC-03（FG-06）・SC-04/05（FG-07）は Week4 スコープ決定により未実装のため test.fixme とし、
 * 実装後に中身を書いて有効化する（今回は SC-01⇔SC-02 の遷移と、一般担当者の入口非表示を確認）。
 */
import { expect, test } from "@playwright/test";
import { API_PREFIX, SC02, expectSc01, expectSc02, loginFromSc01 } from "./support";

test.describe("T-079 画面遷移", () => {
  test("【正常系】SC-01 →（ログイン）→ SC-02 →（ログアウト）→ SC-01", async ({ page }) => {
    await loginFromSc01(page);
    await expectSc02(page);

    const [logoutResp] = await Promise.all([
      page.waitForResponse((r) => r.url().endsWith(`${API_PREFIX}/auth/logout`) && r.request().method() === "POST"),
      SC02.logoutButton(page).click(),
    ]);
    expect(logoutResp.status()).toBe(204); // 4.3 A-02
    await expectSc01(page);
  });

  test("【正常系】一般担当者（E001）には SC-04/05 への入口（マスタ管理）が表示されない", async ({ page }) => {
    await loginFromSc01(page);
    await expectSc02(page);
    await expect(SC02.masterLink(page)).toHaveCount(0);
    // 入口が無いことの対照として、SC-02 の他の要素（ログアウト）は表示されている
    await expect(SC02.logoutButton(page)).toBeVisible();
  });

  test.fixme("【正常系】SC-02 →（購入確定）→ SC-03 →（閉じる）→ SC-02", async () => {
    // FG-06 未実装（Week4 スコープ外）
  });

  test.fixme("【正常系】管理者：SC-02 →（マスタ管理）→ SC-04 →（再認証）→ SC-05 →（戻る）→ SC-02", async () => {
    // FG-07 未実装（Week4 スコープ外）。管理者 A001 の代表値もテスト設計書への追記が必要
  });

  test.fixme("【正常系】一般担当者が SC-05 の URL を直接開いても SC-05 に入れない", async () => {
    // SC-05 の URL が設計仕様書に未定義・画面も未実装のため、実装後に追加
  });
});
