from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path
from database import engine, Base
from routers import (
    auth, users, categories, products, orders, payments, 
    banners, brands, dashboard, settings, backup
)

# 1. បង្កើត database tables ដោយសុវត្ថិភាព
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Database initialization warning: {e}")

app = FastAPI(title="E-Commerce API", version="1.0.0")

# 2. កែសម្រួល CORS ឱ្យត្រូវស្តង់ដារ (អនុញ្ញាត credentials ជាមួយ wildcard regex)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*",  # ដំណើរការបានគ្រប់ domain (localhost, Vercel, Netlify) ដោយមិនប៉ះទង្គិច credentials
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 3. បង្កើត និងកំណត់ Folder uploads ដោយប្រើ Absolute Path
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"

os.makedirs(UPLOAD_DIR / "products", exist_ok=True)
os.makedirs(UPLOAD_DIR / "banners", exist_ok=True)
os.makedirs(UPLOAD_DIR / "brands", exist_ok=True)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# 4. Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(banners.router)
app.include_router(brands.router)
app.include_router(dashboard.router)
app.include_router(settings.router)
app.include_router(backup.router)

@app.get("/")
def root():
    return {"message": "E-Commerce API is running", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)