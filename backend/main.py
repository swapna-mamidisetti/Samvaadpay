import os
import time
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from backend.paypal_routes import router as paypal_router
from backend.db import init_db, search_products
from backend.shop_routes import router as shop_router

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI(title="SamvaadPay Backend")
init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(paypal_router)
app.include_router(shop_router)


class ChatMessage(BaseModel):
    message: str


@app.get("/")
def home():
    return {"status": "success", "message": "SamvaadPay AI Engine is Live!"}


@app.post("/chat")
def chat_with_ai(chat_input: ChatMessage):
    prompt = f"""
    A customer wrote this shopping message: "{chat_input.message}".
    Extract what they want and return a JSON object with these exact keys:
    {{
        "category": "shoes" or "clothing" or null,
        "color": "lowercase color or null",
        "size": "size as text, e.g. 8 or M, or null",
        "max_price": number or null
    }}
    The message may be in Telugu, English, or mixed.
    Use null for anything not mentioned. Return only JSON.
    """

    data = None
    last_error = None

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            data = json.loads(response.text)
            break
        except Exception as e:
            print(f"Gemini error (attempt {attempt + 1}): {e}")
            last_error = e
            time.sleep(2)

    if data is None:
        raise HTTPException(status_code=503, detail=f"AI busy, try again: {last_error}")

    if isinstance(data, list) and len(data) > 0:
        data = data[0]

    if not isinstance(data, dict) or all(v is None for v in data.values()):
        text = "Tell me what you want, for example: red shoes size 8 under 2000"
        return {
            "status": "need_more_info",
            "reply": text,
            "message": text,
            "extracted_data": data,
            "products": [],
        }

    size = data.get("size")
    max_price = data.get("max_price")

    try:
        max_price = float(max_price) if max_price is not None else None
    except (ValueError, TypeError):
        max_price = None

    products = search_products(
        category=data.get("category"),
        color=data.get("color"),
        size=str(size) if size is not None else None,
        max_price=max_price,
    )

    if not products:
        text = "Sorry, no matching products found. Try a different color, size or price."
        return {
            "status": "no_results",
            "reply": text,
            "message": text,
            "extracted_data": data,
            "products": [],
        }

    return {
        "status": "success",
        "reply": f"I found {len(products)} matching product(s) for you.",
        "extracted_data": data,
        "products": products,
    }
