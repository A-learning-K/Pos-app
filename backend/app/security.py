"""N1 認証・トークン（設計仕様書 3.1.3・4.5・5.1）。

外枠（DB検索・保存・例外処理）はAIが作成。
`# TODO(自分で書く)` の付いた行（計4か所・各1行）だけ自分で置き換える（Week4計画 11節）。
置き換えるまでは NotImplementedError で止まり、APIは 501 を返す。

DISABLE_AUTH=true（.env既定）の間は認証チェックをスキップする。
4か所を書き終えたら DISABLE_AUTH=false にする。
"""
import hashlib  # noqa: F401  TODOで使う
import os
import secrets  # noqa: F401  TODOで使う
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import bcrypt  # noqa: F401  TODOで使う
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuthToken, Employee

DISABLE_AUTH = os.getenv("DISABLE_AUTH", "true").lower() == "true"
TOKEN_LIFETIME = timedelta(hours=12)  # 表2-3
JST = timezone(timedelta(hours=9))


@dataclass
class CurrentEmployee:
    employee_id: str
    name: str
    is_admin: bool


def _now() -> datetime:
    """DBのDATETIME列（タイムゾーンなし・JST）と比較できる現在時刻。"""
    return datetime.now(JST).replace(tzinfo=None)


def _todo(what: str):
    raise NotImplementedError(f"TODO(security.py): {what} を実装してください")


def _hash_token(token: str) -> str:
    """生のトークン → SHA-256（16進64文字）。発行・検証・ログアウトで共通に使う。"""
   
    # SHA-256オブジェクトを生成
    hash_obj = hashlib.sha256()
    
    # バイト列を渡してハッシュ値を計算
    data = token.encode()
    hash_obj.update(data)
    
    # ハッシュ値を取得 
    hash_obj16 = hash_obj.hexdigest() # 16進数文字列
    return hash_obj16


def authenticate(db: Session, employee_id: str, password: str) -> Employee | None:
    """照合に成功したら Employee、失敗なら None（不在と不一致は区別しない。表3-2 #1）。"""
    employee = db.get(Employee, employee_id)
    if employee is None:
        return None

    # 入力されたパスワードとハッシュをバイト列にエンコード
    password_bytes = password.encode('utf-8')
    hash_bytes = employee.password_hash.encode('utf-8')
    is_match = bcrypt.checkpw(password_bytes, hash_bytes)

    if is_match:
        return employee 
    else:
        return None


def issue_token(db: Session, employee_id: str) -> tuple[str, datetime]:
    """トークンを発行し、ハッシュだけを auth_tokens に保存する（表3-2 #2・#3）。"""
    now = _now()

    # 期限切れ行の掃除（ログイン成功時にまとめて削除）
    db.query(AuthToken).filter(AuthToken.expires_at < now).delete()

    # 32バイトの乱数発生
    token = secrets.token_urlsafe(32)
    
    expires_at = now + TOKEN_LIFETIME
    db.add(
        AuthToken(
            token_hash=_hash_token(token),
            employee_id=employee_id,
            issued_at=now,
            expires_at=expires_at,
        )
    )
    db.commit()
    return token, expires_at

def verify_token(token: str, db: Session) -> CurrentEmployee:
    """設計仕様書 4.5 の手順2〜4。"""
    row = db.get(AuthToken, _hash_token(token))
    now = _now()

    if row is None:
        is_invalid = True
    elif row.expires_at < now:
        is_invalid = True
    else:
        is_invalid = False

    if is_invalid:
        if row is not None:  # 期限切れ行は削除してから401
            db.delete(row)
            db.commit()
        raise HTTPException(
            status_code=401,
            detail={"code": "TOKEN_INVALID", "message": "ログインの有効期限が切れました。再度ログインしてください"},
        )

    employee = db.get(Employee, row.employee_id)
    return CurrentEmployee(
        employee_id=employee.employee_id, name=employee.name, is_admin=employee.is_admin
    )


def revoke_token(db: Session, token: str) -> None:
    """ログアウト（A-02）。既に無効でもエラーにしない。"""
    row = db.get(AuthToken, _hash_token(token))
    if row is not None:
        db.delete(row)
        db.commit()


def bearer_token(authorization: str | None) -> str | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    return authorization.removeprefix("Bearer ").strip() or None


def not_implemented_error(exc: NotImplementedError) -> HTTPException:
    return HTTPException(status_code=501, detail={"code": "NOT_IMPLEMENTED", "message": str(exc)})


def get_current_employee(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> CurrentEmployee:
    """A-01以外のエンドポイントに Depends で付ける共通処理（4.5）。"""
    if DISABLE_AUTH:
        # 開発中の一時措置。本実装ではここを通らない。
        return CurrentEmployee(employee_id="DEV", name="開発用ダミー", is_admin=True)

    token = bearer_token(authorization)
    if token is None:
        raise HTTPException(
            status_code=401,
            detail={"code": "TOKEN_INVALID", "message": "ログインしてください"},
        )
    try:
        return verify_token(token, db)
    except NotImplementedError as exc:
        raise not_implemented_error(exc) from exc
