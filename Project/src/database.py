import os

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")
import os

print("DATABASE_URL =", os.getenv("DATABASE_URL"))
print("MILVUS_LITE_DB =", os.getenv("MILVUS_LITE_DB"))
print("MILVUS_COLLECTION =", os.getenv("MILVUS_COLLECTION"))
print("EMBEDDING_MODEL =", os.getenv("EMBEDDING_MODEL"))
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Add it to your .env file.")

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()  # every other model will inherit from this base class

def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()
