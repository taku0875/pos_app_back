from fastapi import FastAPI, HTTPException
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

origins = [
    "*" # デプロイ後も許可
]




# 既存ルーターを登録
app.include_router(products.router, prefix="/api/v1/products", tags=["products"])
app.include_router(sales.router, prefix="/api/v1/sales", tags=["sales"])
app.include_router(auth_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
