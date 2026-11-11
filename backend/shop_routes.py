"""
Buyer-side chat search.
Put this file in backend/ (next to main.py, db.py, paypal_routes.py).

POST /shop-chat   {"message": "red kurta"}
-> {
     "status": "found" | "similar" | "related" | "none" | "no_query",
     "reply": "text to show in chat",
     "products": [{id, name, category, color, size, price, stock}, ...]
   }
"""
import os
import re
import json
import time

from dotenv import load_dotenv
from fastapi import APIRouter
from google import genai
from google.genai import types
from pydantic import BaseModel

from backend.db import get_conn

load_dotenv()

router = APIRouter()

# 15 second timeout so a busy Gemini never makes the chat hang
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options=types.HttpOptions(timeout=15000),
)
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

COLORS = [
    "black", "white", "brown", "red", "blue", "grey", "green",
    "yellow", "pink", "orange", "purple", "navy",
]
ITEM_WORDS = [
    "sneakers", "shoes", "sandals", "boots", "loafers", "jacket", "t-shirt",
    "shirt", "polo", "jeans", "trousers", "hoodie", "kurta", "kurthi", "kurti",
    "clothes", "clothing",
]
SHOE_WORDS = {"shoe", "sneaker", "sandal", "boot", "loafer"}
# Generic words that mean a whole category, not a product name
GENERIC_SHOES = {"shoe", "footwear"}
GENERIC_CLOTHES = {"cloth", "clothe", "clothing", "clothes", "dress"}


class ShopMessage(BaseModel):
    message: str


# ---------- understanding the message ----------

def normalize_keyword(k):
    if not k:
        return None
    k = str(k).lower().strip()
    if k in ("kurthi", "kurti", "kurtha", "kurta", "kurtas", "kurthis"):
        k = "kurta"
    if k in ("clothes", "clothing"):
        return k
    if len(k) > 3 and k.endswith("s"):
        k = k[:-1]
    return k or None


def clean_filters(raw):
    keyword = normalize_keyword(raw.get("keyword"))
    category = raw.get("category")
    category = category.lower().strip() if isinstance(category, str) else None
    if category not in ("shoes", "clothing"):
        category = None

    # "shoes" / "clothes" are categories, not product names.
    # Without this, "black shoes" would miss "Black Sneakers" and "Black Sandals".
    if keyword in GENERIC_SHOES:
        keyword, category = None, "shoes"
    elif keyword in GENERIC_CLOTHES:
        keyword, category = None, "clothing"
    elif category is None and keyword in SHOE_WORDS:
        category = "shoes"

    color = raw.get("color")
    color = color.lower().strip() if isinstance(color, str) else None
    if color not in COLORS:
        color = None

    size = raw.get("size")
    size = str(size).upper().strip() if size not in (None, "", "null") else None

    max_price = raw.get("max_price")
    try:
        max_price = float(max_price) if max_price not in (None, "", "null") else None
    except (TypeError, ValueError):
        max_price = None

    return {
        "keyword": keyword,
        "category": category,
        "color": color,
        "size": size,
        "max_price": max_price,
    }


def extract_with_gemini(message):
    prompt = f"""
A shopper wrote this message to a clothing and shoe store: "{message}"
The message may be in Telugu, English, or mixed.
Return a JSON object with exactly these keys:
{{
  "keyword": "the item they want in English, singular, e.g. kurta, hoodie, sneaker, jeans, shoes, or null",
  "category": "shoes" or "clothing" or null,
  "color": "english color name in lowercase or null",
  "size": "size as a string or null",
  "max_price": number in dollars or null
}}
Kurta/kurthi/kurti is clothing. Return only JSON.
"""
    last_error = None
    for _ in range(2):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )
            data = json.loads(response.text)
            if isinstance(data, list) and data:
                data = data[0]
            if not isinstance(data, dict):
                raise ValueError("Gemini did not return a JSON object")
            return data
        except Exception as e:  # noqa: BLE001
            last_error = e
            time.sleep(1)
    raise RuntimeError(last_error)


def extract_with_rules(message):
    """Simple backup if Gemini is busy, so the demo never breaks."""
    text = message.lower()
    color = next((c for c in COLORS if re.search(rf"\b{c}\b", text)), None)
    keyword = next((w for w in ITEM_WORDS if w in text), None)

    price = None
    m = re.search(r"(?:under|below|less than|max|upto|up to|<)\s*\$?\s*(\d+)", text)
    if not m:
        m = re.search(r"\$\s*(\d+)", text)
    if not m:
        m = re.search(r"(\d+)\s*(?:dollars?|usd)", text)
    if m:
        price = float(m.group(1))

    size = None
    m = re.search(r"size\s*[:\-]?\s*([a-z0-9]+)", text)
    if m:
        size = m.group(1)

    return {"keyword": keyword, "category": None, "color": color, "size": size, "max_price": price}


def get_filters(message):
    try:
        raw = extract_with_gemini(message)
    except Exception:  # noqa: BLE001
        raw = extract_with_rules(message)
    filters = clean_filters(raw)
    # If Gemini returned nothing useful, try the simple rules too
    if not any(filters.values()):
        filters = clean_filters(extract_with_rules(message))
    return filters


# ---------- searching the database ----------

def run_query(keyword=None, category=None, color=None, size=None, max_price=None, limit=6):
    q = "SELECT * FROM products WHERE stock > 0"
    params = []
    if keyword:
        q += " AND LOWER(name) LIKE ?"
        params.append(f"%{keyword}%")
    if category:
        q += " AND category = ?"
        params.append(category)
    if color:
        q += " AND color = ?"
        params.append(color)
    if size:
        q += " AND UPPER(size) = ?"
        params.append(size)
    if max_price is not None:
        q += " AND price <= ?"
        params.append(max_price)
    q += " ORDER BY price LIMIT ?"
    params.append(limit)

    conn = get_conn()
    rows = [dict(r) for r in conn.execute(q, params).fetchall()]
    conn.close()
    return rows


def smart_search(f):
    """Returns (status, products). Tries exact first, then looser matches."""
    keyword, category = f["keyword"], f["category"]

    # 1. exact match on everything the shopper asked for
    exact = run_query(
        keyword=keyword,
        category=None if keyword else category,
        color=f["color"],
        size=f["size"],
        max_price=f["max_price"],
    )
    if exact:
        return "found", exact

    # 2. same item, but other colors / sizes / prices
    if keyword:
        similar = run_query(keyword=keyword)
        if similar:
            return "similar", similar

    # 3. related: same category and color
    if category and f["color"]:
        related = run_query(category=category, color=f["color"])
        if related:
            return "related", related

    # 4. related: same category
    if category:
        related = run_query(category=category)
        if related:
            return "related", related

    # 5. related: same color only
    if f["color"]:
        related = run_query(color=f["color"])
        if related:
            return "related", related

    return "none", []


def build_reply(status, f):
    wanted = " ".join(x for x in [f["color"], f["keyword"] or f["category"]] if x) or "that item"
    if status == "found":
        return f"Here's what I found for “{wanted}”:"
    if status == "similar":
        return (
            f"Sorry, “{wanted}” isn't available exactly as you asked. "
            f"Here are other {f['keyword']} options:"
        )
    if status == "related":
        return f"Sorry, “{wanted}” is not available right now. Here are some related products:"
    return f"Sorry, “{wanted}” is not available. You can try asking for shoes or clothing."


@router.post("/shop-chat")
def shop_chat(body: ShopMessage):
    message = body.message.strip()
    filters = get_filters(message)

    if not any(filters.values()):
        return {
            "status": "no_query",
            "reply": "Tell me what you're looking for, for example: “black shoes under $50” or “red hoodie”.",
            "products": [],
        }

    status, products = smart_search(filters)
    return {
        "status": status,
        "reply": build_reply(status, filters),
        "products": products,
    }
