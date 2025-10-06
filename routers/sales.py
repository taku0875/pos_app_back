# routers/sales.py

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List
import datetime
from database import database, transactions, transaction_details

router = APIRouter()

# リクエストボディのモデルを定義
class Item(BaseModel):
    product_id: int
    product_code: str
    product_name: str
    price: int
    tax_code: str
    quantity: int

class PurchaseRequest(BaseModel):
    pos_id: str
    store_id: str
    employee_id: str
    items: List[Item]

@router.post("/purchase", status_code=status.HTTP_201_CREATED)
async def purchase(request: PurchaseRequest):
    """
    Lv.2仕様に対応した購入API。合計金額（税込・税抜）を計算しDBへ保存する。
    """
    if not request.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="購入商品が指定されていません")

    async with database.transaction() as transaction:
        try:
            # 1. 合計金額（税抜）と合計金額（税込）を計算
            total_amt_ex_tax = sum(item.price * item.quantity for item in request.items)
            # 仕様書通り、消費税区分'10'で固定
            tax_rate = 0.10
            total_amt = round(total_amt_ex_tax * (1 + tax_rate))

            # 1-1. 取引テーブルへ登録（合計金額は一旦0で仮登録）
            transaction_insert_query = transactions.insert().values(
                datetime=datetime.datetime.now(),
                emp_cd=request.employee_id,
                store_cd=request.store_id,
                pos_no=request.pos_id,
                total_amt=0,  # Lv.2仕様通り、最初は0で登録
                ttl_amt_ex_tax=0 # Lv.2仕様通り、最初は0で登録
            )
            trd_id = await transaction.execute(transaction_insert_query)

            # 1-2. 取引明細へ登録
            details_to_insert = [
                {
                    "trd_id": trd_id,
                    "prd_id": item.product_id,
                    "prd_code": item.product_code,
                    "prd_name": item.product_name,
                    "prd_price": item.price,
                    "tax_cd": item.tax_code,
                }
                for item in request.items
            ]
            await transaction.execute(transaction_details.insert().values(details_to_insert))

            # 1-4. 取引テーブルを合計金額で更新
            transaction_update_query = transactions.update().where(
                transactions.c.trd_id == trd_id
            ).values(
                total_amt=total_amt,
                ttl_amt_ex_tax=total_amt_ex_tax
            )
            await transaction.execute(transaction_update_query)

            # 1-5. 合計金額、合計金額（税抜）をフロントへ返す
            return {
                "success": True,
                "trd_id": trd_id,
                "total_amount": total_amt,
                "total_amount_ex_tax": total_amt_ex_tax
            }
        
        except Exception as e:
            await transaction.rollback()
            raise HTTPException(status_code=500, detail=f"購入処理中にエラーが発生しました: {e}")