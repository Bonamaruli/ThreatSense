from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import url_scan, email_scan, file_scan
from app.database import engine, Base
from app.routers import dashboard  # Tambahkan di import
 
# Buat semua tabel di database
Base.metadata.create_all(bind=engine)
 
app = FastAPI(
    title='ThreatSense API',
    description='Multi-Vector Malicious Content Detection',
    version='1.0.0'
)
 
# Izinkan akses dari frontend Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],
    allow_methods=['*'],
    allow_headers=['*'],
)
 
# Register routes
app.include_router(url_scan.router, prefix='/api/scan', tags=['URL Scan'])
app.include_router(email_scan.router, prefix='/api/scan', tags=['Email Scan'])
app.include_router(file_scan.router, prefix='/api/scan', tags=['File Scan'])
# Register dashboard router
app.include_router(dashboard.router, prefix='/api/dashboard', tags=['Dashboard'])
 
@app.get('/')
def read_root():
    return {'status': 'ThreatSense API is running', 'version': '1.0.0'}
