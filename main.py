import os
import secrets
from typing import List, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from telegram import Bot

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
ADMIN_USERNAME = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASS", "lavender123")

if not BOT_TOKEN:
    raise ValueError("សូមពិនិត្យមើល BOT_TOKEN ក្នុង file .env ឬ Environment Variables!")

bot = Bot(token=BOT_TOKEN)
security = HTTPBasic()
app = FastAPI(title="Lavender Store API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ផ្ទៀងផ្ទាត់សិទ្ធិអ្នកគ្រប់គ្រង (Admin Authentication)
def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ឈ្មោះ ឬលេខសម្ងាត់មិនត្រឹមត្រូវ",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# ទិន្នន័យទំនិញគ្រប់មុខសម្រាប់ Lavender Store
PRODUCTS = [
    {
        "id": 1,
        "name": "ទឹកអប់ Lavender Blossom 50ml",
        "category": "beauty",
        "price": 28.50,
        "image": "https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?w=400&auto=format&fit=crop&q=80"
    },
    {
        "id": 2,
        "name": "សាប៊ូដុសខ្លួន Organic Lavender",
        "category": "beauty",
        "price": 8.00,
        "image": "https://images.unsplash.com/photo-1607006314041-9d22be223297?w=400&auto=format&fit=crop&q=80"
    },
    {
        "id": 3,
        "name": "អាវយឺតដៃខ្លី Oversized Pastel",
        "category": "fashion",
        "price": 14.00,
        "image": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=400&auto=format&fit=crop&q=80"
    },
    {
        "id": 4,
        "name": "កាបូបស្ពាយ Canvas Tote Bag",
        "category": "fashion",
        "price": 11.50,
        "image": "https://images.unsplash.com/photo-1544816155-12df9643f363?w=400&auto=format&fit=crop&q=80"
    },
    {
        "id": 5,
        "name": "កាសឥតខ្សែ Bluetooth Earbuds Pro",
        "category": "electronics",
        "price": 35.00,
        "image": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=400&auto=format&fit=crop&q=80"
    },
    {
        "id": 6,
        "name": "ឧបករណ៍សាកថ្ម MagSafe Power Bank",
        "category": "electronics",
        "price": 24.00,
        "image": "https://images.unsplash.com/photo-1622445262464-84b1456045b6?w=400&auto=format&fit=crop&q=80"
    }
]

# Schemas
class OrderItem(BaseModel):
    product_name: str
    quantity: int
    price: float

class OrderPayload(BaseModel):
    items: List[OrderItem]
    total_amount: float
    customer_id: Optional[int] = None
    customer_name: Optional[str] = "អតិថិជន"
    username: Optional[str] = ""

class ProductSchema(BaseModel):
    name: str
    category: str
    price: float
    image: str

# ----------------- Store Front Routes -----------------

@app.get("/")
def serve_home():
    return FileResponse("index.html")

@app.get("/api/products")
def get_products():
    return PRODUCTS

@app.post("/api/orders")
async def place_order(order: OrderPayload):
    if not order.items:
        raise HTTPException(status_code=400, detail="កន្ត្រកទំនិញទទេ!")

    items_text = "\n".join([
        f"• {item.product_name} x {item.quantity} = ${item.price * item.quantity:.2f}"
        for item in order.items
    ])
    
    admin_message = (
        f"🌸 *ការបញ្ជាទិញថ្មីពី Lavender Store!*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 អ្នកទិញ: *{order.customer_name}* "
        f"{'(@' + order.username + ')' if order.username else ''}\n"
        f"🆔 Telegram ID: `{order.customer_id}`\n\n"
        f"📦 *ទំនិញកុម្ម៉ង់:*\n{items_text}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 *ទឹកប្រាក់សរុប:* `${order.total_amount:.2f}`\n"
        f"🕒 ស្ថានភាព: មិនទាន់ទូទាត់ប្រាក់"
    )

    customer_message = (
        f"🌸 *អរគុណសម្រាប់ការបញ្ជាទិញនៅ Lavender Store!*\n\n"
        f"សួស្ដី {order.customer_name} ការបញ្ជាទិញរបស់អ្នកត្រូវបានកត់ត្រាទុក៖\n\n"
        f"{items_text}\n\n"
        f"💵 *ទឹកប្រាក់សរុប:* `${order.total_amount:.2f}`\n\n"
        f"បុគ្គលិករបស់យើងនឹងទាក់ទងមកអ្នកតាម Chat នេះក្នុងពេលបន្តិចទៀត។"
    )

    if ADMIN_CHAT_ID:
        try:
            await bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message, parse_mode="Markdown")
        except Exception as e:
            print(f"Error sending message to admin: {e}")

    if order.customer_id:
        try:
            await bot.send_message(chat_id=order.customer_id, text=customer_message, parse_mode="Markdown")
        except Exception as e:
            print(f"Customer error: {e}")

    return {"status": "success", "message": "ការបញ្ជាទិញទទួលបានជោគជ័យ"}

# ----------------- Admin Routes -----------------

@app.get("/admin")
def serve_admin(user: str = Depends(verify_admin)):
    return FileResponse("admin.html")

@app.post("/api/admin/products")
def add_product(prod: ProductSchema, user: str = Depends(verify_admin)):
    new_id = max([p["id"] for p in PRODUCTS], default=0) + 1
    new_item = {
        "id": new_id,
        "name": prod.name,
        "category": prod.category,
        "price": prod.price,
        "image": prod.image
    }
    PRODUCTS.append(new_item)
    return {"status": "success", "product": new_item}

@app.delete("/api/admin/products/{product_id}")
def delete_product(product_id: int, user: str = Depends(verify_admin)):
    global PRODUCTS
    PRODUCTS = [p for p in PRODUCTS if p["id"] != product_id]
    return {"status": "success", "message": "ទំនិញត្រូវបានលុបជោគជ័យ"}