"""A-06 POST /cart/preview（FG-03〜05 の金額計算。保存しない）。設計仕様書 3.5・4.3。"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import calc
from app.database import get_db
from app.schemas import (
    CartErrorOut,
    CartLineOut,
    CartPreviewRequest,
    CartPreviewResponse,
    MemberOut,
)
from app.security import CurrentEmployee, get_current_employee

router = APIRouter(prefix="/api/v1/cart", tags=["cart"])

JST = timezone.utc  # TODO: JSTに変更する場合はここを timezone(timedelta(hours=9)) に


@router.post("/preview", response_model=CartPreviewResponse)
def preview_cart(
    body: CartPreviewRequest,
    db: Session = Depends(get_db),
    _employee: CurrentEmployee = Depends(get_current_employee),
):
    try:
        lines_in = [calc.LineIn(product_code=l.product_code, quantity=l.quantity) for l in body.lines]
        result = calc.calculate(db, body.member_id, lines_in, datetime.now(tz=JST))
    except calc.ValidationError as exc:
        raise HTTPException(
            status_code=400, detail={"code": "VALIDATION_ERROR", "message": str(exc)}
        ) from exc
    except calc.TaxRateNotConfigured as exc:
        raise HTTPException(
            status_code=500, detail={"code": "INTERNAL_ERROR", "message": str(exc)}
        ) from exc

    return CartPreviewResponse(
        lines=[
            CartLineOut(
                line_no=l.line_no,
                product_code=l.product_code,
                name=l.name,
                quantity=l.quantity,
                unit_price=l.unit_price,
                discount_amount=l.discount_amount,
                campaign_id=l.campaign_id,
                line_subtotal=l.line_subtotal,
            )
            for l in result.lines
        ],
        subtotal_excl_tax=result.subtotal_excl_tax,
        discount_total=result.discount_total,
        tax_rate=result.tax_rate,
        tax_amount=result.tax_amount,
        total_incl_tax=result.total_incl_tax,
        member=MemberOut(**result.member) if result.member else None,
        errors=[CartErrorOut(product_code=e.product_code, code=e.code) for e in result.errors],
    )
