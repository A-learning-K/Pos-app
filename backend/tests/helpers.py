"""テストで使う期待値・代表値と、応答の読み取りヘルパー。

値はすべて設計書から引いたもの（実装から逆算しない）。各定数に参照元を記す。
"""
import hashlib

# --- 代表値（テスト設計書 v2.18 T-022／T-025） -------------------------------------
E001_ID = "E001"            # db/seed.sql の一般担当者
E001_NAME = "山田太郎"      # T-012 と共通
E001_PASSWORD = "Passw0rd1"
UNKNOWN_ID = "E999"         # T-025 誤ったID（未登録）
WRONG_PASSWORD = "WrongPass1"  # T-025 誤ったパスワード
ID_21_CHARS = "A" * 21      # T-022 上限20文字（設計仕様書 2.3.1 VARCHAR(20)・表2-14）を1文字超える

# --- API（設計仕様書 4.1・4.2） -------------------------------------------------------
LOGIN_PATH = "/api/v1/auth/login"
LOGOUT_PATH = "/api/v1/auth/logout"
PROTECTED_PATH = "/api/v1/__test__/protected"  # conftest.py のテスト専用ルート（4.5 の共通処理のみ）

# --- エラーコード（設計仕様書 4.4 表4-12） --------------------------------------------
VALIDATION_ERROR = "VALIDATION_ERROR"
AUTH_FAILED = "AUTH_FAILED"
TOKEN_INVALID = "TOKEN_INVALID"
INTERNAL_ERROR = "INTERNAL_ERROR"

# --- セキュリティヘッダー（設計仕様書 5.2 表5-4 セキュアコーディング） ---------------
EXPECTED_SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'none'",
    "X-Frame-Options": "DENY",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "same-origin",
}


def sha256_hex(text: str) -> str:
    """設計仕様書 2.3.2：token_hash＝トークンの SHA-256（16進）。"""
    return hashlib.sha256(text.encode()).hexdigest()


def bearer(token: str) -> dict:
    """設計仕様書 4.1：Authorization: Bearer <token>。"""
    return {"Authorization": f"Bearer {token}"}


def api_error(resp) -> dict:
    """エラー応答オブジェクトを取り出す。

    設計仕様書 4.1：エラー応答は {"code", "message", "detail"} をトップレベルに持つ。
    ※ 仕様と実装で形が違う場合はここで検出される（テスト側で実装に合わせて吸収しない）。
      仕様を改版して形を変えた場合は、この関数1か所だけを直す。
    """
    return resp.json()


def error_id_of(err: dict):
    """500 応答のエラーIDを取り出す。

    設計仕様書 4.4 は「発生時刻とエラーIDを表示」、5.5 は「同じ error_id を含む500応答」と
    定めるが、応答JSON内の位置は明記されていない。そのため位置は問わず、
    トップレベル または detail 内のどちらかにあればよいとする。
    """
    if "error_id" in err:
        return err["error_id"]
    detail = err.get("detail")
    if isinstance(detail, dict):
        return detail.get("error_id")
    return None


def occurred_at_of(err: dict):
    if "occurred_at" in err:
        return err["occurred_at"]
    detail = err.get("detail")
    if isinstance(detail, dict):
        return detail.get("occurred_at")
    return None
