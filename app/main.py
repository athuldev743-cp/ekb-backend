from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from app.auth import router as auth_router
from app.admin import router as admin_router
from app.products import router as product_router
from app.orders import router as order_router

app = FastAPI()

# CORS Configuration
origins = [
    "https://ekabhumi.vercel.app",
    "http://localhost:3000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
app.include_router(product_router, prefix="/products", tags=["Products"])
app.include_router(order_router, prefix="/orders", tags=["Orders"])

@app.get("/")
async def root():
    return {"message": "EKB Backend API", "status": "running"}