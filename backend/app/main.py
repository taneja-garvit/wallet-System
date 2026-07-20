from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, wallet, transactions

from anyio import to_thread

app = FastAPI(
    title="Wallet System",
    description="Digital wallet system with INR currency",
    version="3.0.0"
)

@app.on_event("startup")
async def startup():
    limiter = to_thread.current_default_thread_limiter()
    limiter.total_tokens = 200

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174", 
        "http://localhost:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(wallet.router)
app.include_router(transactions.router)

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "3.0.0", "currency": "INR"}
