/**
 * 購入リストと合計欄（設計仕様書 3.4.4 表3-11 ⑩⑫）。A-06 の応答をそのまま表示するだけで、計算はしない。
 * 行選択・数量変更・削除（FG-04）は今回スコープ外。
 */

import { CartPreviewResponse } from "@/lib/api";

type Props = {
  preview: CartPreviewResponse | null;
  highlightCode: string | null; // 追加・加算した行（2秒ハイライト、表3-8 #6）
};

export default function CartList({ preview, highlightCode }: Props) {
  return (
    <>
      <table border={1} cellPadding={6} style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead>
          <tr>
            <th>名称</th>
            <th>数量</th>
            <th>税抜単価</th>
            <th>値引き額</th>
            <th>小計</th>
          </tr>
        </thead>
        <tbody>
          {preview?.lines.map((l) => (
            <tr key={l.product_code} style={{ background: l.product_code === highlightCode ? "#fff3b0" : undefined }}>
              <td>{l.name}</td>
              <td>{l.quantity}</td>
              <td>{l.unit_price}</td>
              <td style={{ color: l.discount_amount > 0 ? "crimson" : undefined }}>{l.discount_amount}</td>
              <td>{l.line_subtotal}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div style={{ marginTop: 16 }}>
        <p>税抜合計: {preview?.subtotal_excl_tax ?? 0}円</p>
        <p>値引き合計: {preview?.discount_total ?? 0}円</p>
        <p>
          消費税額: {preview?.tax_amount ?? 0}円（税率 {preview?.tax_rate ?? "-"}%）
        </p>
        <p style={{ fontSize: 24, fontWeight: "bold" }}>税込合計: {preview?.total_incl_tax ?? 0}円</p>
      </div>
    </>
  );
}
