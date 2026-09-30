"""監査ログ（設計仕様書 表2-16・表5-7）。

外枠（呼び出し口・出力先）はAIが作成。何をどう記録するかは自分で決める（Week4計画 11節）。
出力先は標準出力のロガー "audit"。App Service 上では Azure Monitor Logs 側で収集する想定。
"""
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger("audit")
JST = timezone(timedelta(hours=9))


def log_event(action: str, employee_id: str | None, target_id: str | None = None) -> None:
    """監査イベントを1件記録する。

    action      : 操作種別（今回の呼び出し元は LOGIN_SUCCESS / LOGIN_FAILURE の2つ）
    employee_id : 担当者ID（ログイン失敗時は入力されたID）
    target_id   : 対象ID（ログインでは無し）
    """
    occurred_at = datetime.now(JST).isoformat(timespec="seconds")

    # TODO(自分で書く): 記録する項目と文言を決め、logger.info(...) の1行で出力する
    #   表2-16「日時・担当者ID・操作種別・対象ID」。個人情報（パスワード等）は出さない。
    #   書くまでは何も記録されない（ログイン自体は止めない）。
    logger.info("Occurred_at: %s action:%s employee_id:%s target_id:%s", occurred_at, action, employee_id, target_id)
