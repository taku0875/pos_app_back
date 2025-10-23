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
    """
    取引ヘッダと明細を一括登録（同一コネクション＋Tx で実行）
    """
    try:
        print("🟢 購入登録開始:", request.dict())

        async with database.connection() as conn:
            async with conn.transaction():  # ← 同一コネクション＋Tx
                # --- 取引ヘッダ ---
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
                    "ttl_amt_ex_tax": request.total,
                }
                exec_result = await conn.execute(trd_query, trd_values)  # MySQLだとNoneのことがある
                print("🧾 execute結果:", exec_result)

                # ← 同一コネクションで必ず取得
                trd_id = await conn.fetch_val("SELECT LAST_INSERT_ID()")
                if not trd_id:
                    raise RuntimeError("取引IDを取得できませんでした。")

                print(f"✅ 取引登録成功: trd_id={trd_id}")

                # --- 取引明細 ---
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
                            "tax_cd": "10",
                        }
                        await conn.execute(dtl_query, dtl_values)
                        print(f"🧩 明細登録: {item.product_name} ×1")

        print("🎉 登録完了")
        return {"message": "取引および明細を登録しました", "trd_id": trd_id}

    except Exception as e:
        tb = traceback.format_exc()
        print("❌ PURCHASE INSERT ERROR:", str(e))
        print(tb)
        # ここでTxは自動ロールバックされます
        raise HTTPException(status_code=500, detail={"error": str(e), "traceback": tb})
