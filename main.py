import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from telegram import Bot

# ទាញយក Environment Variables ពី file .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

if not BOT_TOKEN:
    raise ValueError("សូមពិនិត្យមើល BOT_TOKEN ក្នុង file .env មិនទាន់បានកំណត់ទេ!")

bot = Bot(token=BOT_TOKEN)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

products = [
    {"id": 1, "name": "អាវយឺត Classic T-Shirt", "price": 10.0, "image": "https://placehold.co/200x200/png"},
    {"id": 2, "name": "កាបូបស្ពាយ Backpack", "price": 25.0, "image": "https://placehold.co/200x200/png"}
]

@app.get("/")
def serve_home():
    return FileResponse("index.html")

@app.get("/api/products")
def get_products():
    return products

class OrderItem(BaseModel):
    product_name: str
    quantity: int
    price: float

class OrderPayload(BaseModel):
    items: list[OrderItem]
    total_amount: float
    customer_name: str | None = "អតិថិជន"

@app.post("/api/orders")
async def place_order(order: OrderPayload):
    order_details = "\n".join([f"- {item.product_name} x {item.quantity} = ${item.price * item.quantity:.2f}" for item in order.items])
    message_text = (
        f"🔔 *មានការបញ្ជាទិញថ្មី!*\n\n"
        f"👤 អ្នកទិញ: *{order.customer_name}*\n"
        f"📦 ទំនិញ:\n{order_details}\n\n"
        f"💰 សរុប: *${order.total_amount:.2f}*"
    )

    try:
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=message_text, parse_mode="Markdown")
        return {"status": "success", "message": "ការបញ្ជាទិញទទួលបានជោគជ័យ"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))