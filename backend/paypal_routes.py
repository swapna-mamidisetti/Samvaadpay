import os

import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from backend.db import get_conn, reduce_stock
from backend.paypal_service import create_order, capture_order

router = APIRouter()

FRONTEND_URL = os.getenv("FRONTEND_URL", "https://samvaadpay-0dcc.onrender.com").rstrip("/")

ORDER_PRODUCTS = {}  # order_id -> product_id


class CheckoutRequest(BaseModel):
    product_id: int


@router.post("/api/checkout")
def checkout(req: CheckoutRequest):
    conn = get_conn()
    row = conn.execute(
        "SELECT id, name, price, stock FROM products WHERE id = ?",
        (req.product_id,),
    ).fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Product not found")
    if row["stock"] < 1:
        raise HTTPException(status_code=409, detail="Out of stock")

    try:
        order_id, link = create_order(row["price"], "USD", f"{row['name']} x 1")
    except requests.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"PayPal error: {e.response.text}")

    ORDER_PRODUCTS[order_id] = req.product_id

    return {
        "order_id": order_id,
        "approve_link": link,
        "product": row["name"],
        "total_usd": row["price"],
    }


@router.post("/capture-order/{order_id}")
def capture(order_id: str):
    try:
        status = capture_order(order_id)
    except requests.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"PayPal error: {e.response.text}")
    return {"order_id": order_id, "status": status}


@router.get("/success")
def success(token: str):
    try:
        status = capture_order(token)
    except requests.HTTPError:
        return RedirectResponse(f"{FRONTEND_URL}/?payment=failed")

    if status == "COMPLETED":
        product_id = ORDER_PRODUCTS.pop(token, None)
        if product_id is not None:
            reduce_stock(product_id)
        return RedirectResponse(f"{FRONTEND_URL}/?payment=success")

    return RedirectResponse(f"{FRONTEND_URL}/?payment=failed")


@router.get("/cancel")
def cancel():
    return RedirectResponse(f"{FRONTEND_URL}/?payment=cancel")