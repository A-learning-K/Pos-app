"""pytest 共通設定（Week5 単体テスト：FG-01＋N2/N3）。

方針（テスト設計書 1.1・1.4・1.6）
- 外部依存（Azure MySQL）は遮断し、テストごとに作り直すインメモリ SQLite を使う。
  → 各テストは独立して実行でき、実DBを壊さない。
- 期待値は設計仕様書・テスト設計書から引く（helpers.py に定数としてまとめる）。
"""
import os

# app.database は import 時に engine を作るため、import より前に設定する。
# 実DB（Azure）へ誤って接続しないよう、ここでは必ず SQLite を指す（接続はしない）。
os.environ["DATABASE_URL"] = "sqlite://"
os.environ.setdefault("DISABLE_AUTH", "true")  # 認証が要るテストは auth_enabled フィクスチャで個別に有効化

import bcrypt  # noqa: E402
import pytest  # noqa: E402
from fastapi import Depends  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app import security  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Employee  # noqa: E402
from helpers import E001_ID, E001_NAME, E001_PASSWORD, PROTECTED_PATH  # noqa: E402

# --- 認証付きAPIの代役（テスト専用ルート） -----------------------------------------
# 設計仕様書 4.5「A-01 以外の全エンドポイントに Depends(get_current_employee) を付与」。
# Week5 時点で有効なルーターは auth のみで、認証必須の業務APIが存在しない（Week4計画 1節）。
# T-064「トークンで API を呼ぶと 401」を確かめるため、4.5 の共通処理だけを付けた
# 最小のルートをテスト時のみ追加する（本番コードには追加しない）。
@app.get(PROTECTED_PATH)
def _protected_probe(current: security.CurrentEmployee = Depends(security.get_current_employee)):
    return {"employee_id": current.employee_id}


# --- DB ----------------------------------------------------------------------------
@pytest.fixture
def db_session():
    """テストごとに空のDBを作り、終わったら捨てる（テスト間で状態を共有しない）。"""
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autocommit=False, autoflush=False)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def seeded_db(db_session):
    """一般担当者 E001（db/seed.sql と同じID・氏名）。
    テスト設計書 T-022：平文 Passw0rd1 をテスト側で bcrypt ハッシュ化して投入する。
    コストは設計仕様書 5.1 の 12。
    """
    db_session.add(
        Employee(
            employee_id=E001_ID,
            name=E001_NAME,
            password_hash=bcrypt.hashpw(E001_PASSWORD.encode(), bcrypt.gensalt(12)).decode(),
            is_admin=False,
        )
    )
    db_session.commit()
    return db_session


@pytest.fixture
def client(seeded_db):
    """アプリの get_db をテスト用セッションに差し替えた TestClient。"""

    def _override_get_db():
        yield seeded_db

    app.dependency_overrides[get_db] = _override_get_db
    # raise_server_exceptions=False：想定外例外は N3 ミドルウェアの 500 応答として観測する
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_enabled(monkeypatch):
    """.env 既定の DISABLE_AUTH=true を、このテストの間だけ無効にする（本来の認証チェックを通す）。"""
    monkeypatch.setattr(security, "DISABLE_AUTH", False)
