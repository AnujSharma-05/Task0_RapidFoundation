#This is where "Hidden Chef" lives and does the tasks for us. It is responsible for handling the business logic but in asynchronous way.


import asyncio
from sqlalchemy.orm import Session
from .websocket_manager import manager
from . import models

async def process_document_task(doc_id: int, filename: str, db: Session):
    """
    Modular Logic for RAG processing.
    """
    try:
        # Step 1: Simulate Parsing
        await asyncio.sleep(3)
        await manager.broadcast(f" {filename}: Text extraction started...")

        # Step 2: Update Status in Postgres
        # We find the doc and change status from 'uploaded' to 'processing'
        doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
        if doc:
            doc.status = "processing"
            db.commit()

        await asyncio.sleep(3)
        await manager.broadcast(f" {filename}: Generating Embeddings...")

        # Step 3: Finalize
        await asyncio.sleep(2)
        if doc:
            doc.status = "ready"
            db.commit()
            
        await manager.broadcast(f" {filename} is now ready for AI chat.")
        
    except Exception as e:
        await manager.broadcast(f" Error processing {filename}: {str(e)}")


#what this function does is it takes the document id, filename and database session as input and then it simulates the processing of the document in three steps: text extraction, generating embeddings and finalizing. During each step, it updates the status of the document in the database and broadcasts messages to all connected WebSocket clients to keep them informed about the progress. If any error occurs during processing, it catches the exception and broadcasts an error message.

#why are we statically sleeping? Because we are simulating the time taken for each step of the RAG process. In a real implementation, you would replace these sleep calls with actual logic to extract text, generate embeddings, and finalize the document processing. 
