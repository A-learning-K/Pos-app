/**
 * T-024 パスワード保存・外部ID基盤への通信なし（IT／正常系・非機能系）
 *
 * 参照元
 * - テスト設計書 v2.18 表2-1 T-024
 * - 設計仕様書 v2.10 2.3.1（password_hash＝bcrypt、平文は保存しない）、3.1.1（外部ID基盤と連携しない）、
 *   3.1.3 表3-2 #4（トークンはメモリ保持。localStorage・Cookie には置かない）、5.1（bcrypt）
 *
 * トークンの保持場所は実装を見ずに、ログイン後のブラウザの保存領域を外から調べて確認する。
 */
import { expect, test } from "@playwright/test";
import mysql, { type RowDataPacket } from "mysql2/promise";
import { API_URL, E001, dbConfig, expectSc02, loginFromSc01 } from "./support";

test.describe("T-024 パスワード保存", () => {
  test("【正常系】employees.password_hash が bcrypt 形式（$2b$…）で平文でない", async () => {
    const conn = await mysql.createConnection(dbConfig());
    try {
      const [rows] = await conn.query<RowDataPacket[]>(
        "SELECT password_hash FROM employees WHERE employee_id = ?",
        [E001.id],
      );
      expect(rows).toHaveLength(1);
      const hash: string = rows[0].password_hash;
      // bcrypt 形式：$2b$ + コスト2桁 + $ + 53文字（salt 22 + hash 31）＝ 計60文字（2.3.1 VARCHAR(60)）
      expect(hash).toMatch(/^\$2b\$\d{2}\$[./A-Za-z0-9]{53}$/);
      expect(hash).not.toBe(E001.password);
      expect(hash).not.toContain(E001.password);
    } finally {
      await conn.end();
    }
  });

  test("【非機能系】ログイン時に外部ID基盤への通信がない（通信先はフロントと自システムAPIのみ）", async ({ page, baseURL }) => {
    const allowedOrigins = new Set([new URL(baseURL!).origin, new URL(API_URL).origin]);
    const origins = new Set<string>();
    page.on("request", (req) => {
      const url = new URL(req.url());
      if (url.protocol === "http:" || url.protocol === "https:") origins.add(url.origin);
    });

    const resp = await loginFromSc01(page);
    expect(resp.status()).toBe(200);
    await expectSc02(page);

    const unexpected = [...origins].filter((o) => !allowedOrigins.has(o));
    expect(unexpected, `想定外の通信先: ${unexpected.join(", ")}`).toEqual([]);
  });

  test("【非機能系】ログイン後、localStorage・Cookie が空でトークンがブラウザの保存領域にない", async ({ page, context }) => {
    const resp = await loginFromSc01(page);
    const { token } = await resp.json();
    await expectSc02(page);

    // 表3-2 #4：localStorage・Cookie には置かない
    expect(await page.evaluate(() => window.localStorage.length)).toBe(0);
    expect(await context.cookies()).toEqual([]);

    // 表3-2 #4：メモリ（JS変数）に持つ → sessionStorage にも入っていない
    const sessionDump = await page.evaluate(() => JSON.stringify({ ...window.sessionStorage }));
    expect(sessionDump).not.toContain(token);
  });
});
