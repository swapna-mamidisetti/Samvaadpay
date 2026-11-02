import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from backend.paypal_service import create_order, capture_order, calculate_total

router = APIRouter()


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
        return HTMLResponse("<h2>Payment Success ✅</h2><p>Thank you! You can close this tab.</p>")
    return HTMLResponse(f"<h2>Payment status: {status}</h2>")


@router.get("/cancel", response_class=HTMLResponse)
def cancel():
    return HTMLResponse("<h2>Payment cancelled.</h2>")