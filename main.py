import os
import secrets
import io
import base64
from typing import List, Optional
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from telegram import Bot
import qrcode
from bakong_khqr import KHQR

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
ADMIN_USERNAME = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASS", "lavender123")

# ព័ត៌មានគណនីបាគង KHQR
BAKONG_ACCOUNT_ID = os.getenv("BAKONG_ACCOUNT_ID", "your_bakong_id@bkng")
MERCHANT_NAME = os.getenv("MERCHANT_NAME", "Lavender Store")
MERCHANT_CITY = os.getenv("MERCHANT_CITY", "Phnom Penh")

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

# កន្លែងរក្សាទុកប្រវត្តិ Orders
ORDERS_DB = []

# Schemas
class OrderItem(BaseModel):
    product_name: str
    quantity: int
    price: float

class OrderPayload(BaseModel):
    order_id: Optional[str] = None
    items: List[OrderItem]
    total_amount: float
    customer_id: Optional[int] = None
    customer_name: Optional[str] = "អតិថិជន"
    phone: Optional[str] = "មិនបានបញ្ជាក់"
    address: Optional[str] = "មិនបានបញ្ជាក់"
    username: Optional[str] = ""

class KHQRRequest(BaseModel):
    amount: float
    currency: str = "USD"

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

@app.post("/api/generate-khqr")
def generate_khqr(req: KHQRRequest):
    try:
        # បង្កើត Dynamic KHQR String
        khqr = KHQR()
        qr_string = khqr.create_qr(
            bank_account=BAKONG_ACCOUNT_ID,
            merchant_name=MERCHANT_NAME,
            merchant_city=MERCHANT_CITY,
            amount=req.amount,
            currency=req.currency,
            store_label="Lavender Store",
            terminal_label="MiniApp"
        )
        # បំប្លែងទៅជារូបភាព Base64
        qr_img = qrcode.make(qr_string)
        buffer = io.BytesIO()
        qr_img.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return {
            "status": "success",
            "qr_image": f"data:image/png;base64,{qr_base64}",
            "amount": req.amount
        }
    except Exception as e:
        # ប្រសិនបើមានបញ្ហា library khqr បង្កើត Fallback QR សាកល្បង
        fallback_qr = qrcode.make(f"BAKONG:{BAKONG_ACCOUNT_ID}?amount={req.amount}")
        buf = io.BytesIO()
        fallback_qr.save(buf, format="PNG")
        return {
            "status": "success",
            "qr_image": f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}",
            "amount": req.amount
        }

@app.post("/api/orders")
async def place_order(order: OrderPayload):
    if not order.items:
        raise HTTPException(status_code=400, detail="កន្ត្រកទំនិញទទេ!")

    order_id = order.order_id or f"LV-{secrets.randbelow(900000) + 100000}"
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    # រក្សាទុកក្នុង Orders DB
    order_record = {
        "order_id": order_id,
        "items": [item.model_dump() for item in order.items],
        "total_amount": order.total_amount,
        "customer_id": order.customer_id,
        "customer_name": order.customer_name,
        "phone": order.phone,
        "address": order.address,
        "status": "បានទូទាត់ (KHQR)",
        "created_at": created_at
    }
    ORDERS_DB.insert(0, order_record)

    items_text = "\n".join([
        f"• {item.product_name} x {item.quantity} = ${item.price * item.quantity:.2f}"
        for item in order.items
    ])
    
    admin_message = (
        f"🌸 *ការបញ្ជាទិញថ្មីពី Lavender Store!*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🧾 លេខវិក្កយបត្រ: `{order_id}`\n"
        f"👤 អ្នកទិញ: *{order.customer_name}* "
        f"{'(@' + order.username + ')' if order.username else ''}\n"
        f"📞 ទូរស័ព្ទ: `{order.phone}`\n"
        f"📍 ទីតាំងដឹកជញ្ជូន: {order.address}\n\n"
        f"📦 *ទំនិញកុម្ម៉ង់:*\n{items_text}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 *ទឹកប្រាក់សរុប:* `${order.total_amount:.2f}`\n"
        f"💳 វិធីសាស្ត្រ: Bakong KHQR"
    )

    customer_message = (
        f"🌸 *អរគុណសម្រាប់ការបញ្ជាទិញនៅ Lavender Store!*\n\n"
        f"សួស្ដី {order.customer_name} ការបញ្ជាទិញលេខ `{order_id}` របស់អ្នកទទួលបានជោគជ័យ៖\n\n"
        f"{items_text}\n\n"
        f"💵 *ទឹកប្រាក់សរុប:* `${order.total_amount:.2f}`\n"
        f"📍 ទីតាំងដឹកជញ្ជូន: {order.address}\n"
        f"📞 ទូរស័ព្ទទំនាក់ទំនង: {order.phone}\n\n"
        f"យើងខ្ញុំនឹងរៀបចំដឹកជញ្ជូនជូនលោកអ្នកឆាប់ៗនេះ!"
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

    return {"status": "success", "order_id": order_id, "message": "ការបញ្ជាទិញទទួលបានជោគជ័យ"}

@app.get("/api/orders/user/{customer_id}")
def get_user_orders(customer_id: int):
    # ទាញយកប្រវត្តិ Orders របស់ User ជាក់លាក់
    user_orders = [o for o in ORDERS_DB if o.get("customer_id") == customer_id]
    return user_orders

# ----------------- Admin Routes -----------------

@app.get("/admin")
def serve_admin(user: str = Depends(verify_admin)):
    return FileResponse("admin.html")

@app.get("/api/admin/orders")
def get_all_orders(user: str = Depends(verify_admin)):
    return ORDERS_DB

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