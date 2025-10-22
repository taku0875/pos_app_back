from fastapi import APIRouter, HTTPException
from database import database, transactions, transaction_details, products
from datetime import datetime
from sqlalchemy import insert, select

router = APIRouter()

@router.post("/purchases")
async def create_purchase(data: dict):
    """
    購入情報を登録するAPI。
    data には以下の形式のデータを受け取る想定：
    {
        "code": "4901085653463",
        "name": "カフェオレ",
        "price": 180
    }
    """
    try:
        # 1️⃣ 商品コードから商品情報を再確認
        query = select(products).where(products.c.code == data["code"])
        product = await database.fetch_one(query)
        if not product:
            raise HTTPException(status_code=404, detail="商品が見つかりません")

        # 2️⃣ 取引テーブルに新規登録
        trd_insert = insert(transactions).values(
            datetime=datetime.now(),
            emp_cd="E001",
            store_cd="S001",
            pos_no="001",
            total_amt=product["price"],
            ttl_amt_ex_tax=round(product["price"] / 1.1),  # 仮に10%税抜
        )
        trd_id = await database.execute(trd_insert)

        # 3️⃣ 取引明細テーブルに登録
        dtl_insert = insert(transaction_details).values(
            trd_id=trd_id,
            prd_id=product["prd_id"],
            prd_code=product["code"],
            prd_name=product["name"],
            prd_price=product["price"],
            tax_cd="01",
        )
        await database.execute(dtl_insert)

        return {"message": "購入を登録しました", "trd_id": trd_id}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [PURCHASE INSERT ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))
