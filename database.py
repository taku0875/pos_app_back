import os
import ssl
import sqlalchemy
from databases import Database
from dotenv import load_dotenv

# このファイル (database.py) があるディレクトリのパスを取得
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# .envファイルへのパスを明示的に指定して読み込む
dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path=dotenv_path)


# 環境変数から接続情報を取得
DATABASE_URL = os.getenv("DATABASE_URL")
SSL_CA_FILENAME = os.getenv("SSL_CA_PATH") # .envからはファイル名だけ取得

# DATABASE_URLが設定されていない場合はエラーを発生させる
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable must be set.")

database = None
ssl_context = None

# SSL証明書が指定されている場合の処理
if SSL_CA_FILENAME:
    # database.py と同じ階層にある証明書ファイルへの絶対パスを生成
    ssl_ca_path_full = os.path.join(BASE_DIR, SSL_CA_FILENAME)
    
    if os.path.exists(ssl_ca_path_full):
        print(f"✅ SSL CA file found, creating SSL context: {ssl_ca_path_full}")
        ssl_context = ssl.create_default_context(cafile=ssl_ca_path_full)
        # SSLコンテキストを渡してdatabaseインスタンスを作成
        database = Database(DATABASE_URL, ssl=ssl_context)
    else:
        print(f"❌ FATAL: SSL CA file not found at expected path: {ssl_ca_path_full}")
        # ファイルが見つからない場合はエラーで停止
        raise FileNotFoundError(f"SSL CA file not found at: {ssl_ca_path_full}")
else:
    # Azure上ではSSL_CA_PATHが設定されている前提だが、ローカルでSSLなしDBを使う場合
    print("⚠️ SSL_CA_PATH not set in .env. Connecting without SSL.")
    database = Database(DATABASE_URL)


metadata = sqlalchemy.MetaData()

# --- テーブル定義 (変更なし) ---
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

