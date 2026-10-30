from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# អនុញ្ញាតឱ្យ Frontend អាចទាញទិន្នន័យបានដោយមិនជាប់បញ្ហា CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# បញ្ជីផលិតផលគំរូសាកល្បង
products = [
    {
        "id": 1, 
        "name": "អាវយឺត Classic T-Shirt", 
        "price": 10.0, 
        "image": "https://placehold.co/200x200/png"
    },
    {
        "id": 2, 
        "name": "កាបូបស្ពាយ Backpack", 
        "price": 25.0, 
        "image": "https://placehold.co/200x200/png"
    }
]

@app.get("/")
def home():
    return {"message": "Python API កំពុងដំណើរការយ៉ាងរលូន!"}

@app.get("/api/products")
def get_products():
    return products