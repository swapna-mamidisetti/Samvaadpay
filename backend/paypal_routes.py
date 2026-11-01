import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from backend.paypal_service import create_order, capture_order

router = APIRouter()


class OrderRequest(BaseModel):
    amount: float
    currency: str = "USD"


@router.post("/create-order")
def create(req: OrderRequest):
    try:
        order_id, link = create_order(req.amount, req.currency)
    except requests.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"PayPal error: {e.response.text}")
    return {"order_id": order_id, "approve_link": link}


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