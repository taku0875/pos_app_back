from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import database
import products
import sales
import purchases

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    yield
    await database.disconnect()

# ▼▼▼ 'prefix="/api/v1"' を削除した元の形に戻します ▼▼▼
app = FastAPI(lifespan=lifespan)

# ✅ CORS設定（ここが最重要）
origins = [
    "https://app-002-gen10-step3-1-node-oshima9.azurewebsites.net",  # フロントエンド
    "http://localhost:3000",  # ローカル開発用（必要なら残す）
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ ルーター登録（CORS設定の後に書くのが重要！）
app.include_router(products.router)
app.include_router(sales.router)
app.include_router(purchases.router)


# ✅ 動作確認用のルート（疎通テストに便利）
@app.get("/")
def read_root():
    return {"message": "Backend is running and CORS is working!"}