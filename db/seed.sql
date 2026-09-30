-- 動作確認用の最小データ。
-- 商品A/B/Cと数値は設計仕様書 表2-13（計算例）と一致させている。
-- 注：テスト設計書 1.5 の方針では本番相当の試験は実物商品バーコードを使うこと。
--     ここでは開発中の動作確認用のダミーコードを使っている。

INSERT INTO employees (employee_id, name, password_hash, is_admin) VALUES
  ('E001', '山田太郎', '$2b$12$placeholder_replace_with_real_bcrypt_hash', FALSE),
  ('A001', '管理者', '$2b$12$placeholder_replace_with_real_bcrypt_hash', TRUE)
ON DUPLICATE KEY UPDATE name = VALUES(name);
-- password_hashはダミー値。ログインを試す前に、bcrypt（コストファクタ12・表5-3）で生成した値に置き換える。
-- 生成例（backend の venv で実行）:
--   python -c "import bcrypt; print(bcrypt.hashpw(b'任意のパスワード', bcrypt.gensalt(12)).decode())"
-- 置き換え例:
--   UPDATE employees SET password_hash = '<出力された値>' WHERE employee_id = 'E001';

INSERT INTO products (product_code, name, unit_price) VALUES
  ('4900000000018', '商品A', 198),
  ('4900000000025', '商品B', 105),
  ('4900000000032', '商品C', 350)
ON DUPLICATE KEY UPDATE name = VALUES(name), unit_price = VALUES(unit_price);

INSERT INTO members (member_id, name) VALUES
  ('1000000000001', 'テスト会員')
ON DUPLICATE KEY UPDATE name = VALUES(name);

INSERT INTO tax_rates (rate, effective_from) VALUES
  (10.00, '2020-01-01')
ON DUPLICATE KEY UPDATE rate = VALUES(rate);

INSERT INTO discount_campaigns (product_code, start_date, end_date, discount_type, discount_value) VALUES
  ('4900000000018', '2026-01-01', '2026-12-31', 'RATE', 20),
  ('4900000000032', '2026-01-01', '2026-12-31', 'AMOUNT', 30);
