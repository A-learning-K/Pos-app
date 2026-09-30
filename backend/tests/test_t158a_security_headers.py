"""T-158A SECURITY_HEADERS 5項目の値検証（UT／非機能系）

参照元
- テスト設計書 v2.18 表2-3 T-158A
- 設計仕様書 v2.10 5.2（表5-4 セキュアコーディング：全レスポンスに5項目を付与）

2026-09-29 カバレッジ点検で追加：200/401 のみで、Week4コーディング計画 4節に記録された
「500応答でCORS/セキュリティヘッダーが欠落した」過去の不具合パターンを検証していなかったため、
T-022A と同じ bcrypt 例外モックで 500 応答を発生させ、そのケースも追加した。
"""
import bcrypt
import pytest

from helpers import E001_ID, E001_PASSWORD, EXPECTED_SECURITY_HEADERS, LOGIN_PATH, WRONG_PASSWORD


def _health(client, monkeypatch):
    return client.get("/health")


def _login_failed(client, monkeypatch):
    return client.post(LOGIN_PATH, json={"employee_id": E001_ID, "password": WRONG_PASSWORD})


def _login_500(client, monkeypatch):
    def _raise(*_args, **_kwargs):
        raise ValueError("Invalid salt")

    # security.py は `import bcrypt` → `bcrypt.checkpw(...)` で呼ぶため、モジュール属性を差し替える（T-022Aと同じ手法）
    monkeypatch.setattr(bcrypt, "checkpw", _raise)
    return client.post(LOGIN_PATH, json={"employee_id": E001_ID, "password": E001_PASSWORD})


@pytest.mark.parametrize(
    "call",
    [
        pytest.param(_health, id="200応答_health"),
        pytest.param(_login_failed, id="401応答_ログイン失敗"),
        pytest.param(_login_500, id="500応答_bcrypt例外"),
    ],
)
@pytest.mark.parametrize("header_name", list(EXPECTED_SECURITY_HEADERS))
def test_T158A_セキュリティヘッダーが正確な値で付与される(client, call, header_name, monkeypatch):
    resp = call(client, monkeypatch)

    assert resp.headers.get(header_name) == EXPECTED_SECURITY_HEADERS[header_name]
