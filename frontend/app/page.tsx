import Link from "next/link";


export default function Home() {
  return (
    <main>
      <h1>簡易POSアプリ改 Lv2</h1>
      <p>
        <Link href="/login">→ ログイン（SC-01）</Link>
      </p>
      <p style={{ color: "#666", fontSize: 12 }}>
        開発中（バックエンドが DISABLE_AUTH=true の間）は <Link href="/pos">POSレジ画面</Link> を直接開けます。
      </p>
    </main>
  );
}
