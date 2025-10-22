from fastapi import APIRouter, HTTPException
from database import database, transactions, transaction_details, products
from datetime import datetime
from sqlalchemy import insert, select

router = APIRouter()

@router.post("/purchases")
async def create_purchase(data: dict):
    """
    カート内の複数商品を登録するAPI
    data = {
      "items": [
        {"code": "4901085653463", "name": "カフェオレ", "price": 180},
        {"code": "4901777318772", "name": "紅茶", "price": 150}
      ],
      "total": 330,
      "totalWithTax": 363
    }
    """
    try:
        items = data.get("items", [])
        if not items:
            raise HTTPException(status_code=400, detail="商品が空です")

        # ✅ トランザクション登録
        trd_insert = insert(transactions).values(
            datetime=datetime.now(),
            emp_cd="E001",
            store_cd="S001",
            pos_no="001",
            total_amt=data.get("totalWithTax"),
            ttl_amt_ex_tax=data.get("total"),
        )
        trd_id = await database.execute(trd_insert)

        # ✅ 各商品を明細登録
        for item in items:
            # DB上の商品確認（存在チェック）
            query = select(products).where(products.c.code == item["code"])
            product = await database.fetch_one(query)
            if not product:
                print(f"⚠️ 商品コード {item['code']} がマスタに存在しません。スキップします。")
                continue

            dtl_insert = insert(transaction_details).values(
                trd_id=trd_id,
                prd_id=product["prd_id"],
                prd_code=product["code"],
                prd_name=product["name"],
                prd_price=product["price"],
                tax_cd="01",
            )
            await database.execute(dtl_insert)

        return {"message": "複数商品の購入を登録しました", "trd_id": trd_id}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [PURCHASE INSERT ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))
