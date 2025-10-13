from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import database
import products
import sales
from auth import router as auth_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    yield
    await database.disconnect()

app = FastAPI(lifespan=lifespan)

# CORSで許可するオリジン（アクセス元）のリスト
origins = [
    # Azure上のフロントエンドのURL
    "https://app-002-gen10-step3-1-node-oshima9.azurewebsites.net",
    
    # ローカル開発環境のURL
    "http://localhost:3000",
]

# CORSミドルウェアをアプリケーションに追加
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 既存ルーターを登録
app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(sales.router, prefix="/sales", tags=["sales"])
app.include_router(auth_router)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)