"""FG-05 会計処理: 値引き・消費税の計算ロジック。

設計仕様書 2.5（計算ルール）・3.5（FG-05）に対応する。
A-06 (POST /cart/preview) と将来のA-07 (POST /transactions) は同じこの関数を使う想定
（A-07・取引保存は今回のスコープ外。設計仕様書3.6参照）。

このファイルはAI駆動で実装した部分（今回のスコープ決定：計算ロジックはAIが実装）。
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import ROUND_DOWN, Decimal

from sqlalchemy.orm import Session

from app.models import DiscountCampaign, Member, Product, TaxRate


class ValidationError(Exception):
    """400 VALIDATION_ERROR に対応する（数量範囲外・同一コードの重複行など）。"""


class TaxRateNotConfigured(Exception):
    """税率マスタ未整備。500 INTERNAL_ERROR に対応する（設計仕様書2.5 表2-12）。"""


@dataclass
class LineIn:
    product_code: str
    quantity: int


@dataclass
class LineOut:
    line_no: int
    product_code: str
    name: str
    quantity: int
    unit_price: int
    discount_amount: int
    campaign_id: int | None
    line_subtotal: int


@dataclass
class CalcError:
    product_code: str
    code: str


@dataclass
class CalcResult:
    lines: list[LineOut]
    subtotal_excl_tax: int
    discount_total: int
    tax_rate: Decimal
    tax_amount: int
    total_incl_tax: int
    member: dict | None
    errors: list[CalcError] = field(default_factory=list)


def _select_tax_rate(db: Session, at: date) -> Decimal:
    """税率の選び方（表2-12）: effective_from <= 取引日 のうち最新の1件。"""
    row = (
        db.query(TaxRate)
        .filter(TaxRate.effective_from <= at)
        .order_by(TaxRate.effective_from.desc())
        .first()
    )
    if row is None:
        raise TaxRateNotConfigured("税率マスタが未整備です（設計仕様書2.5 表2-12）")
    return Decimal(str(row.rate))


def _best_campaign_discount(
    db: Session, product_code: str, at: date, pre_discount: int, quantity: int
) -> tuple[int, int | None]:
    """適用企画の選び方（表2-12）: 期間内の企画のうち値引き額最大の1件。

    同額なら campaign_id が小さい方。併用しない。
    """
    candidates = (
        db.query(DiscountCampaign)
        .filter(
            DiscountCampaign.product_code == product_code,
            DiscountCampaign.start_date <= at,
            DiscountCampaign.end_date >= at,
        )
        .all()
    )

    best_amount = 0
    best_campaign_id: int | None = None
    for c in candidates:
        if c.discount_type == "RATE":
            amount = (pre_discount * c.discount_value) // 100  # 円未満切り捨て
        else:  # AMOUNT
            amount = c.discount_value * quantity
        amount = min(amount, pre_discount)  # 値引き前金額を上限とする

        if best_campaign_id is None:
            best_amount, best_campaign_id = amount, c.campaign_id
        elif amount > best_amount:
            best_amount, best_campaign_id = amount, c.campaign_id
        elif amount == best_amount and c.campaign_id < best_campaign_id:
            best_campaign_id = c.campaign_id

    return best_amount, best_campaign_id


def calculate(
    db: Session,
    member_id: str | None,
    lines: list[LineIn],
    at: datetime | date,
) -> CalcResult:
    """設計仕様書2.5 表2-11の手順1〜6を実行する。"""
    txn_date = at.date() if isinstance(at, datetime) else at

    # 入力検証（4.3 A-06: 400 VALIDATION_ERROR）
    seen_codes: set[str] = set()
    for line in lines:
        if not (1 <= line.quantity <= 99):
            raise ValidationError(f"quantity out of range (1-99): {line.product_code}")
        if line.product_code in seen_codes:
            raise ValidationError(f"duplicate product_code in lines: {line.product_code}")
        seen_codes.add(line.product_code)

    # 会員判定（表2-12）: member_idが非nullかつmembersに存在するときだけ値引きを計算する
    member_row = db.get(Member, member_id) if member_id else None
    member_applies = member_row is not None

    errors: list[CalcError] = []
    out_lines: list[LineOut] = []
    line_no = 0

    for line in lines:
        product = db.get(Product, line.product_code)
        if product is None:
            errors.append(CalcError(product_code=line.product_code, code="PRODUCT_NOT_FOUND"))
            continue

        line_no += 1
        # 手順1: 行の値引き前金額
        pre_discount = product.unit_price * line.quantity

        # 手順2: 値引き額（会員あり かつ 適用期間内の企画がある行のみ）
        discount_amount = 0
        campaign_id = None
        if member_applies:
            discount_amount, campaign_id = _best_campaign_discount(
                db, line.product_code, txn_date, pre_discount, line.quantity
            )

        # 手順3: 行小計
        line_subtotal = pre_discount - discount_amount

        out_lines.append(
            LineOut(
                line_no=line_no,
                product_code=line.product_code,
                name=product.name,
                quantity=line.quantity,
                unit_price=product.unit_price,
                discount_amount=discount_amount,
                campaign_id=campaign_id,
                line_subtotal=line_subtotal,
            )
        )

    # 手順4: 税抜合計・値引き合計
    subtotal_excl_tax = sum(l.line_subtotal for l in out_lines)
    discount_total = sum(l.discount_amount for l in out_lines)

    # 手順5: 税額（税抜合計 × 税率 ÷ 100、円未満切り捨て、取引で1回だけ）
    tax_rate = _select_tax_rate(db, txn_date)
    tax_amount = int(
        (Decimal(subtotal_excl_tax) * tax_rate / Decimal(100)).to_integral_value(
            rounding=ROUND_DOWN
        )
    )

    # 手順6: 税込合計
    total_incl_tax = subtotal_excl_tax + tax_amount

    member_out = None
    if member_row is not None:
        member_out = {"member_id": member_row.member_id, "name": member_row.name}

    return CalcResult(
        lines=out_lines,
        subtotal_excl_tax=subtotal_excl_tax,
        discount_total=discount_total,
        tax_rate=tax_rate,
        tax_amount=tax_amount,
        total_incl_tax=total_incl_tax,
        member=member_out,
        errors=errors,
    )
