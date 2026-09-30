"""DB接続設定。

設計決定記録 #13: 接続プールはSQLAlchemyの既定値のまま、pool_pre_pingのみ有効にする
（pool_size=5, max_overflow=10, pool_timeout=30秒はデフォルトを変更しない）。
"""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

connect_args = {"ssl": {"ssl_disabled": False}}

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # 設計決定記録 #13
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
