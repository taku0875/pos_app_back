from fastapi import APIRouter, HTTPException
from database import database, transactions, transaction_details, products
from datetime import datetime
from sqlalchemy import insert, select
import traceback

router = APIRouter()

@router.post("/purchases")
async def create_purchase(data: dict):
    """
    複数商品の購入情報を登録するAPI。
    受信形式:
    {
      "items": [
        {"code": "4901085653463", "name": "タリーズコーヒー", "price": 180, "quantity": 1},
        {"code": "4901777318779", "name": "サントリー天然水", "price": 120, "quantity": 2}
      ],
      "total": 420,
      "totalWithTax": 462
    }
    """
    try:
        print("🟢 受信データ:", data)
        items = data.get("items", [])
        if not items:
            raise HTTPException(status_code=400, detail="商品データが空です")

        # --- 取引ヘッダ登録 ---
        trd_insert = insert(transactions).values(
            datetime=datetime.now(),
            emp_cd="E001",
            store_cd="S001",
            pos_no="001",
            total_amt=data.get("totalWithTax", 0),
            ttl_amt_ex_tax=data.get("total", 0),
        )
        trd_id = await database.execute(trd_insert)
        print(f"🟢 取引登録完了 trd_id={trd_id}")

        # --- 各明細登録 ---
        for item in items:
            print(f"➡️ 明細処理中: {item}")

            # 商品コードからマスタ検索
            prd_query = select(products).where(products.c.code == item["code"])
            product = await database.fetch_one(prd_query)

            if not product:
                print(f"⚠️ 商品コード {item['code']} がマスタに存在しません。スキップします。")
                continue

            # 明細登録
            dtl_insert = insert(transaction_details).values(
                trd_id=trd_id,
                prd_id=product["prd_id"],
                prd_code=product["code"],
                prd_name=product["name"],
                prd_price=item["price"],
                tax_cd="01",
            )
            await database.execute(dtl_insert)
            print(f"✅ 明細登録OK: {product['name']}")

        print("🎉 全商品の登録完了")
        return {"message": "複数商品の購入を登録しました", "trd_id": trd_id}

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        print(f"❌ [PURCHASE INSERT ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))
