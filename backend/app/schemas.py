"""APIの要求・応答スキーマ。設計仕様書 4.3 の各APIの仕様に対応する。"""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# --- A-01 POST /auth/login ---
class LoginRequest(BaseModel):
    employee_id: str = Field(min_length=1, max_length=20)  # 表2-14
    password: str = Field(min_length=1)


class EmployeeOut(BaseModel):
    # password_hash はあえて定義しない（このクラス自体が応答に出す項目の許可リスト）
    employee_id: str
    name: str
    is_admin: bool


class LoginResponse(BaseModel):
    token: str
    expires_at: datetime
    employee: EmployeeOut


# --- A-04 GET /products/{product_code} ---
class ProductOut(BaseModel):
    product_code: str
    name: str
    unit_price: int


# --- A-05 GET /members/{member_id} ---
class MemberOut(BaseModel):
    member_id: str
    name: str


# --- A-06 POST /cart/preview ---
class CartLineIn(BaseModel):
    product_code: str = Field(min_length=13, max_length=13)
    quantity: int = Field(ge=1, le=99)


class CartPreviewRequest(BaseModel):
    member_id: str | None = None
    lines: list[CartLineIn] = Field(default_factory=list)


class CartLineOut(BaseModel):
    line_no: int
    product_code: str
    name: str
    quantity: int
    unit_price: int
    discount_amount: int
    campaign_id: int | None
    line_subtotal: int


class CartErrorOut(BaseModel):
    product_code: str
    code: str


class CartPreviewResponse(BaseModel):
    lines: list[CartLineOut]
    subtotal_excl_tax: int
    discount_total: int
    tax_rate: Decimal
    tax_amount: int
    total_incl_tax: int
    member: MemberOut | None
    errors: list[CartErrorOut]


class ErrorResponse(BaseModel):
    code: str
    message: str
    detail: dict | None = None
