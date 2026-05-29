import os
import shutil

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from . import models, schemas
from .database import engine, get_db
from .models import Document

from typing import List 

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/ping")
async def ping():
    return {"status":"alive", "message": "pong"}


    # -----------------UPLOAD ENDPOINT-----------------

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    #validate the content type of the uploaded file
    if file.content_type != "application/pdf": #application/pdf is the MIME type for PDF files. This check ensures that only PDF files are accepted for upload.
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are allowed.")

    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True) 

    file_path = os.path.join(upload_dir, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer) 

    new_doc = Document(
        filename = file.filename,
        file_path = file_path,
        status = "uploaded"
    )

    # Calculate file size before saving
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0) # Reset file pointer to the beginning after calculating size


    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)


    return {
        "id": new_doc.id,
        "filename": new_doc.filename,
        "status": new_doc.status,
        "file_size": file_size
        }


#-----------------GET DOCUMENTS ENDPOINT-----------------

@app.get("/documents", response_model=List[schemas.DocumentResponse])
async def get_documents(db: Session = Depends(get_db)):
        docs = db.query(models.Document).all()
        return docs