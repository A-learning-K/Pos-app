"""T-022A authenticate() 内の bcrypt 例外を N3 が捕捉する（UT／異常系）

参照元
- テスト設計書 v2.18 表2-3 T-022A
- 設計仕様書 v2.10 4.4（表4-12 500 INTERNAL_ERROR）、4.1（日時は ISO 8601・JST）、5.5（表5-7 エラー監視）

2026-09-27 にテストデータ不備（不正な password_hash）で実際に起きた事象の再現。
bcrypt.checkpw をモックして ValueError("Invalid salt") を発生させる。
"""
import logging
import uuid
from datetime import datetime, timedelta

import bcrypt
import pytest

from app.models import AuthToken
from helpers import (
    E001_ID,
    E001_PASSWORD,
    INTERNAL_ERROR,
    LOGIN_PATH,
    api_error,
    error_id_of,
    occurred_at_of,
)


@pytest.fixture
def checkpw_raises(monkeypatch):
    def _raise(*_args, **_kwargs):
        raise ValueError("Invalid salt")

    # security.py は `import bcrypt` → `bcrypt.checkpw(...)` で呼ぶため、モジュール属性を差し替える
    monkeypatch.setattr(bcrypt, "checkpw", _raise)


def test_T022A_bcrypt例外は500_INTERNAL_ERRORとerror_idを返す(client, seeded_db, checkpw_raises, caplog):
    caplog.set_level(logging.ERROR)

    resp = client.post(LOGIN_PATH, json={"employee_id": E001_ID, "password": E001_PASSWORD})

    # 表4-12：予期しない例外は 500 INTERNAL_ERROR
    assert resp.status_code == 500
    err = api_error(resp)
    assert err["code"] == INTERNAL_ERROR

    # 表5-7：error_id は UUID
    error_id = error_id_of(err)
    assert error_id is not None, "応答に error_id がない"
    uuid.UUID(error_id)  # UUID 形式でなければ ValueError

    # 表4-12：発生時刻も返す。4.1：日時は ISO 8601（JST）
    occurred_at = occurred_at_of(err)
    assert occurred_at is not None, "応答に発生時刻がない"
    assert datetime.fromisoformat(occurred_at).utcoffset() == timedelta(hours=9)

    # 表5-7：同じ error_id をサーバーログにも記録する（問い合わせ時にIDでログを引けること）
    assert any(error_id in rec.getMessage() for rec in caplog.records if rec.levelno >= logging.ERROR)

    # 認証に失敗しているのでトークンは発行されない
    seeded_db.expire_all()
    assert seeded_db.query(AuthToken).count() == 0

