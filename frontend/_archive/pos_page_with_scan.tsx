"use client";

/**
 * SC-02 POSレジ画面（設計仕様書 3.3.4 表3-9）。
 * 今回のスコープは「スキャン→購入リストに追加→合計金額を表示」の1本のチェーンのみ（Week4計画 1節）。
 * 会員ID(FG-02)・行操作(FG-04)・購入確定(FG-06)・マスタ管理(FG-07)はスコープ外。
 *
 * ログインしていなくても開ける。バックエンドが DISABLE_AUTH=false のときは
 * APIが401を返すので、そこでログイン画面へ戻す（表2-16「401の扱い」）。
 */

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import CartList from "@/components/CartList";
import ScanArea from "@/components/ScanArea";
import {
  ApiError,
  CartLineIn,
  CartPreviewResponse,
  getCurrentEmployee,
  logout,
  previewCart,
} from "@/lib/api";

const CODE_PATTERN = /^\d{13}$/;
const MAX_QUANTITY = 99;

export default function PosPage() {
  const router = useRouter();
  const employee = getCurrentEmployee();

  // 購入リストのブラウザ側の状態は lines のみ（3.3.2）。表示は preview（A-06の応答）を使う。
  const linesRef = useRef<CartLineIn[]>([]);
  const [preview, setPreview] = useState<CartPreviewResponse | null>(null);
  const [codeInput, setCodeInput] = useState("");
  const [highlightCode, setHighlightCode] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  /** 手入力とスキャンで共通の追加処理（表3-8 #4〜#7・#9） */
  async function handleAddProductCode(code: string) {
    if (!CODE_PATTERN.test(code)) {
      setMessage("M-09: 商品コードは13桁の数字で入力してください");
      return;
    }

    const lines = linesRef.current;
    const existing = lines.find((l) => l.product_code === code);
    if (existing && existing.quantity >= MAX_QUANTITY) {
      setMessage("M-05: 数量は99までです");
      return;
    }
    const nextLines: CartLineIn[] = existing
      ? lines.map((l) => (l.product_code === code ? { ...l, quantity: l.quantity + 1 } : l))
      : [...lines, { product_code: code, quantity: 1 }];

    setBusy(true);
    try {
      const result = await previewCart(null, nextLines); // 会員IDはスコープ外のため常にnull

      // 未登録コードは購入リストから除く（A-06応答の errors）
      const notFound = new Set(result.errors.map((e) => e.product_code));
      linesRef.current = nextLines.filter((l) => !notFound.has(l.product_code));
      setPreview(result);
      setCodeInput("");

      if (notFound.size > 0) {
        setMessage("M-02: 商品がマスタ未登録です");
      } else {
        setMessage("M-16: 追加しました");
        setHighlightCode(code);
        setTimeout(() => setHighlightCode((c) => (c === code ? null : c)), 2000);
      }
    } catch (e) {
      handleError(e);
    } finally {
      setBusy(false);
    }
  }

  function handleError(e: unknown) {
    if (!(e instanceof ApiError)) {
      setMessage("M-11: 通信に失敗しました。もう一度お試しください");
    } else if (e.status === 401) {
      goLoginExpired();
    } else if (e.code === "INTERNAL_ERROR") {
      // N3: 発生時刻とエラーIDを表示（M-11）
      setMessage(`M-11: ${e.message}（${e.occurredAt ?? "-"} / ${e.errorId ?? "-"}）`);
    } else {
      setMessage(`エラー(${e.code}): ${e.message}`);
    }
  }

  function goLoginExpired() {
    // 購入リストは失われる（2.6.3）
    linesRef.current = [];
    setPreview(null);
    router.push("/login?expired=1");
  }

  async function handleLogout() {
    await logout();
    router.push("/login");
  }

  return (
    <main>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>POSレジ画面（SC-02）</h1>
        <div>
          {employee ? `担当: ${employee.employee_id} ${employee.name}` : "未ログイン（開発モード）"}
          {employee && (
            <button type="button" onClick={handleLogout} style={{ marginLeft: 8 }}>
              ログアウト
            </button>
          )}
        </div>
      </header>

      <section style={{ marginBottom: 24 }}>
        <h2>① バーコードスキャン</h2>
        <ScanArea onDetected={handleAddProductCode} disabled={busy} />
        <div style={{ marginTop: 8 }}>
          <input
            value={codeInput}
            onChange={(e) => setCodeInput(e.target.value)}
            placeholder="13桁の商品コード（手入力）"
            maxLength={13}
            disabled={busy}
          />
          <button
            type="button"
            onClick={() => handleAddProductCode(codeInput)}
            disabled={busy}
            style={{ marginLeft: 8 }}
          >
            {busy ? "読み込み中" : "追加"}
          </button>
        </div>
      </section>

      <section style={{ marginBottom: 24 }}>
        <h2>② 購入リスト・合計</h2>
        <CartList preview={preview} highlightCode={highlightCode} />
      </section>

      {message && <p role="status">{message}</p>}
    </main>
  );
}
