"""A-01 POST /auth/login・A-02 POST /auth/logout（FG-01）。設計仕様書 3.1・4.3。"""
from fastapi import APIRouter, Depends, Header, HTTPException, Response
from sqlalchemy.orm import Session

from app import audit, security
from app.database import get_db
from app.schemas import EmployeeOut, ErrorResponse, LoginRequest, LoginResponse

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse, responses={401: {"model": ErrorResponse}})
def login(body: LoginRequest, db: Session = Depends(get_db)):
    try:
        employee = security.authenticate(db, body.employee_id, body.password)
        if employee is None:
            audit.log_event("LOGIN_FAILURE", body.employee_id)
            raise HTTPException(
                status_code=401,
                detail={"code": "AUTH_FAILED", "message": "担当者IDまたはパスワードが違います"},
            )
        token, expires_at = security.issue_token(db, employee.employee_id)
    except NotImplementedError as exc:
        raise security.not_implemented_error(exc) from exc

    audit.log_event("LOGIN_SUCCESS", employee.employee_id)

    # 応答に出す項目を1つずつ明示的にコピーする（password_hash を混入させない）
    return LoginResponse(
        token=token,
        expires_at=expires_at,
        employee=EmployeeOut(
            employee_id=employee.employee_id, name=employee.name, is_admin=employee.is_admin
        ),
    )


@router.post("/logout", status_code=204)
def logout(authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    """トークンが既に無効・未指定でも 204（4.3 A-02）。"""
    token = security.bearer_token(authorization)
    if token is not None:
        try:
            security.revoke_token(db, token)
        except NotImplementedError as exc:
            raise security.not_implemented_error(exc) from exc
    return Response(status_code=204)
