import os
import time
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from backend.paypal_routes import router as paypal_router

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI(title="SamvaadPay Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(paypal_router)

class ChatMessage(BaseModel):
    message: str

@app.get("/")
def home():
    return {"status": "success", "message": "SamvaadPay AI Engine is Live!"}

@app.post("/chat")
def chat_with_ai(chat_input: ChatMessage):
    prompt = f"""
    A seller wrote this message to sell a product: "{chat_input.message}".
    Extract the item details and return a JSON object with these exact keys:
    {{
        "item_name": "string or null",
        "quantity": "number or null",
        "price": "number or null"
    }}
    The message may be in Telugu, English, or mixed. Price is per one item.
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
            last_error = e
            time.sleep(2)

    if data is None:
        raise HTTPException(status_code=503, detail=f"AI busy, try again: {last_error}")

    if data["item_name"] is None or data["price"] is None:
        return {
            "status": "need_more_info",
            "message": "Please tell the product name and price"
        }

    return {
        "status": "success",
        "extracted_data": data
    }
