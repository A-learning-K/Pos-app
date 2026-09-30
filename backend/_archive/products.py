"""A-04 GET /products/{product_code}（FG-08 商品検索）。設計仕様書 3.8・4.3。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product
from app.schemas import ProductOut
from app.security import CurrentEmployee, get_current_employee

router = APIRouter(prefix="/api/v1/products", tags=["products"])


@router.get("/{product_code}", response_model=ProductOut)
def get_product(
    product_code: str,
    db: Session = Depends(get_db),
    _employee: CurrentEmployee = Depends(get_current_employee),
):
    if len(product_code) != 13 or not product_code.isdigit():
        raise HTTPException(
            status_code=400,
            detail={"code": "VALIDATION_ERROR", "message": "商品コードは13桁の数字で入力してください"},
        )

    product = db.get(Product, product_code)
    if product is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "PRODUCT_NOT_FOUND", "message": "商品がマスタ未登録です"},
        )

    return ProductOut(
        product_code=product.product_code,
        name=product.name,
        unit_price=product.unit_price,
    )
