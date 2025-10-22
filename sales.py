# frontend/backend/sales.py

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List
import datetime
from database import database, transactions, transaction_details

router = APIRouter()

# (Itemクラス, PurchaseRequestクラスは変更なし)
class Item(BaseModel):
    product_id: int
    product_code: str # <- フロントエンドの型定義に合わせて修正 (prd_code -> product_code)
    product_name: str # <- フロントエンドの型定義に合わせて修正 (prd_name -> product_name)
    price: int        # <- フロントエンドの型定義に合わせて修正 (prd_price -> price)
    tax_code: str
    quantity: int

class PurchaseRequest(BaseModel):
    # ★ 1. フロントエンド('page.tsx')が送るJSONのキーに合わせる
    # pos_id: str
    # store_id: str
    # employee_id: str
    items: List[Item]
    # (page.tsxは 'items', 'total', 'totalWithTax' を送っていますが、
    #  バックエンドで計算するため 'items' だけ受け取ればOKです)


# ★ 2. エンドポイントを '/purchase' から '/purchases' (複数形) に変更
@router.post("/purchases", status_code=status.HTTP_201_CREATED)
async def purchase(request: PurchaseRequest):
    """
    購入API。合計金額（税込・税抜）を計算しDBへ保存する。
    """
    if not request.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="購入商品が指定されていません")

    async with database.transaction() as transaction:
        try:
            # フロントエンドから送られてきた 'items' リストを使って計算
            total_amt_ex_tax = sum(item.price * item.quantity for item in request.items)
            tax_rate = 0.10
            total_amt = round(total_amt_ex_tax * (1 + tax_rate))

            # 取引テーブルへの挿入
            transaction_insert_query = transactions.insert().values(
                datetime=datetime.datetime.now(),
                emp_cd="EMP001", # ★ 3. 固定値 (またはフロントから受け取る)
                store_cd="STR01", # ★ 3. 固定値 (またはフロントから受け取る)
                pos_no="POS01",   # ★ 3. 固定値 (またはフロントから受け取る)
                total_amt=0, # 合計金額 (後で更新)
                ttl_amt_ex_tax=0 # 税抜合計 (後で更新)
            )
            trd_id = await transaction.execute(transaction_insert_query)

            # 取引明細テーブルへの挿入
            details_to_insert = [
                {
                    "trd_id": trd_id,
                    "prd_id": item.product_id,
                    "prd_code": item.product_code, # ★ 4. Itemモデルのキーと合わせる
                    "prd_name": item.product_name, # ★ 4. Itemモデルのキーと合わせる
                    "prd_price": item.price,     # ★ 4. Itemモデルのキーと合わせる
                    "tax_cd": item.tax_code,
                }
                for item in request.items
                for _ in range(item.quantity) # ★ 5. 数量(quantity)分だけ明細行を作成
            ]
            
            if details_to_insert: # 挿入するデータがある場合のみ実行
                await transaction.execute(transaction_details.insert().values(details_to_insert))
            else:
                # 数量が0などの理由で明細がない場合はロールバック
                await transaction.rollback()
                raise HTTPException(status_code=400, detail="有効な購入明細がありません")


            # 取引テーブルの合計金額を更新
            transaction_update_query = transactions.update().where(
                transactions.c.trd_id == trd_id
            ).values(
                total_amt=total_amt,
                ttl_amt_ex_tax=total_amt_ex_tax
            )
            await transaction.execute(transaction_update_query)

            # フロントエンドに返すレスポンス
            return {
                "success": True,
                "trd_id": trd_id,
                "total_amount": total_amt,
                "total_amount_ex_tax": total_amt_ex_tax
            }
        
        except Exception as e:
            await transaction.rollback()
            raise HTTPException(status_code=500, detail=f"購入処理中にエラーが発生しました: {e}")