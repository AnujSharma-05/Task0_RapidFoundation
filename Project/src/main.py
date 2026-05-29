from fastapi import FastAPI, UploadFile, File, HTTPException
from .schemas import DocumentResponse

app = FastAPI()

@app.get("/ping")
async def ping():
    return {"status":"alive", "message": "pong"}

@app.post("/upload", response_model=DocumentResponse)
async def upload_pdf(file: UploadFile):
    #validate the content type of the uploaded file
    if file.content_type != "application/pdf": #application/pdf is the MIME type for PDF files. This check ensures that only PDF files are accepted for upload.
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are allowed.")


    #lets do the size check
    file.file.seek(0,2) # Move file pointer to the end of the file to get its size.
    file_size = file.file.tell() #curr pos of the pointer -> gives file size in bytes
    file.file.seek(0) # pointer to the beginning


    doc_id = 101

    return DocumentResponse(
        id=doc_id,
        filename=file.filename,
        status="recieved",
        file_size=file_size
    )

    