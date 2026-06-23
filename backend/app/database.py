from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Load environment variables dari file .env
load_dotenv()

# Ambil DATABASE_URL dari .env
DATABASE_URL = os.getenv("DATABASE_URL")

# Validasi DATABASE_URL ada
if not DATABASE_URL:
    raise ValueError("DATABASE_URL tidak ditemukan di file .env!")

# Buat engine SQLAlchemy
engine = create_engine(DATABASE_URL)

# Buat session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class untuk semua models
Base = declarative_base()

# Dependency untuk mendapatkan database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()