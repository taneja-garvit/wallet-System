from fastapi import FastAPI
from app.api import auth, wallet, transactions

app = FastAPI(title="Wallet System")

app.include_router(auth.router)
app.include_router(wallet.router)
app.include_router(transactions.router)
