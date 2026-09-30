"""T-022 A-01 ログインAPI（UT／正常系・異常系）

参照元
- テスト設計書 v2.18 表2-1 T-022
- 設計仕様書 v2.10 4.3 A-01（表4-3）、2.3.2 auth_tokens（表2-3）、3.1.3（表3-2 #2）、4.4（表4-12）
"""
import re
from datetime import datetime, timedelta

import pytest

from app.models import AuthToken
from helpers import (
    E001_ID,
    E001_NAME,
    E001_PASSWORD,
    ID_21_CHARS,
    LOGIN_PATH,
    VALIDATION_ERROR,
    api_error,
    sha256_hex,
)


def _login(client, employee_id=E001_ID, password=E001_PASSWORD):
    return client.post(LOGIN_PATH, json={"employee_id": employee_id, "password": password})


# ---------------------------------------------------------------- 正常系
def test_T022_正常_200とtokenが返る(client):
    resp = _login(client)

    assert resp.status_code == 200
    body = resp.json()
    # 表4-3：応答200 は token / expires_at / employee の3項目
    assert set(body.keys()) == {"token", "expires_at", "employee"}
    assert isinstance(body["token"], str) and body["token"]
    # 表4-3：employee は {employee_id, name, is_admin}（password_hash を含まない）
    assert body["employee"] == {"employee_id": E001_ID, "name": E001_NAME, "is_admin": False}


def test_T022_正常_auth_tokensにSHA256ハッシュだけが保存される(client, seeded_db):
    token = _login(client).json()["token"]

    seeded_db.expire_all()
    rows = seeded_db.query(AuthToken).all()
    assert len(rows) == 1
    row = rows[0]
    # 表2-3：token_hash＝SHA-256（16進 64文字）。生のトークンは保存しない
    assert re.fullmatch(r"[0-9a-f]{64}", row.token_hash)
    assert row.token_hash == sha256_hex(token)
    assert row.token_hash != token
    assert row.employee_id == E001_ID


def test_T022_正常_expires_atは発行から12時間後(client, seeded_db):
    body = _login(client).json()

    seeded_db.expire_all()
    row = seeded_db.query(AuthToken).one()
    # 表2-3・表3-2 #2：有効期限＝発行＋12時間
    assert row.expires_at - row.issued_at == timedelta(hours=12)
    # 応答の expires_at も DB と同じ時刻を指す（タイムゾーン表記の有無は比較対象外）
    resp_expires = datetime.fromisoformat(body["expires_at"]).replace(tzinfo=None)
    assert resp_expires == row.expires_at


# ---------------------------------------------------------------- 異常系
@pytest.mark.parametrize(
    ("employee_id", "password"),
    [
        pytest.param("", E001_PASSWORD, id="ID空欄"),
        pytest.param(E001_ID, "", id="パスワード空欄"),
        pytest.param(ID_21_CHARS, E001_PASSWORD, id="ID21文字"),
    ],
)
def test_T022_異常_入力不正は400(client, seeded_db, employee_id, password):
    resp = _login(client, employee_id, password)

    # T-022：400。表4-12：400 は VALIDATION_ERROR
    assert resp.status_code == 400
    assert api_error(resp)["code"] == VALIDATION_ERROR
    # 失敗時はトークンを発行しない
    seeded_db.expire_all()
    assert seeded_db.query(AuthToken).count() == 0
