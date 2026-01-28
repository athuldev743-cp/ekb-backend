from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth import router as auth_router
from app.admin import router as admin_router
from app.products import router as product_router
from app.orders import router as order_router

app = FastAPI()

# -------------------- CORS --------------------
# FIX: Add all necessary origins and remove trailing slashes
origins = [
    "https://ekabhumi.vercel.app",      # Production
    "http://localhost:3000",            # React dev
    "http://localhost:5173",            # Vite dev
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
    expose_headers=["*"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# -------------------- Routers --------------------
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
app.include_router(product_router, prefix="/products", tags=["Products"])
app.include_router(order_router, prefix="/orders", tags=["Orders"])

@app.get("/")
async def root():
    return {"message": "EKB Backend API", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)