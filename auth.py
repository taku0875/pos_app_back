# auth.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import os

router = APIRouter(prefix="/auth", tags=["auth"])

# --- セキュリティ設定 ---
# 環境変数からJWTシークレットキーを読み込む
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# SECRET_KEYが設定されていない場合は、エラーを出して安全に停止する
if SECRET_KEY is None:
    raise ValueError("JWT_SECRET_KEY must be set in the environment variables.")

# パスワードのハッシュ化に関する設定
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- テスト用のユーザーデータベース ---
# password001 をハッシュ化したものを直接格納
fake_users_db = {
    "test1": {
        "username": "test1",
        "hashed_password": "$2b$12$EixZaY2V.4.wz.g523s3sOXsgKzZxwe4S.86Y.N2.GM.s.cMUv.Da" 
    }
}


# --- モデル定義 ---
class Token(BaseModel):
    access_token: str
    token_type: str

class UserLogin(BaseModel):
    username: str
    password: str


# --- ヘルパー関数 ---
def verify_password(plain_password, hashed_password):
    """平文のパスワードとハッシュ化されたパスワードを比較する"""
    return pwd_context.verify(plain_password, hashed_password)

def get_user(username: str):
    """テスト用DBからユーザー情報を取得する"""
    if username in fake_users_db:
        return fake_users_db[username]
    return None

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """JWTアクセストークンを生成する"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# --- APIエンドポイント ---
@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: UserLogin):
    """ユーザー名とパスワードで認証し、アクセストークンを発行する"""
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user["username"]}
    )
    return {"access_token": access_token, "token_type": "bearer"}