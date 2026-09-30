"""T-025 ログイン失敗・ロックアウトなし（UT／異常系）

参照元
- テスト設計書 v2.18 表2-1 T-025
- 設計仕様書 v2.10 3.1.1、3.1.3（表3-2 #1・#6）、4.3 A-01（表4-3）、4.4（表4-12）、5.1（表5-3 ロックアウト）

※ T-025 のうち「画面は M-01 で入力を消さない」は画面側の確認のため、本ファイル（API）では扱わない。
"""
import pytest

from app.models import AuthToken
from helpers import (
    AUTH_FAILED,
    E001_ID,
    E001_PASSWORD,
    LOGIN_PATH,
    UNKNOWN_ID,
    WRONG_PASSWORD,
    api_error,
)


def _login(client, employee_id, password):
    return client.post(LOGIN_PATH, json={"employee_id": employee_id, "password": password})


@pytest.mark.parametrize(
    ("employee_id", "password"),
    [
        pytest.param(UNKNOWN_ID, E001_PASSWORD, id="誤ったID_E999"),
        pytest.param(E001_ID, WRONG_PASSWORD, id="誤ったパスワード_WrongPass1"),
    ],
)
def test_T025_異常_401_AUTH_FAILED(client, seeded_db, employee_id, password):
    resp = _login(client, employee_id, password)

    assert resp.status_code == 401
    assert api_error(resp)["code"] == AUTH_FAILED
    seeded_db.expire_all()
    assert seeded_db.query(AuthToken).count() == 0


def test_T025_異常_ID不在とパスワード不一致は同じ応答(client):
    # 表3-2 #1・表4-3：担当者不在とパスワード不一致は区別せず同じエラー
    r_unknown = _login(client, UNKNOWN_ID, E001_PASSWORD)
    r_wrong_pw = _login(client, E001_ID, WRONG_PASSWORD)

    assert r_unknown.status_code == r_wrong_pw.status_code == 401
    assert r_unknown.json() == r_wrong_pw.json()


def test_T025_異常_5回連続失敗後も正しい値でログインできる(client):
    # 表3-2 #6・表5-3：ロックアウト（失敗回数制限）は設けない
    for _ in range(5):
        assert _login(client, E001_ID, WRONG_PASSWORD).status_code == 401

    resp = _login(client, E001_ID, E001_PASSWORD)
    assert resp.status_code == 200
    assert resp.json()["token"]
