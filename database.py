# database.py

import sqlalchemy
from databases import Database
from sqlalchemy.orm import declarative_base, sessionmaker

# PostgreSQL接続URL
DATABASE_URL = ""

# データベースオブジェクト
database = Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

# テーブル定義
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

# 非同期セッションのファクトリ
engine = sqlalchemy.create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()