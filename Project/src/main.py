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



#----upload document----

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)): #depends upon
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
        file_size=file_size,
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



#----get all documents----

@app.get("/documents", response_model=List[schemas.DocumentResponse])
async def get_documents(db: Session = Depends(get_db)):
    docs = db.query(models.Document).all()

    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "status": doc.status,
            "file_size": doc.file_size if getattr(doc, "file_size", None) is not None else (os.path.getsize(doc.file_path) if doc.file_path and os.path.exists(doc.file_path) else 0), #Explaination of this line: This line is checking if the file_size attribute exists on the doc object and is not None. If it does exist and is not None, it uses that value. If it does not exist or is None, it checks if the file_path attribute exists and if the file at that path exists. If both conditions are true, it gets the size of the file using os.path.getsize(doc.file_path). If either condition is false, it defaults to 0. This ensures that we have a valid file size value even if the file_size attribute is missing or None, or if the file itself is missing.
        }
        for doc in docs
    ]
