import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE = "https://api-m.sandbox.paypal.com"
CID = os.getenv("PAYPAL_CLIENT_ID")
SECRET = os.getenv("PAYPAL_SECRET")


def get_token():
    r = requests.post(
        f"{BASE}/v1/oauth2/token",
        auth=(CID, SECRET),
        data={"grant_type": "client_credentials"},
    )
    r.raise_for_status()
    return r.json()["access_token"]


def create_order(amount, currency="USD"):
    r = requests.post(
        f"{BASE}/v2/checkout/orders",
        headers={
            "Authorization": f"Bearer {get_token()}",
            "Content-Type": "application/json",
        },
        json={
            "intent": "CAPTURE",
            "purchase_units": [
                {"amount": {"currency_code": currency, "value": f"{amount:.2f}"}}
            ],
            "payment_source": {
                "paypal": {
                    "experience_context": {
                        "return_url": "http://localhost:8000/success",
                        "cancel_url": "http://localhost:8000/cancel",
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