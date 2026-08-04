import os

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional, List

# Jalur ke .env dipatok ABSOLUT, dihitung dari lokasi berkas ini.
#
# KENAPA TIDAK CUKUP MENULIS ".env" SAJA:
# Tulisan ".env" dicari relatif terhadap folder tempat kamu berdiri saat
# menjalankan perintah, bukan relatif terhadap berkas ini. Jadi:
#
#     dijalankan dari backend/  -> .env ketemu   -> pakai PostgreSQL
#     dijalankan dari root/     -> .env TIDAK ketemu -> diam-diam pakai
#                                  nilai bawaan sqlite:///./threatsense.db
#
# Yang berbahaya, kegagalan ini TIDAK memunculkan peringatan apa pun. Aplikasi
# tetap menyala, tapi menunjuk database yang sama sekali berbeda dan kosong.
# Di project ini kebetulan langsung kelihatan karena SQLite tidak mengenal
# tipe kolom JSONB sehingga crash - kalau tidak, datanya akan terlihat
# "hilang" tanpa penjelasan.
#
# config.py ada di backend/app/, jadi naik dua tingkat untuk sampai ke backend/
_ENV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"
)

class Settings(BaseSettings):
    """
    Configuration settings untuk aplikasi ThreatSense
    """
    
    # Application
    APP_NAME: str = "ThreatSense API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite:///./threatsense.db"
    
    # Redis
    REDIS_URL: Optional[str] = None
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Rate Limiting & File Upload (Opsional, disesuaikan dengan main.py/router)
    RATE_LIMIT_PER_MINUTE: int = 60
    MAX_FILE_SIZE: int = 10 * 1024 * 1024
    ALLOWED_FILE_TYPES: List[str] = [
        "application/pdf", "image/jpeg", "image/png", "text/plain",
        "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    
    # ML Settings
    MODEL_PATH: Optional[str] = None
    MLFLOW_TRACKING_URI: Optional[str] = None

    # KUNCI UTAMA: extra="ignore" akan mematikan error extra_forbidden!
    model_config = ConfigDict(
        env_file=_ENV_PATH,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

# Create singleton instance
settings = Settings()