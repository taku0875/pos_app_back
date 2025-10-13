from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta, timezone
from jose import jwt
import os

router = APIRouter(tags=["auth"])

# データベース接続とテーブル定義、ハッシュ化ユーティリティをインポート
from database import database, users
from hashing import Hash

# --- 環境変数 ---
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))


if not SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY must be set in environment variables")

# --- モデル定義 ---
class Token(BaseModel):
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    username: str
    password: str

# --- トークン生成 ---
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- ログイン API ---
@router.post("/login", response_model=Token)
async def login(request: LoginRequest):
    # データベースのusersテーブルからユーザーを検索
    query = users.select().where(users.c.email == request.username)
    user = await database.fetch_one(query)

    # ユーザーが見つからないか、パスワードが一致しない場合はエラー
    if not user or not Hash.verify(user.hashed_password, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Incorrect username or password"
        )

    # 成功した場合、アクセストークンを生成して返す
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}