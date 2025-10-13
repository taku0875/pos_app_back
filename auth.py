# auth.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from database import database
import os


router = APIRouter(prefix="/auth", tags=["auth"])

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed_password = pwd_context.hash("password001")

fake_users_db = {
    "user1": {
        "username": "test1",
        "hashed_password": "$2b$12$xJhI8K.0DaA2d4A.Io/HXu6lAQrghZ8sn07knY3CvgaF.0jadAOl2"
    }
}


# --- モデル定義 ---
class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str

class UserInDB(User):
    hashed_password: str

class UserLogin(BaseModel):
    username: str
    password: str

# --- パスワード検証 ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# --- ユーザー検索 ---
def get_user(db, username: str):
    user = db.get(username)
    if user:
        return UserInDB(**user)
    return None

# --- JWTトークン作成 ---
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- ログインAPI ---
@router.post("/login", response_model=Token)
async def login(user: UserLogin):
    db_user = get_user(fake_users_db, user.username)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="ユーザー名またはパスワードが違います")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- 認証テストAPI ---
@router.get("/users/me")
async def read_users_me(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="トークンが無効です")
        return {"username": username}
    except JWTError:
        raise HTTPException(status_code=401, detail="トークンが無効です")
