from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

from app.routers import auth, groups, expenses, balances, settlements, import_csv

app = FastAPI(title="Shared Expenses API")

app.include_router(auth.router)
app.include_router(groups.router)
app.include_router(expenses.router)
app.include_router(balances.router)
app.include_router(settlements.router)
app.include_router(import_csv.router)

# Explicit CORS Origins
origins = [
    os.getenv("FRONTEND_URL", "http://localhost:5173"), 
    # Vercel deployment URL should be added here via env var
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    """
    Root endpoint for health checks.
    """
    return {"message": "Shared Expenses API is running"}
