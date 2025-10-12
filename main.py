from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from database import database
import products
import sales  # ← routersではなく直接ファイルをインポート！

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    yield
    await database.disconnect()

app = FastAPI(lifespan=lifespan)

# ✅ 商品検索APIをmainにも定義（スキャナー用）
@app.get("/products/search")
async def search_product(code: str):
    query = "SELECT * FROM products WHERE code = :code"
    result = await database.fetch_one(query, values={"code": code})
    if not result:
        raise HTTPException(status_code=404, detail="この商品は登録されていません。")
    return result

# 既存ルーターを登録
app.include_router(products.router, prefix="/api/v1/products", tags=["products"])
app.include_router(sales.router, prefix="/api/v1/sales", tags=["sales"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
