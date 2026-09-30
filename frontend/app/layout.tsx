import type { Metadata } from "next";


export const metadata: Metadata = {
  title: "簡易POSアプリ改 Lv2",
  description: "Week4 コーディング課題",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body style={{ fontFamily: "sans-serif", margin: 0, padding: 16 }}>{children}</body>
    </html>
  );
}
