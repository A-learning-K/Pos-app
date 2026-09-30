"""T-064A verify_token() の期限切れ判定（UT／準正常系・個別関数レベル）

参照元
- テスト設計書 v2.18 表2-3 T-064A
- 設計仕様書 v2.10 4.5（表4-13 #2・#3）、2.3.2、4.4（表4-12 TOKEN_INVALID）

DB は使わず、Session をモックして固定データ（行はあるが expires_at＝2000-01-01T00:00:00）を返す。
モック対象・呼び出し方は 関数外形サマリ（verify_token(token, db) -> CurrentEmployee）による。
"""
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import AuthToken, Employee
from app.security import CurrentEmployee, verify_token
from helpers import E001_ID, E001_NAME, TOKEN_INVALID, sha256_hex

RAW_TOKEN = "fixed-test-token"
EXPIRED_AT = datetime(2000, 1, 1, 0, 0, 0)     # T-064A：現在より過去の固定値
NOT_EXPIRED_AT = datetime(2999, 1, 1, 0, 0, 0)  # 対照用：現在より未来の固定値


def _mock_db(expires_at: datetime):
    row = AuthToken(
        token_hash=sha256_hex(RAW_TOKEN),
        employee_id=E001_ID,
        issued_at=datetime(1999, 12, 31, 12, 0, 0),
        expires_at=expires_at,
    )
    employee = Employee(employee_id=E001_ID, name=E001_NAME, password_hash="x" * 60, is_admin=False)

    db = MagicMock(spec=Session)
    db.get.side_effect = lambda model, key: {AuthToken: row, Employee: employee}.get(model)
    return db, row


def test_T064A_期限切れの行は無効と判定され401_TOKEN_INVALID():
    db, row = _mock_db(EXPIRED_AT)

    with pytest.raises(HTTPException) as exc_info:
        verify_token(RAW_TOKEN, db)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["code"] == TOKEN_INVALID
    # 4.5 #2：受け取ったトークンを SHA-256 でハッシュして主キー検索する
    db.get.assert_any_call(AuthToken, sha256_hex(RAW_TOKEN))
    # 4.5 #3：期限切れ行は削除する
    db.delete.assert_called_once_with(row)


def test_T064A_対照_期限内の行は有効と判定され担当者が返る():
    # 期限切れ判定が「常に無効」になっていないことの対照
    db, _ = _mock_db(NOT_EXPIRED_AT)

    result = verify_token(RAW_TOKEN, db)

    # 4.5 #4：employee_id を取り出して以降の処理に渡す
    assert isinstance(result, CurrentEmployee)
    assert result.employee_id == E001_ID
    db.delete.assert_not_called()
