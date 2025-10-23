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
    quantity: int  # ← 数量必須

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

        print("🟢 取引登録クエリ:", trd_query)
        print("🟢 取引登録値:", trd_values)

        trd_id = await database.execute(trd_query, trd_values)
        print(f"✅ 取引登録成功: trd_id={trd_id}")

        # --- 明細登録 ---
        for item in request.items:
            print(f"🧾 明細登録準備: {item.product_name} × {item.quantity}")
            for i in range(item.quantity):
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
                print("➡️ 明細クエリ:", dtl_query)
                print("➡️ 明細値:", dtl_values)
                await database.execute(dtl_query, dtl_values)
                print(f"✅ 明細登録完了: {item.product_name}")

        print("🎉 全商品の登録完了")
        return {"message": "取引および明細を登録しました", "trd_id": trd_id}

    except Exception as e:
        tb = traceback.format_exc()
        print("❌ PURCHASE INSERT ERROR:")
        print(tb)
        raise HTTPException(status_code=500, detail={"error": str(e), "traceback": tb})


# ------------------------------------------------
# ✅ デバッグ用エンドポイント（DB疎通と件数確認）
# ------------------------------------------------
@router.get("/debug-db")
async def debug_db():
    """
    DB接続確認とレコード件数確認用
    """
    try:
        async with database.connection() as conn:
            trd_count = await conn.fetch_val("SELECT COUNT(*) FROM `取引`")
            dtl_count = await conn.fetch_val("SELECT COUNT(*) FROM `取引明細`")
            return {
                "取引テーブル件数": trd_count,
                "取引明細テーブル件数": dtl_count
            }
    except Exception as e:
        tb = traceback.format_exc()
        print("❌ DEBUG DB ERROR:", e)
        print(tb)
        return {"error": str(e), "trace": tb}
