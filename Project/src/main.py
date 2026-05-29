import os
import shutil
from typing import List

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from . import models, schemas
from .database import engine, get_db
from .models import Document

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/ping")
async def ping():
    return {"status": "alive", "message": "pong"}


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are allowed.")

    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    new_doc = Document(
        filename=file.filename,
        file_path=file_path,
        status="uploaded",
    )

    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    return {
        "id": new_doc.id,
        "filename": new_doc.filename,
        "status": new_doc.status,
        "file_size": file_size,
    }


@app.get("/documents", response_model=List[schemas.DocumentResponse])
async def get_documents(db: Session = Depends(get_db)):
    docs = db.query(models.Document).all()

    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "status": doc.status,
            "file_size": os.path.getsize(doc.file_path) if doc.file_path and os.path.exists(doc.file_path) else 0,
        }
        for doc in docs
    ]
