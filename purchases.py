from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime
from database import database
import traceback

router = APIRouter()

# -------------------------------
# 💡 Pydanticモデル定義
# -------------------------------

class PurchaseItem(BaseModel):
    product_id: int
    product_name: str
    price: int
    quantity: int  # ← 数量を必須に！

class PurchaseRequest(BaseModel):
    items: List[PurchaseItem]
    total: int
    totalWithTax: int

# -------------------------------
# 💡 購入登録API
# -------------------------------

@router.post("/purchases")
async def create_purchase(request: PurchaseRequest):
    """
    複数商品の購入情報を登録するAPI
    """
    try:
        print("🟢 購入登録開始:", request.dict())

        # --- 取引（ヘッダ）登録 ---
        trd_query = """
            INSERT INTO 取引 (datetime, emp_cd, store_cd, pos_no, total_amt, ttl_amt_ex_tax)
            VALUES (:datetime, :emp_cd, :store_cd, :pos_no, :total_amt, :ttl_amt_ex_tax)
        """
        trd_values = {
            "datetime": datetime.now(),
            "emp_cd": "E001",
            "store_cd": "S001",
            "pos_no": "P01",
            "total_amt": request.totalWithTax,
            "ttl_amt_ex_tax": request.total
        }
        trd_id = await database.execute(trd_query, trd_values)
        print(f"✅ 取引登録成功: trd_id={trd_id}")

        # --- 取引明細登録 ---
        for item in request.items:
            for _ in range(item.quantity):  # ← 数量分ループで登録
                dtl_query = """
                    INSERT INTO 取引明細 (trd_id, prd_id, prd_code, prd_name, prd_price, tax_cd)
                    VALUES (:trd_id, :prd_id, :prd_code, :prd_name, :prd_price, :tax_cd)
                """
                dtl_values = {
                    "trd_id": trd_id,
                    "prd_id": item.product_id,
                    "prd_code": f"PRD{item.product_id}",
                    "prd_name": item.product_name,
                    "prd_price": item.price,
                    "tax_cd": "10"
                }
                await database.execute(dtl_query, dtl_values)
                print(f"🧾 明細登録: {item.product_name} x1")

        print("🎉 全商品の登録完了")
        return {"message": "取引および明細を登録しました", "trd_id": trd_id}

    except Exception as e:
        tb = traceback.format_exc()
        print("❌ PURCHASE INSERT ERROR:", str(e))
        print(tb)
        raise HTTPException(status_code=500, detail={"error": str(e), "traceback": tb})
