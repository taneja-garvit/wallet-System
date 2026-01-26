from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, wallet, transactions

app = FastAPI(title="Wallet System")

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
