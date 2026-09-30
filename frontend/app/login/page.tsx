"use client";

/** SC-01 ログイン画面（設計仕様書 3.1.4 表3-3）。 */

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, login } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [employeeId, setEmployeeId] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    // POS画面で401を受けて戻ってきた場合（2.6.3）
    if (new URLSearchParams(window.location.search).get("expired")) {
      setMessage("M-12: ログインの有効期限が切れました。再度ログインしてください");
    }
  }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMessage(null);
    try {
      await login(employeeId, password);
      router.push("/pos");
    } catch (err) {
      // 入力は消さない（表3-3 #4）
      if (err instanceof ApiError && err.code === "AUTH_FAILED") {
        setMessage("M-01: 担当者IDまたはパスワードが違います");
      } else if (err instanceof ApiError) {
        setMessage(`エラー(${err.code}): ${err.message}`);
      } else {
        setMessage("M-11: 通信に失敗しました。もう一度お試しください");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <main style={{ maxWidth: 360 }}>
      <h1>ログイン（SC-01）</h1>
      <form onSubmit={handleSubmit}>
        <p>
          <label>
            担当者ID
            <br />
            <input value={employeeId} onChange={(e) => setEmployeeId(e.target.value)} maxLength={20} required />
          </label>
        </p>
        <p>
          <label>
            パスワード
            <br />
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </label>
        </p>
        <button type="submit" disabled={busy}>
          {busy ? "読み込み中" : "ログイン"}
        </button>
      </form>
      {message && (
        <p role="alert" style={{ color: "crimson" }}>
          {message}
        </p>
      )}
    </main>
  );
}
