"""FastAPIアプリのエントリポイント。

実装済みAPI: A-01/A-02（ログイン・ログアウト）
非機能の外枠: N2 セキュリティヘッダー, N3 エラーID（値・ログ内容は TODO(自分で書く)）

2026-09-27：Week5スコープ決定により、A-04/A-05/A-06関連のルーター（products/members/cart）は
無効化し、backend/_archive/ に退避した（Week4コーディング計画 参照）。
"""
import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.routers import auth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")
JST = timezone(timedelta(hours=9))

app = FastAPI(title="簡易POSアプリ改 Lv2 API", version="0.2.0")


# --- N3 エラーID表示（表4-12 INTERNAL_ERROR・表5-7 サービスデスク） ---
@app.middleware("http")
async def handle_unexpected_error(request: Request, call_next):
    """想定外の例外（500）だけを受け、エラーIDと発生時刻を返す。想定済みエラー（4xx）は通らない。"""
    try:
        return await call_next(request)
    except Exception as exc:
        error_id = str(uuid.uuid4())
        occurred_at = datetime.now(JST).isoformat(timespec="seconds")

        logger.error("error_id:%s occurred_at:%s type:%s message:%s", error_id, occurred_at, type(exc).__name__, exc)
        

        return JSONResponse(
            status_code=500,
            content={
                "code": "INTERNAL_ERROR",
                "message": "通信に失敗しました。もう一度お試しください",
                "detail": {"error_id": error_id, "occurred_at": occurred_at},
            },
        )


# --- N2 セキュリティヘッダー（表5-4 セキュアコーディング） ---
SECURITY_HEADERS: dict[str, str | None] = {
    "Content-Security-Policy": "default-src 'none'",
    "X-Frame-Options": "DENY",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "same-origin",
}


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    for name, value in SECURITY_HEADERS.items():
        if value is not None:
            response.headers[name] = value
    return response


# --- エラー応答形式の統一（設計仕様書 4.1・4.4／バグ管理表 BUG-001・BUG-002） ---
@app.exception_handler(HTTPException)
async def handle_http_exception(request: Request, exc: HTTPException):
    """HTTPException(detail={...}) の既定応答 {"detail": {...}} を、
    設計仕様書 4.1 の {"code","message","detail"}（トップレベル）に整形する。"""
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail:
        code = detail.get("code")
        message = detail.get("message", "")
        extra = {k: v for k, v in detail.items() if k not in ("code", "message")}
        body = {"code": code, "message": message, "detail": extra or None}
    else:
        body = {"code": "HTTP_ERROR", "message": str(detail), "detail": None}
    return JSONResponse(status_code=exc.status_code, content=body)


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    """入力値の検証エラーを、FastAPI既定の422ではなく設計仕様書 4.4 の
    400 VALIDATION_ERROR に変換する。"""
    return JSONResponse(
        status_code=400,
        content={
            "code": "VALIDATION_ERROR",
            "message": "入力内容を確認してください",
            "detail": exc.errors(),
        },
    )


# CORSは最後に追加する（最後に追加したものが最も外側になり、500応答にもCORSヘッダーが付く）。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)


@app.get("/health")
def health():
    return {"status": "ok"}
