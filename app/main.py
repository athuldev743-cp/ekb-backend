from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from app.auth import router as auth_router
from app.admin import router as admin_router
from app.products import router as product_router
from app.orders import router as order_router

app = FastAPI()

# -------------------- CORS --------------------
origins = [
    "https://ekabhumi.vercel.app",
    "http://localhost:3000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

# -------------------- Routers --------------------
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
app.include_router(product_router, prefix="/products", tags=["Products"])
app.include_router(order_router, prefix="/orders", tags=["Orders"])

# -------------------- Root Redirect --------------------
@app.get("/")
async def root():
    return {"message": "EKB Backend API", "status": "running"}

# Remove automatic trailing slash redirects
@app.get("/{path:path}")
async def catch_all(path: str):
    if path.endswith("/"):
        # Return JSON instead of redirect
        return {"error": f"Endpoint {path} not found. Try without trailing slash."}
    # Let FastAPI handle the actual 404
    raise HTTPException(status_code=404, detail="Not Found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)