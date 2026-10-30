import os
from typing import List, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from telegram import Bot

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

if not BOT_TOKEN:
    raise ValueError("សូមពិនិត្យមើល BOT_TOKEN ក្នុង file .env ឬ Environment Variables!")

bot = Bot(token=BOT_TOKEN)
app = FastAPI(title="Lavender Store API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

    # រៀបចំទម្រង់អត្ថបទវិក្កយបត្រ
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

    # ១. ផ្ញើ Alert ទៅកាន់អ្នកលក់ (Admin)
    if ADMIN_CHAT_ID:
        try:
            await bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message, parse_mode="Markdown")
        except Exception as e:
            print(f"Error sending message to admin: {e}")

    # ២. ផ្ញើវិក្កយបត្រទៅកាន់អតិថិជនវិញ (ប្រសិនបើមាន Telegram ID)
    if order.customer_id:
        try:
            await bot.send_message(chat_id=order.customer_id, text=customer_message, parse_mode="Markdown")
        except Exception as e:
            print(f"Customer hasn't started the bot or error: {e}")

    return {"status": "success", "message": "ការបញ្ជាទិញទទួលបានជោគជ័យ"}