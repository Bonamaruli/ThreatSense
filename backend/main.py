from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import url_scan, email_scan, file_scan, dashboard
from app.database import engine, Base
from app.config import settings

# Buat semua tabel di database
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description='Multi-Vector Malicious Content Detection',
    version=settings.APP_VERSION
)

# Konfigurasi CORS dari settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Register routes
app.include_router(url_scan.router, prefix='/api/scan', tags=['URL Scan'])
app.include_router(email_scan.router, prefix='/api/scan', tags=['Email Scan'])
app.include_router(file_scan.router, prefix='/api/scan', tags=['File Scan'])
app.include_router(dashboard.router, prefix='/api/dashboard', tags=['Dashboard'])

@app.get('/')
def read_root():
    return {
        'status': f'{settings.APP_NAME} is running',
        'version': settings.APP_VERSION
    }

@app.get('/health')
def health_check():
    """Health check endpoint untuk monitoring"""
    return {'status': 'healthy', 'service': settings.APP_NAME}
