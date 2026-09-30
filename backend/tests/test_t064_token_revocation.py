"""T-064 トークンの失効（UT／正常系・異常系）

参照元
- テスト設計書 v2.18 表2-1 T-064
- 設計仕様書 v2.10 5.1（表5-3 認証トークン）、4.3 A-02、4.5（表4-13）、4.4（表4-12）、2.3.2

※ 「SC-01 へ戻る」は画面側の確認のため本ファイル（API）では扱わない（ログアウト→SC-01 は Playwright T-079 で確認）。
※ 認証必須の業務APIが Week5 時点で存在しないため、4.5 の共通処理だけを付けたテスト専用ルート
  （conftest.py の PROTECTED_PATH）を「API」として呼ぶ。
"""
from datetime import datetime

import pytest

from app.models import AuthToken
from helpers import (
    E001_ID,
    E001_PASSWORD,
    LOGIN_PATH,
    LOGOUT_PATH,
    PROTECTED_PATH,
    TOKEN_INVALID,
    api_error,
    bearer,
    sha256_hex,
)

EXPIRED_AT = datetime(2000, 1, 1, 0, 0, 0)  # T-064：expires_at を過去の固定値「2000-01-01T00:00:00」に更新

pytestmark = pytest.mark.usefixtures("auth_enabled")


def _login_token(client) -> str:
    resp = client.post(LOGIN_PATH, json={"employee_id": E001_ID, "password": E001_PASSWORD})
    assert resp.status_code == 200
    return resp.json()["token"]


def _assert_token_invalid(resp):
    assert resp.status_code == 401
    assert api_error(resp)["code"] == TOKEN_INVALID


# ---------------------------------------------------------------- 前提確認
def test_T064_前提_有効なトークンなら認証付きAPIを呼べる(client):
    # 以降の 401 が「常に401を返すルート」だから通った、とならないための対照
    token = _login_token(client)
    resp = client.get(PROTECTED_PATH, headers=bearer(token))
    assert resp.status_code == 200
    assert resp.json() == {"employee_id": E001_ID}


# ---------------------------------------------------------------- 正常系
def test_T064_正常_ログアウトでauth_tokensの行が削除される(client, seeded_db):
    token = _login_token(client)
    seeded_db.expire_all()
    assert seeded_db.get(AuthToken, sha256_hex(token)) is not None

    resp = client.post(LOGOUT_PATH, headers=bearer(token))

    assert resp.status_code == 204  # 4.3 A-02
    seeded_db.expire_all()
    assert seeded_db.get(AuthToken, sha256_hex(token)) is None


# ---------------------------------------------------------------- 異常系
def test_T064_異常_ログアウト後のトークンは401_TOKEN_INVALID(client):
    token = _login_token(client)
    assert client.post(LOGOUT_PATH, headers=bearer(token)).status_code == 204

    _assert_token_invalid(client.get(PROTECTED_PATH, headers=bearer(token)))


def test_T064_異常_期限切れのトークンは401_TOKEN_INVALID(client, seeded_db):
    token = _login_token(client)
    seeded_db.expire_all()
    row = seeded_db.get(AuthToken, sha256_hex(token))
    row.expires_at = EXPIRED_AT
    seeded_db.commit()

    _assert_token_invalid(client.get(PROTECTED_PATH, headers=bearer(token)))

    # 4.5 #3：期限切れ行は削除する
    seeded_db.expire_all()
    assert seeded_db.get(AuthToken, sha256_hex(token)) is None


def test_T064_異常_Authorizationヘッダなしは401_TOKEN_INVALID(client):
    _login_token(client)  # 有効なトークンが存在していても、送らなければ401
    _assert_token_invalid(client.get(PROTECTED_PATH))


def test_T064_異常_改ざんトークンは401_TOKEN_INVALID(client):
    token = _login_token(client)
    # T-064：発行済みの有効なトークン文字列の末尾1文字を別の文字に変更
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    assert tampered != token

    _assert_token_invalid(client.get(PROTECTED_PATH, headers=bearer(tampered)))
