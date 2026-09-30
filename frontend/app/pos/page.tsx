"use client";

/**
 * ログイン後の遷移先画面。
 * 2026-09-27：Week5提出に向けたスコープ決定により、スキャン・購入リスト機能（旧pos画面）は
 * frontend/_archive/pos_page_with_scan.tsx に退避した（Week4コーディング計画 参照）。
 * 今回はログイン成功の確認のみを行う。
 *
 * 2026-09-30 T-023で検出（バグ管理表 BUG-006）：未ログイン（トークンがメモリに無い状態）で
 * このURLを直接開いても何も弾かれず画面が表示されてしまっていたため、
 * 設計仕様書 表3-2 #4（トークンはメモリ保持。再読み込み・タブを閉じたら再ログイン）に従い、
 * 未ログインならSC-01（/login）へリダイレクトするガードを追加した。
 */

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getCurrentEmployee, logout } from "@/lib/api";

export default function PosPage() {
  const router = useRouter();
  const employee = getCurrentEmployee();

  useEffect(() => {
    if (!employee) {
      router.replace("/login");
    }
  }, [employee, router]);

  async function handleLogout() {
    await logout();
    router.push("/login");
  }

  if (!employee) {
    // リダイレクト中は何も表示しない（未ログイン状態の画面がちらつくのを防ぐ）
    return null;
  }

  return (
    <main style={{ maxWidth: 360 }}>
      <h1>ログインできました！</h1>
      <p>
        担当: {employee.employee_id} {employee.name}
      </p>
      <button type="button" onClick={handleLogout}>
        ログアウト
      </button>
    </main>
  );
}
