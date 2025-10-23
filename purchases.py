from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from database import database
import traceback

router = APIRouter()

# -------------------------------
# 💡 Pydanticモデル定義（修正版）
# -------------------------------

class PurchaseItem(BaseModel):
    product_id: int
    name: Optional[str] = Field(None, description="商品名（name または product_name）")
    product_name: Optional[str] = Field(None, description="商品名（旧キー対応）")
    price: int
    quantity: int

    # name または product_name のどちらかを優先的に取得
    @property
    def resolved_name(self):
        return self.product_name or self.name or "不明商品"


class PurchaseRequest(BaseModel):
    items: List[PurchaseItem]
    total: int
    totalWithTax: int

# -------------------------------
# 💡 購入登録API（修正版）
# -------------------------------

@router.post("/purchases")
async def create_purchase(request: PurchaseRequest):
    """
    複数商品の購入情報を登録するAPI（name / product_name 両対応）
    """
    try:
        print("🟢 購入登録開始:", request.dict())

        async with database.transaction():
            # --- 取引登録 ---
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

            # --- 明細登録 ---
            for item in request.items:
                dtl_query = """
                    INSERT INTO 取引明細 (trd_id, prd_id, prd_code, prd_name, prd_price, tax_cd)
                    VALUES (:trd_id, :prd_id, :prd_code, :prd_name, :prd_price, :tax_cd)
                """
                dtl_values = {
                    "trd_id": trd_id,
                    "prd_id": item.product_id,
                    "prd_code": f"PRD{item.product_id}",
                    "prd_name": item.resolved_name,   # ← ここで name or product_name のどちらでもOK
                    "prd_price": item.price,
                    "tax_cd": "10"
                }

                # 数量分ループ
                for _ in range(item.quantity):
                    await database.execute(dtl_query, dtl_values)
                    print(f"🧾 明細登録: {item.resolved_name} x1")

        print("🎉 全商品の登録完了")
        return {"message": "取引および明細を登録しました", "trd_id": trd_id}

    except Exception as e:
        tb = traceback.format_exc()
        print("❌ PURCHASE INSERT ERROR:", str(e))
        print(tb)
        raise HTTPException(status_code=500, detail={"error": str(e), "traceback": tb})
