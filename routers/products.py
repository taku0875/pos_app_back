# routers/products.py

from fastapi import APIRouter, HTTPException
from database import database, products

router = APIRouter()

@router.get("/search")
async def search_product(code: str):
    """
    商品コードで商品情報を検索します。
    """
    query = products.select().where(products.c.code == code)
    result = await database.fetch_one(query)
    
    if result:
        return result
    raise HTTPException(status_code=404, detail="商品が見つかりません")