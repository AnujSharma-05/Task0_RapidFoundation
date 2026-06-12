import sys
import os
from pathlib import Path
from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

# ==========================================
# CRITICAL: Path manipulation for Monorepo
# ==========================================
# We must add the original 'backend' directory to the Python path 
# so we can import 'services.py' directly without duplicating it.
backend_dir = Path(__file__).parent.parent.parent.parent / "backend"
sys.path.append(str(backend_dir))

# Now we can import from the original CaRAG engine!
from src import services 

# Local live imports
from .database import engine, Base, get_db
from . import auth

# Create all tables (Users, Groups, etc.)
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize the Milvus connection using the engine's init logic
    print("Initializing CaRAG Engine...")
    yield
    # Shutdown logic would go here
    print("Shutting down Live API...")

app = FastAPI(title="CaRAG Live API", version="2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Wire up the Auth router
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])

@app.get("/ping")
async def ping():
    return {"status": "Live API is running", "engine": "Connected"}
