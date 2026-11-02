import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE = "https://api-m.sandbox.paypal.com"
CID = os.getenv("PAYPAL_CLIENT_ID")
SECRET = os.getenv("PAYPAL_SECRET")
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")
INR_PER_USD = float(os.getenv("INR_PER_USD", "95"))
def calculate_total(quantity, price, currency="INR"):
    """Returns (total_inr, total_usd) from quantity x price."""
    if quantity is None:
        quantity = 1
    if quantity < 1:
        raise ValueError("quantity must be at least 1")
    if price is None or price <= 0:
        raise ValueError("price is required and must be greater than 0")

    total = round(quantity * price, 2)

    if currency == "INR":
        total_inr = total
        total_usd = round(total / INR_PER_USD, 2)
    elif currency == "USD":
        total_usd = total
        total_inr = round(total * INR_PER_USD, 2)
    else:
        raise ValueError("currency must be INR or USD")

    if total_usd < 0.01:
        raise ValueError("total is too small to create a payment")

    return total_inr, total_usd
def get_token():
    r = requests.post(
        f"{BASE}/v1/oauth2/token",
        auth=(CID, SECRET),
        data={"grant_type": "client_credentials"},
    )
    r.raise_for_status()
    return r.json()["access_token"]


def create_order(amount, currency="USD", description=None):
    r = requests.post(
        f"{BASE}/v2/checkout/orders",
        headers={
            "Authorization": f"Bearer {get_token()}",
            "Content-Type": "application/json",
        },
        json={
            "intent": "CAPTURE",
            "purchase_units": [
    {
        "amount": {"currency_code": currency, "value": f"{amount:.2f}"},
        "description": (description or "SamvaadPay order")[:127],
    }
],
            "payment_source": {
                "paypal": {
                    "experience_context": {
                        "return_url": f"{APP_BASE_URL}/success",
                        "cancel_url": f"{APP_BASE_URL}/cancel",
                        "user_action": "PAY_NOW",
                    }
                }
            },
        },
    )
    r.raise_for_status()
    data = r.json()
    link = next(
        l["href"] for l in data["links"] if l["rel"] in ("payer-action", "approve")
    )
    return data["id"], link


def capture_order(order_id):
    r = requests.post(
        f"{BASE}/v2/checkout/orders/{order_id}/capture",
        headers={
            "Authorization": f"Bearer {get_token()}",
            "Content-Type": "application/json",
        },
    )
    r.raise_for_status()
    return r.json()["status"]  # "COMPLETED" = Payment Success


if __name__ == "__main__":
    oid, link = create_order(49.99)
    print("Order ID:", oid)
    print("Pay here:", link)
    input("Pay chesaka Enter nokkandi...")
    print("Status:", capture_order(oid))