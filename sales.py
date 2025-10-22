# frontend/backend/sales.py

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List
import datetime
from database import database, transactions, transaction_details, products

router = APIRouter()

# ★ 1. Pydanticモデル (変更なし)
class Item(BaseModel):
    product_id: int
    quantity: int
    price: int

class PurchaseRequest(BaseModel):
    items: List[Item]
    total: int 
    totalWithTax: int

@router.post("/purchases", status_code=status.HTTP_201_CREATED)
async def purchase(request: PurchaseRequest):
    if not request.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="購入商品が指定されていません")

    async with database.transaction() as transaction:
        try:
            total_amt_ex_tax = request.total
            total_amt = request.totalWithTax

            # 取引テーブルへの挿入
            transaction_insert_query = transactions.insert().values(
                datetime=datetime.datetime.now(),
                emp_cd="EMP001", 
                store_cd="STR01",
                pos_no="POS01",  
                total_amt=total_amt,
                ttl_amt_ex_tax=total_amt_ex_tax
            )
            trd_id = await transaction.execute(transaction_insert_query)

            # 取引明細テーブルへの挿入
            details_to_insert = []
            for item in request.items: # ★ ループ開始
                product_query = products.select().where(products.c.prd_id == item.product_id)
                db_product = await database.fetch_one(product_query)
                
                if not db_product:
                    await transaction.rollback()
                    raise HTTPException(status_code=404, detail=f"商品ID {item.product_id} がマスタに存在しません")

                for _ in range(item.quantity):
                    details_to_insert.append(
                        {
                            "trd_id": trd_id,
                            "prd_id": item.product_id,
                            "prd_code": db_product.code,
                            "prd_name": db_product.name,
                            "prd_price": db_product.price,
                            "tax_cd": "10",
                        }
                    )
            # ★ ループ終了
            
            # ▼▼▼ 修正箇所 ▼▼▼
            # 'if' ブロックをループの外に（インデントを一段階浅く）修正
            if details_to_insert:
                await transaction.execute(transaction_details.insert().values(details_to_insert))
            else:
                await transaction.rollback()
                raise HTTPException(status_code=400, detail="有効な購入明細がありません")
            # ▲▲▲ 修正完了 ▲▲▲

            return {
                "success": True,
                "trd_id": trd_id,
                "total_amount": total_amt,
                "total_amount_ex_tax": total_amt_ex_tax
            }
        
        except Exception as e:
            await transaction.rollback()
            raise HTTPException(status_code=500, detail=f"購入処理中にエラーが発生しました: {e}")