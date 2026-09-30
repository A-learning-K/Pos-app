/**
 * T-012 担当者表示（UT／正常系）
 *
 * 参照元
 * - テスト設計書 v2.18 表2-1 T-012：ログイン後のヘッダにログイン中の担当者ID・氏名が表示される
 *   （代表値：担当者ID＝E001、氏名＝山田太郎。db/seed.sql の一般担当者と一致）
 * - 設計仕様書 v2.10 3.3.4 表3-9 #1 担当者表示「ログイン中の担当者ID・氏名」、3.1.1
 * - テスト設計書 1.1 / 1.7：外部依存（API）は遮断し、固定の値を返すモックを使う
 *
 * 画面の実装は参照せず、lib/api.ts の外形（getCurrentEmployee(): Employee | null）だけを使ってモックする。
 * 画面側の依存箇所（import パス）はこのファイル冒頭の2か所だけ。
 *
 * 2026-09-30 追記（バグ管理表 BUG-006）：未ログイン（getCurrentEmployee()がnull）の分岐は
 * これまで一度もテストされておらず、/posへの未認証アクセスを弾けない実装バグがUTでは検出できなかった。
 * 再発防止のため、未ログイン時に/loginへリダイレクトされることを検証するケースを追加した。
 */
import { render, screen, waitFor } from "@testing-library/react";
import PosPage from "@/app/pos/page";
import * as api from "@/lib/api";

const E001 = { employee_id: "E001", name: "山田太郎", is_admin: false };

// lib/api：ログイン済みの状態（メモリ上に担当者がいる）を再現する
jest.mock("@/lib/api", () => ({
  getCurrentEmployee: jest.fn(),
  logout: jest.fn().mockResolvedValue(undefined),
  login: jest.fn(),
}));

// Next.js のルーター（画面遷移）は UT では動かさない
const mockPush = jest.fn();
const mockReplace = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace, back: jest.fn(), prefetch: jest.fn() }),
  usePathname: () => "/pos",
  useSearchParams: () => new URLSearchParams(),
  redirect: jest.fn(),
}));

describe("T-012 担当者表示", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.getCurrentEmployee as jest.Mock).mockReturnValue(E001);
    // 実通信が起きないことの保険（呼ばれたら失敗させる）
    global.fetch = jest.fn(() => Promise.reject(new Error("UTで実通信は行わない"))) as jest.Mock;
  });

  test("【正常系】ログイン中の担当者ID（E001）が表示される", async () => {
    render(<PosPage />);
    expect(await screen.findByText(/E001/)).toBeInTheDocument();
  });

  test("【正常系】ログイン中の担当者の氏名（山田太郎）が表示される", async () => {
    render(<PosPage />);
    expect(await screen.findByText(/山田太郎/)).toBeInTheDocument();
  });
});

describe("未ログイン時のアクセス制御（BUG-006再発防止）", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.getCurrentEmployee as jest.Mock).mockReturnValue(null);
    global.fetch = jest.fn(() => Promise.reject(new Error("UTで実通信は行わない"))) as jest.Mock;
  });

  test("【異常系】担当者情報が無ければ /login へリダイレクトされる", async () => {
    render(<PosPage />);
    await waitFor(() => expect(mockReplace).toHaveBeenCalledWith("/login"));
  });

  test("【異常系】担当者情報が無ければ画面本体（ログイン成功メッセージ）は描画されない", () => {
    render(<PosPage />);
    expect(screen.queryByText(/ログインできました/)).not.toBeInTheDocument();
  });
});
