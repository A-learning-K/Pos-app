# 簡易POSアプリ改 Lv2 - コーディング（Week5提出版）

範囲・役割分担は `claude/Week4_コーディング計画_2026-09-24.md`（プロジェクト）、仕様は設計仕様書 v2.12・テスト設計書 v2.20 を参照。

## 実装状況（2026-09-30 更新）

業務機能は「ログイン → スキャン → 購入リストに追加 → 合計金額を表示」から成り立つ。
2026-09-27のWeek5スコープ決定により、今回は「ログイン」のみを実装・接続の対象とした（他の機能は一旦コードを作成した上で `_archive/` へ退避し、`main.py`のルーター登録からも外した）。

| 機能 | 状態 | 担当 |
|---|---|---|
| FG-01 ログイン画面・API（A-01/A-02） | ✅ 実装済み（配線・照合・トークン発行/検証とも完了） | AI／核心は自分 |
| FG-03 バーコードスキャン（カメラ→JAN13デコード→追加） | ⏸ コード作成済み・`frontend/_archive/`へ退避（現在の画面には未接続） | AI |
| FG-05 会計処理（値引き・消費税、A-06） | ⏸ コード作成済み・`backend/_archive/`へ退避（`main.py`未登録） | AI |
| FG-02 会員照会API（A-05）/ FG-08 商品検索API（A-04） | ⏸ コード作成済み・`backend/_archive/`へ退避（`main.py`未登録） | AI |
| N1 パスワード照合・トークン発行/検証 | ✅ 実装済み | 外枠AI／核心は自分 |
| 監査ログ | ✅ 実装済み | 外枠AI／核心は自分 |
| N2 セキュリティヘッダー | ✅ 実装済み | 外枠AI／核心は自分 |
| N3 エラーID表示 | ✅ 実装済み | 外枠AI／核心は自分 |
| FG-04/FG-06/FG-07 | 見送り（着手せず） | ― |

## セットアップ

### バックエンド

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # DATABASE_URL を編集（Azure Database for MySQL Flexible Server）
uvicorn app.main:app --reload
```

テストを実行する場合：

```bash
pip install -r requirements-dev.txt
pytest
```

### フロントエンド

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev   # http://localhost:3000
```

テストを実行する場合：

```bash
npx jest              # 単体テスト（__tests__/）
npx playwright test   # 結合テスト（e2e/。事前にbackendとfrontendを起動し、DBにseedを投入しておく）
```

## DB（Azure Database for MySQL Flexible Server）

```bash
mysql -h <host> -u <user> -p < db/schema.sql
mysql -h <host> -u <user> -p < db/seed.sql
```

`db/seed.sql` の `password_hash` はプレースホルダーです。ログインを試す前に、以下でbcryptハッシュを生成し、UPDATE文で実際の値に置き換えてください（コストファクタ12、設計仕様書 表5-3）。

```bash
python3 -c "import bcrypt; print(bcrypt.hashpw(b'任意のパスワード', bcrypt.gensalt(12)).decode())"
```

```sql
UPDATE employees SET password_hash = '<出力された値>' WHERE employee_id = 'E001';
```

DBはMySQL（Azure Database for MySQL Flexible Server）を使用します。`db/schema.sql` は `ENGINE=InnoDB` 等MySQL専用のDDLのため、SQLiteでは動作しません。ローカルから接続する前に、自分のIPをMySQLのファイアウォール規則で許可しておくこと。

## 動作確認の順番

1. `.env` の `DISABLE_AUTH=false`（現在の既定値）のまま、backendとfrontendを起動する
2. `/login` から担当者ID・パスワードでログインし、`/pos` へ遷移して担当者名とログアユトボタンが表示されることを確認する
3. 未ログイン状態で `/pos` のURLを直接開くと `/login` へ強制的に戻されることを確認する（BUG-006対応）
4. 自動テストで確認する場合は上記「セットアップ」内のテストコマンドを参照

## テスト実施状況

- pytest 34件・Jest 4件（BUG-006再発防止分を含む）・Playwright 11件（4件はFG-06/07未実装のため設計どおりスキップ）を実施し、全て合格（詳細はテスト設計書 v2.20 第3章）
- ローカルの実行結果は `backend/.pytest_cache/`・`frontend/playwright-report/`・`frontend/test-results/` に残る（いずれもGit管理対象外）

## 投稿（④）用メモ

- 業務機能スコープ：Week5提出時点ではログイン（FG-01）のみを実装・接続対象とした
- 生成AIを使った部分：FG-01の画面・API配線、非機能（N1・監査ログ・N2・N3）の外枠、DBスキーマ
- 自力実装した部分：パスワード照合・トークン生成/ハッシュ/検証の核心、監査ログの記録内容、セキュリティヘッダーの値、エラーログの内容、BUG-006（未ログイン時の`/pos`アクセス制御漏れ）の修正
- コードは作成したがWeek5スコープ外として`_archive/`へ退避した部分：FG-02（会員照会API）・FG-03（バーコードスキャン）・FG-05（会計処理）・FG-08（商品検索API）
- 今回まったく着手しなかった部分：FG-04（購入リスト操作）・FG-06（取引確定）・FG-07（マスタ管理画面）
