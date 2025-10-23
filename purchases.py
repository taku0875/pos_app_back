from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime
from database import database
import traceback

router = APIRouter()

class PurchaseItem(BaseModel):
    product_id: int
    product_name: str
    price: int
    quantity: int

class PurchaseRequest(BaseModel):
    items: List[PurchaseItem]
    total: int
    totalWithTax: int


@router.post("/purchases")
async def create_purchase(request: PurchaseRequest):
    try:
        print("🟢 購入登録開始:", request.dict())

        async with database.connection() as conn:
            async with conn.transaction():
                # 取引ヘッダ登録
                trd_query = """
                    INSERT INTO `取引`
                        (`datetime`, `emp_cd`, `store_cd`, `pos_no`, `total_amt`, `ttl_amt_ex_tax`)
                    VALUES
                        (:datetime, :emp_cd, :store_cd, :pos_no, :total_amt, :ttl_amt_ex_tax)
                """
                trd_values = {
                    "datetime": datetime.now(),
                    "emp_cd": "E001",
                    "store_cd": "S001",
                    "pos_no": "P01",
                    "total_amt": request.totalWithTax,
                    "ttl_amt_ex_tax": request.total
                }

                try:
                    exec_result = await conn.execute(trd_query, trd_values)
                    print("🧾 取引INSERT実行結果:", exec_result)
                except Exception as e:
                    print("❌ 取引INSERT失敗:", e)
                    raise

                # trd_id取得
                trd_id = await conn.fetch_val("SELECT LAST_INSERT_ID()")
                print("✅ 取得した取引ID:", trd_id)

                # 明細登録
                dtl_query = """
                    INSERT INTO `取引明細`
                        (`trd_id`, `prd_id`, `prd_code`, `prd_name`, `prd_price`, `tax_cd`)
                    VALUES
                        (:trd_id, :prd_id, :prd_code, :prd_name, :prd_price, :tax_cd)
                """

                for item in request.items:
                    for _ in range(item.quantity):
                        dtl_values = {
                            "trd_id": trd_id,
                            "prd_id": item.product_id,
                            "prd_code": f"PRD{item.product_id}",
                            "prd_name": item.product_name,
                            "prd_price": item.price,
                            "tax_cd": "10"
                        }
                        print(f"🧩 明細登録中: {dtl_values}")
                        await conn.execute(dtl_query, dtl_values)

        print("🎉 全登録完了")
        return {"message": "登録完了", "trd_id": trd_id}

    except Exception as e:
        tb = traceback.format_exc()
        print("❌ PURCHASE INSERT ERROR:", str(e))
        print(tb)
        raise HTTPException(status_code=500, detail={"error": str(e), "traceback": tb})
