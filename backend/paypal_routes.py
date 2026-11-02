import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from backend.paypal_service import create_order, capture_order, calculate_total
from backend.db import get_conn
from backend.db import get_conn, reduce_stock
router = APIRouter()
ORDER_PRODUCTS = {}  # order_id -> product_id


class OrderRequest(BaseModel):
    item_name: str | None = None
    quantity: int | None = None
    price: float | None = None
    currency: str = "INR"

@router.post("/create-order")
def create(req: OrderRequest):
    try:
        total_inr, total_usd = calculate_total(req.quantity, req.price, req.currency)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    description = f"{req.item_name or 'Item'} x {req.quantity or 1}"

    try:
        order_id, link = create_order(total_usd, "USD", description)
    except requests.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"PayPal error: {e.response.text}")

    return {
        "order_id": order_id,
        "approve_link": link,
        "total_inr": total_inr,
        "total_usd": total_usd,
    }


@router.post("/capture-order/{order_id}")
def capture(order_id: str):
    try:
        status = capture_order(order_id)
    except requests.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"PayPal error: {e.response.text}")
    return {"order_id": order_id, "status": status}


@router.get("/success", response_class=HTMLResponse)
def success(token: str):
    try:
        status = capture_order(token)
    except requests.HTTPError:
        return HTMLResponse("<h2>Payment could not be completed.</h2>", status_code=400)
    if status == "COMPLETED":
        product_id = ORDER_PRODUCTS.pop(token, None)
        if product_id is not None:
            reduce_stock(product_id)
        return HTMLResponse("<h2>Payment Success ✅</h2><p>Thank you! You can close this tab.</p>")
    return HTMLResponse(f"<h2>Payment status: {status}</h2>")


@router.get("/cancel", response_class=HTMLResponse)
def cancel():
    return HTMLResponse("<h2>Payment cancelled.</h2>")
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