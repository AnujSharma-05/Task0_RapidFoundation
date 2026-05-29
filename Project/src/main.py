import os
import shutil
from typing import List

from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from . import models, schemas, services
from .database import engine, get_db
from .models import Document

from .websocket_manager import manager

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/ping")
async def ping():
    return {"status": "alive", "message": "pong"}



#----upload document----

@app.post("/upload")
async def upload_pdf(
    background_tasks: BackgroundTasks, #This is a special parameter that allows us to run tasks in the background without blocking the main thread. In this case, we will use it to trigger the document processing task after the file is uploaded.(always kept as the first parameter in the function definition)
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
    ): 
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

    #now we trigger the modular rag  service in background

    background_tasks.add_task(services.process_document_task, new_doc.id, file.filename, db) #This line is adding the process_document_task function from the services module to the background tasks. It passes the document id, filename, and database session as arguments to the function. This allows the document processing to happen asynchronously in the background while the API can immediately return a response to the client.
    return new_doc



#----websocket endpoint for notifications----


@app.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket): 
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text() 
    except WebSocketDisconnect:
        manager.disconnect(websocket)







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
