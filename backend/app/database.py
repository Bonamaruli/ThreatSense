from sqlalchemy import create_engine
# declarative_base pindah ke sqlalchemy.orm sejak SQLAlchemy 2.0.
# Lokasi lamanya masih jalan tapi memunculkan peringatan setiap aplikasi start.
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# Ambil DATABASE_URL dari config (dengan fallback ke default)
DATABASE_URL = settings.DATABASE_URL

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