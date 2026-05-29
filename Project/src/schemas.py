from pydantic import BaseModel

class DocumentResponse(BaseModel): #This is the response model for the document upload endpoint. It defines the structure of the response that will be returned when a document is uploaded.
    id: int
    filename: str
    status: str
    file_size: int