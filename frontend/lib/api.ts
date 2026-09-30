/**
 * バックエンドAPIの呼び出し。設計仕様書 4章（API設計）に対応する。
 * すべて同期（await して応答を待ってから画面を更新する）。設計方針#3。
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export type ProductOut = {
  product_code: string;
  name: string;
  unit_price: number;
};

export type CartLineIn = {
  product_code: string;
  quantity: number;
};

export type CartLineOut = {
  line_no: number;
  product_code: string;
  name: string;
  quantity: number;
  unit_price: number;
  discount_amount: number;
  campaign_id: number | null;
  line_subtotal: number;
};

export type CartError = { product_code: string; code: string };

export type CartPreviewResponse = {
  lines: CartLineOut[];
  subtotal_excl_tax: number;
  discount_total: number;
  tax_rate: string;
  tax_amount: number;
  total_incl_tax: number;
  member: { member_id: string; name: string } | null;
  errors: CartError[];
};

export type Employee = { employee_id: string; name: string; is_admin: boolean };

class ApiError extends Error {
  code: string;
  status: number;
  errorId?: string; // N3: 500のときだけ入る
  occurredAt?: string;
  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

// トークンはメモリ（JS変数）だけに持つ。localStorage・Cookieには置かない（表3-2 #4）。
// ページを再読み込み・タブを閉じたら再ログインになる。
let authToken: string | null = null;
let currentEmployee: Employee | null = null;

export function getCurrentEmployee(): Employee | null {
  return currentEmployee;
}

function authHeaders(): HeadersInit {
  return authToken ? { Authorization: `Bearer ${authToken}` } : {};
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = body.detail ?? body;
    const err = new ApiError(res.status, detail?.code ?? "UNKNOWN", detail?.message ?? res.statusText);
    err.errorId = detail?.error_id;
    err.occurredAt = detail?.occurred_at;
    throw err;
  }
  return res.json();
}

/** A-01 POST /auth/login（FG-01） */
export async function login(employeeId: string, password: string): Promise<Employee> {
  const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ employee_id: employeeId, password }),
  });
  const body = await handleResponse<{ token: string; expires_at: string; employee: Employee }>(res);
  authToken = body.token;
  currentEmployee = body.employee;
  return body.employee;
}

/** A-02 POST /auth/logout（失敗してもメモリ上のトークンは消す） */
export async function logout(): Promise<void> {
  try {
    await fetch(`${API_BASE}/api/v1/auth/logout`, { method: "POST", headers: authHeaders() });
  } finally {
    authToken = null;
    currentEmployee = null;
  }
}

/** A-04 GET /products/{product_code}（FG-08 商品検索） */
export async function fetchProduct(productCode: string): Promise<ProductOut> {
  const res = await fetch(`${API_BASE}/api/v1/products/${productCode}`, {
    headers: authHeaders(),
  });
  return handleResponse<ProductOut>(res);
}

/** A-06 POST /cart/preview（FG-03〜05 金額計算・保存しない） */
export async function previewCart(
  memberId: string | null,
  lines: CartLineIn[]
): Promise<CartPreviewResponse> {
  const res = await fetch(`${API_BASE}/api/v1/cart/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ member_id: memberId, lines }),
  });
  return handleResponse<CartPreviewResponse>(res);
}

export { ApiError };
