import sqlalchemy
from databases import Database
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv
import os
import ssl

# .envファイルから環境変数を読み込む
load_dotenv()

# 環境変数からデータベースURLとSSL証明書のパスを取得
DATABASE_URL = os.getenv("DATABASE_URL")
SSL_CA_PATH =r"C:\POS-app\backend\azure-mysql-ca-bundle.pem"


# DATABASE_URLが設定されていない場合はエラーを発生させる
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set.")

# SSL証明書のパスが指定されているか確認
if not SSL_CA_PATH:
    raise ValueError("SSL_CA_PATH environment variable is not set.")

# SSLコンテキストを生成
# cafile引数にSSL証明書のパスを指定
ssl_context = ssl.create_default_context(cafile=SSL_CA_PATH)

# databaseオブジェクトの初期化時に、sslパラメータにssl_contextを渡す
# Azure MySQLではこの形式が必須
database = Database(DATABASE_URL, ssl=ssl_context)

metadata = sqlalchemy.MetaData()

# テーブル定義
# 商品マスタテーブル
products = sqlalchemy.Table(
    "商品マスタ",
    metadata,
    sqlalchemy.Column("prd_id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("code", sqlalchemy.String(25), unique=True, index=True),
    sqlalchemy.Column("name", sqlalchemy.String(50)),
    sqlalchemy.Column("price", sqlalchemy.Integer),
)

# 取引テーブル
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

# 取引明細テーブル
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