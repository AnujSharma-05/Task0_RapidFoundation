#schemas.py vs models.py
#In the context of a FastAPI application, the terms "schemas" and "models" can sometimes be used interchangeably, but they often refer to different concepts: 
#- "Schemas" are used for data validation and serialization (e.g., Pydantic models).
#- "Models" are used for database interactions (e.g., SQLAlchemy models).



from sqlalchemy import Column, Integer, String, DateTime
from .database import Base
from datetime import datetime

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    file_path = Column(String)
    status = Column(String, default="uploaded")
    created_at = Column(DateTime, default=datetime.utcnow)
    table_args = {"extend_existing": True}



    #the actual files are store locally in computer, just the address string are in the db for fetching.abs

