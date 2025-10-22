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
        {"product_id": 1, "quantity": 2, "price": 180},
        {"product_id": 2, "quantity": 1, "price": 220}
      ],
      "total": 580,
      "totalWithTax": 638
    }
    """
    try:
        print("🟢 受信データ:", data)
        items = data.get("items", [])
        if not items:
            raise HTTPException(status_code=400, detail="商品データが空です")

        # --- トランザクション（取引ヘッダ）登録 ---
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

        # --- 各明細を登録 ---
        for item in items:
            print(f"➡️ 明細処理中: {item}")
            product_id = item.get("product_id")
            if not product_id:
                print(f"⚠️ product_id が指定されていません: {item}")
                continue

            prd_query = select(products).where(products.c.prd_id == product_id)
            product = await database.fetch_one(prd_query)
            print("📦 商品取得結果:", product)
            if not product:
                print(f"⚠️ 商品ID {product_id} がマスタに存在しません。スキップします。")
                continue

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
        return {"message": "購入を登録しました", "trd_id": trd_id}

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        print(f"❌ [PURCHASE INSERT ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))
