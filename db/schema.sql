-- 簡易POSアプリ改（Lv2） スキーマ定義
-- 設計仕様書 v2.9 第2章2.3 に基づく。
-- 講師配布のAzure Database for MySQL Flexible Server に、
-- このアプリ用のテーブルとして追加することを想定（CREATE TABLE IF NOT EXISTS）。
--
-- 実行例:
--   mysql -h <host> -u <user> -p < schema.sql
--
-- 文字コードはutf8mb4、金額列は円の整数（INT）、日時はDATETIME(JST)。
-- created_at/updated_atは全テーブル共通（設計仕様書2.3の共通事項）。

SET NAMES utf8mb4;

-- 2.3.1 employees（担当者）
CREATE TABLE IF NOT EXISTS employees (
  employee_id     VARCHAR(20)  NOT NULL,
  name            VARCHAR(50)  NOT NULL,
  password_hash   VARCHAR(60)  NOT NULL,
  is_admin        BOOLEAN      NOT NULL DEFAULT FALSE,
  created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (employee_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2.3.2 auth_tokens（認証トークン）
CREATE TABLE IF NOT EXISTS auth_tokens (
  token_hash          CHAR(64)     NOT NULL,
  employee_id         VARCHAR(20)  NOT NULL,
  issued_at           DATETIME     NOT NULL,
  expires_at          DATETIME     NOT NULL,
  admin_verified_at   DATETIME     NULL,
  created_at          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (token_hash),
  CONSTRAINT fk_auth_tokens_employee FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
  INDEX idx_auth_tokens_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2.3.3 products（商品）
CREATE TABLE IF NOT EXISTS products (
  product_code   CHAR(13)     NOT NULL,
  name            VARCHAR(100) NOT NULL,
  unit_price      INT          NOT NULL,
  created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (product_code),
  CONSTRAINT chk_products_unit_price CHECK (unit_price >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2.3.4 members（会員）
CREATE TABLE IF NOT EXISTS members (
  member_id   VARCHAR(13)   NOT NULL,
  name        VARCHAR(50)   NOT NULL,
  phone       VARCHAR(20)   NULL,
  address     VARCHAR(200)  NULL,
  gender      CHAR(1)       NULL,
  age         INT           NULL,
  created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (member_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2.3.5 discount_campaigns（値引き企画）
CREATE TABLE IF NOT EXISTS discount_campaigns (
  campaign_id     INT          NOT NULL AUTO_INCREMENT,
  product_code    CHAR(13)     NOT NULL,
  start_date      DATE         NOT NULL,
  end_date        DATE         NOT NULL,
  discount_type   CHAR(6)      NOT NULL,
  discount_value  INT          NOT NULL,
  created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (campaign_id),
  CONSTRAINT fk_campaigns_product FOREIGN KEY (product_code) REFERENCES products(product_code),
  CONSTRAINT chk_campaigns_dates CHECK (end_date >= start_date),
  CONSTRAINT chk_campaigns_type CHECK (discount_type IN ('RATE', 'AMOUNT')),
  CONSTRAINT chk_campaigns_value CHECK (discount_value > 0),
  INDEX idx_campaigns_product_period (product_code, start_date, end_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2.3.6 tax_rates（消費税率）
CREATE TABLE IF NOT EXISTS tax_rates (
  tax_rate_id     INT           NOT NULL AUTO_INCREMENT,
  rate            DECIMAL(4,2)  NOT NULL,
  effective_from  DATE          NOT NULL,
  created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (tax_rate_id),
  UNIQUE KEY uq_tax_rates_effective_from (effective_from)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2.3.7 transactions（取引）※FG-06は今回未実装だが、スキーマは仕様書どおり用意する
CREATE TABLE IF NOT EXISTS transactions (
  transaction_id      BIGINT        NOT NULL AUTO_INCREMENT,
  transacted_at        DATETIME      NOT NULL,
  idempotency_key      CHAR(36)      NOT NULL,
  employee_id          VARCHAR(20)   NOT NULL,
  member_id            VARCHAR(13)   NULL,
  subtotal_excl_tax    INT           NOT NULL,
  discount_total       INT           NOT NULL,
  tax_rate             DECIMAL(4,2)  NOT NULL,
  tax_amount           INT           NOT NULL,
  total_incl_tax       INT           NOT NULL,
  created_at           DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at           DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (transaction_id),
  UNIQUE KEY uq_transactions_idempotency_key (idempotency_key),
  CONSTRAINT fk_transactions_employee FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
  CONSTRAINT fk_transactions_member FOREIGN KEY (member_id) REFERENCES members(member_id),
  INDEX idx_transactions_transacted_at (transacted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2.3.8 transaction_details（取引明細）
CREATE TABLE IF NOT EXISTS transaction_details (
  transaction_id    BIGINT        NOT NULL,
  line_no           INT           NOT NULL,
  product_code      CHAR(13)      NOT NULL,
  quantity          INT           NOT NULL,
  unit_price        INT           NOT NULL,
  discount_amount   INT           NOT NULL,
  campaign_id       INT           NULL,
  line_subtotal     INT           NOT NULL,
  created_at        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (transaction_id, line_no),
  CONSTRAINT fk_details_transaction FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id),
  CONSTRAINT fk_details_product FOREIGN KEY (product_code) REFERENCES products(product_code),
  CONSTRAINT fk_details_campaign FOREIGN KEY (campaign_id) REFERENCES discount_campaigns(campaign_id),
  CONSTRAINT chk_details_quantity CHECK (quantity BETWEEN 1 AND 99),
  INDEX idx_details_product_code (product_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
