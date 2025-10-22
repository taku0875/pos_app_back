# frontend/backend/sales.py

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List
import datetime
from database import database, transactions, transaction_details, products # 'products' をインポート

router = APIRouter()

# ★ 1. フロントエンド('CartItem'型)とJSONのキーを合わせる
class Item(BaseModel):
    product_id: int
    quantity: int
    price: int
    # (フロントエンドから送られてくる他のキーは、このAPIでは使わないため省略)

class PurchaseRequest(BaseModel):
    # ★ 2. フロントエンド('page.tsx')が送るJSONのキーに合わせる
    items: List[Item]
    total: int # totalPreTax (税抜合計)
    totalWithTax: int # totalAfterTax (税込合計)


# ★ 3. エンドポイントを '/purchase' から '/purchases' (複数形) に変更 (修正済みのはず)
@router.post("/purchases", status_code=status.HTTP_201_CREATED)
async def purchase(request: PurchaseRequest):
    """
    購入API。フロントエンドで計算された合計金額を受け取りDBへ保存する。
    """
    if not request.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="購入商品が指定されていません")

    async with database.transaction() as transaction:
        try:
            # ★ 4. 金額はフロントエンドから受け取った値を使用
            total_amt_ex_tax = request.total
            total_amt = request.totalWithTax

            # 取引テーブルへの挿入
            transaction_insert_query = transactions.insert().values(
                datetime=datetime.datetime.now(),
                emp_cd="EMP001", # 固定値 (フロントから受け取っていないため)
                store_cd="STR01", # 固定値
                pos_no="POS01",   # 固定値
                total_amt=total_amt, # ★ 5. 合計金額を最初から挿入
                ttl_amt_ex_tax=total_amt_ex_tax # ★ 5. 税抜合計を最初から挿入
            )
            trd_id = await transaction.execute(transaction_insert_query)

            # 取引明細テーブルへの挿入
            details_to_insert = []
            for item in request.items:
                # DBから商品情報を取得（prd_code, prd_name, tax_cdを補完するため）
                product_query = products.select().where(products.c.prd_id == item.product_id)
                db_product = await database.fetch_one(product_query)
                
                if not db_product:
                    await transaction.rollback()
                    raise HTTPException(status_code=404, detail=f"商品ID {item.product_id} がマスタに存在しません")

                # 数量(quantity)分だけ明細行を作成
                for _ in range(item.quantity):
                    details_to_insert.append(
                        {
                            "trd_id": trd_id,
                            "prd_id": item.product_id,
                            "prd_code": db_product.code,     # DBから取得
                            "prd_name": db_product.name,     # DBから取得
                            "prd_price": db_product.price,    # DBから取得 (item.priceでも可)
                            "tax_cd": "10", # 固定
                        }
                    )
            
            if details_to_insert: # 挿入するデータがある場合のみ実行
                await transaction.execute(transaction_details.insert().values(details_to_insert))
            else:
                await transaction.rollback()
                raise HTTPException(status_code=400, detail="有効な購入明細がありません")

            # ★ 6. 合計金額のUPDATE処理は不要になったため削除
            
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