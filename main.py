# main.py

from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import database
from routers import products, sales

@asynccontextmanager
async def lifespan(app: FastAPI):
    # アプリケーション起動時にDB接続を確立
    await database.connect()
    yield
    # アプリケーション終了時にDB接続を切断
    await database.disconnect()

app = FastAPI(lifespan=lifespan)

# ルーターをアプリケーションに含める
app.include_router(products.router, prefix="/api/v1/products", tags=["products"])
app.include_router(sales.router, prefix="/api/v1/sales", tags=["sales"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)