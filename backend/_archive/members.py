"""A-05 GET /members/{member_id}（FG-02 会員照会）。設計仕様書 3.2・4.3。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Member
from app.schemas import MemberOut
from app.security import CurrentEmployee, get_current_employee

router = APIRouter(prefix="/api/v1/members", tags=["members"])


@router.get("/{member_id}", response_model=MemberOut)
def get_member(
    member_id: str,
    db: Session = Depends(get_db),
    _employee: CurrentEmployee = Depends(get_current_employee),
):
    member = db.get(Member, member_id)
    if member is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "MEMBER_NOT_FOUND", "message": "該当会員なし"},
        )

    # 氏名以外の個人情報は返さない（設計仕様書2.6.3・4.3）
    return MemberOut(member_id=member.member_id, name=member.name)
