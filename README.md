# 簡易POSアプリ改 Lv2 - Week4 コーディング

範囲・役割分担は `claude/Week4_コーディング計画_2026-09-24.md`（プロジェクト）、仕様は設計仕様書 v2.9 を参照。

## 実装状況（2026-09-26）

業務機能は「ログイン → スキャン → 購入リストに追加 → 合計金額を表示」の1本のチェーンのみ。

| 機能 | 状態 | 担当 |
|---|---|---|
| FG-01 ログイン画面・API（A-01/A-02） | ✅ 配線済み（照合・トークンの核心は下のTODO） | AI |
| FG-03 バーコードスキャン（カメラ→JAN13デコード→追加） | ✅ 実装済み | AI |
| FG-05 会計処理（値引き・消費税、A-06） | ✅ 実装済み | AI |
| FG-02 会員照会API（A-05）/ FG-08 商品検索API（A-04） | バックエンドのみ（画面なし） | AI |
| N1 パスワード照合・トークン発行/検証 | 外枠のみ・**TODO 4行** | 外枠AI／核心は自分 |
| 監査ログ | 外枠のみ・**TODO 1行** | 外枠AI／核心は自分 |
| N2 セキュリティヘッダー | 外枠のみ・**値5つがTODO** | 外枠AI／核心は自分 |
| N3 エラーID表示 | 外枠・画面表示まで済み・**ログ出力TODO 1行** | 外枠AI／核心は自分 |
| FG-04/FG-06/FG-07 | 見送り | ― |

## 自分で書くところ（`TODO(自分で書く)` で検索）

| ファイル | 場所 | 書く内容 |
|---|---|---|
| `backend/app/security.py` | `_hash_token` | SHA-256（16進）を返す1行 |
| 〃 | `authenticate` | bcrypt で照合して True/False を返す1行 |
| 〃 | `issue_token` | 32バイトの乱数トークンを作る1行 |
| 〃 | `verify_token` | 「無効なら True」の条件式1行 |
| `backend/app/audit.py` | `log_event` | 何をどう記録するか（`logger.info` 1行） |
| `backend/app/main.py` | `handle_unexpected_error` | error_id で検索できるログ1行 |
| 〃 | `SECURITY_HEADERS` | 5つのヘッダーの値（採用しないものは None のまま） |

- security.py の4行を書くまで、ログインは 501（NOT_IMPLEMENTED）を返す。書き終えたら `.env` の `DISABLE_AUTH=false` にする
- audit.py・N3 のログ行は未記入でもアプリは止まらない（何も記録されないだけ）
- ヒント：CSP・X-Frame-Options は「ブラウザが画面（HTML）を表示するとき」に効くヘッダー。このアプリで画面のHTMLを返しているのは FastAPI と Next.js のどちらか、を一度考えてから値を決めると良い

## セットアップ

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # DATABASE_URL を編集
uvicorn app.main:app --reload
```

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev   # http://localhost:3000
```

## DB（Step3 の MySQL に追加）

```bash
mysql -h <host> -u <user> -p < db/schema.sql
mysql -h <host> -u <user> -p < db/seed.sql
```

seed の `password_hash` はダミー。ログインを試す前に、`seed.sql` のコメントにある1行で bcrypt ハッシュを作って UPDATE する。

**訂正（2026-09-26）**：以前ここに「`DATABASE_URL` を `sqlite:///./local_dev.db` に変えるだけで動作確認できる」と書いていたが誤り。`db/schema.sql` は `ENGINE=InnoDB`・`AUTO_INCREMENT` などMySQL専用のDDLで、SQLiteに切り替えてもテーブルは自動で作られない（初回アクセスで失敗する）。

**方針決定（2026-09-26）**：DBはMySQL（Step3のAzure Database for MySQL Flexible Server）を使う。ローカルからの動作確認前に、自分のIPをそのMySQLのファイアウォール規則で許可しておくこと。`.env` の `DATABASE_URL` はそのAzure MySQLの接続文字列を設定する。

## 動作確認の順番（おすすめ）

1. `DISABLE_AUTH=true` のまま `/pos` を開き、手入力 `4900000000018` → 合計が出る
2. 「カメラ起動」でスキャン（JAN13のみ、同一コードは1秒以内は無視）
3. security.py の TODO 4行 → `DISABLE_AUTH=false` → `/login` からログイン → `/pos`
4. audit.py・main.py の TODO を埋める

## 検証について

この作業環境では PyPI・npm がブロックされていて、サーバー起動とビルドはできていない。確認済みは以下のみ：
- Python 全ファイルの構文チェック（`py_compile`）
- TypeScript の型チェック（ライブラリ型は簡易スタブで代用）
- N3 のミドルウェア順序（500応答にも CORS とセキュリティヘッダーが付くこと）を Starlette 単体で確認

ローカルで上記「動作確認の順番」を必ず通すこと。単体テストは講師指示により今回は作成しない。

## 投稿（④）用メモ

- 業務機能スコープ：ログイン→スキャン→購入リスト追加→合計表示の1本に絞った
- 生成AIを使った部分：画面・API配線、スキャン、値引き/消費税計算、DBスキーマ、非機能コードの外枠
- 自力実装した部分：パスワード照合・トークン生成/ハッシュ/検証の核心、監査ログの記録内容、セキュリティヘッダーの値、エラーログの内容
- 見送った部分：会員ID入力(FG-02)、行操作(FG-04)、取引確定(FG-06)、マスタ管理(FG-07)
