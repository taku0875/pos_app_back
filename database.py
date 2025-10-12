import os
import ssl
import sqlalchemy
from databases import Database

# Azure環境変数から接続情報を取得
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set.")

# Azure Database for MySQL は SSL 必須
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_REQUIRED

# ✅ App Service 環境には pem ファイルがないため create_default_context でOK
database = Database(DATABASE_URL, ssl=ssl_context)

metadata = sqlalchemy.MetaData()

# --- 以下は既存のテーブル定義そのままでOK ---
products = sqlalchemy.Table(
    "商品マスタ",
    metadata,
    sqlalchemy.Column("prd_id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("code", sqlalchemy.String(25), unique=True, index=True),
    sqlalchemy.Column("name", sqlalchemy.String(50)),
    sqlalchemy.Column("price", sqlalchemy.Integer),
)

transactions = sqlalchemy.Table(
    "取引",
    metadata,
    sqlalchemy.Column("trd_id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("datetime", sqlalchemy.TIMESTAMP),
    sqlalchemy.Column("emp_cd", sqlalchemy.String(10)),
    sqlalchemy.Column("store_cd", sqlalchemy.String(5)),
    sqlalchemy.Column("pos_no", sqlalchemy.String(3)),
    sqlalchemy.Column("total_amt", sqlalchemy.Integer),
    sqlalchemy.Column("ttl_amt_ex_tax", sqlalchemy.Integer),
)

transaction_details = sqlalchemy.Table(
    "取引明細",
    metadata,
    sqlalchemy.Column("dtl_id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("trd_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("取引.trd_id")),
    sqlalchemy.Column("prd_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("商品マスタ.prd_id")),
    sqlalchemy.Column("prd_code", sqlalchemy.String(13)),
    sqlalchemy.Column("prd_name", sqlalchemy.String(50)),
    sqlalchemy.Column("prd_price", sqlalchemy.Integer),
    sqlalchemy.Column("tax_cd", sqlalchemy.String(2)),
)
