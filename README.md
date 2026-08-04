# ThreatSense

ThreatSense adalah platform keamanan siber berbasis AI untuk mendeteksi ancaman dari:

- URL Scan
- Email Scan
- File Scan
- Dashboard Monitoring

## Teknologi

### Backend
- FastAPI
- SQLAlchemy
- SQLite

### Frontend
- Next.js
- React
- Tailwind CSS

## Menjalankan Backend

Dari folder root project (bisa dari folder mana pun sebenarnya):

```bash
backend\venv\Scripts\python.exe run.py --reload
```

Atau klik dua kali `start-backend.bat`.

Server jalan di http://localhost:8000, dokumentasi API di /docs.

Kalau kamu terbiasa menjalankan dari dalam folder `backend`, dua-duanya jalan:

```bash
uvicorn main:app --reload
```

```bash
uvicorn app.main:app --reload
```

> Aplikasi aslinya ada di `backend/app/main.py`. Berkas `backend/main.py`
> cuma jalan pintas satu baris yang menunjuk ke sana, supaya perintah lama
> `uvicorn main:app` tetap bekerja setelah aplikasinya dipindah.
>
> Keduanya hanya jalan dari DALAM folder `backend`. Dari folder root
> hasilnya `ModuleNotFoundError: No module named 'app'`, karena paket `app`
> berada di dalam `backend/`. Pakai `run.py` kalau ingin bebas dari folder
> mana pun.

### Kalau muncul "Fatal error in launcher"

```
Fatal error in launcher: Unable to create process using
'"C:\path\LAMA\venv\Scripts\python.exe" ...'
```

Ini terjadi kalau folder project pernah **dipindah**. Virtual environment
tidak bisa dipindah: setiap berkas `.exe` di `venv\Scripts\` menyimpan path
lengkap ke `python.exe` di dalam berkasnya, ditulis saat paket dipasang.
Begitu foldernya pindah, ke-37 berkas `.exe` itu rusak sekaligus.

Cirinya khas: `python -m uvicorn ...` tetap jalan, tapi `uvicorn ...` gagal —
karena `python.exe` sendiri tidak menyimpan path apa pun.

Perbaiki dengan klik dua kali `perbaiki-venv.bat`, atau:

```bash
backend\venv\Scripts\python.exe -m pip install --force-reinstall --no-deps uvicorn==0.30.0
```

Kalau virtual environment belum dibuat:

```bash
python -m venv backend\venv
backend\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Kalau database belum ada, buat dulu lewat pgAdmin atau psql:

```bash
psql -U postgres -c "CREATE DATABASE threatsense;"
```

Tabelnya dibuat otomatis saat backend pertama kali dijalankan.

## Menjalankan Frontend

```bash
cd frontend
npm install
npm run dev
```








## Ini bagian PENGERJAAN
📋 DOKUMENTASI PROGRESS BACKEND THREATSENSE
🎯 OVERVIEW PROJECT
ThreatSense adalah platform deteksi ancaman siber multi-vektor berbasis AI untuk Tugas Akhir. Platform ini menganalisis URL, Email, dan File menggunakan Machine Learning untuk mendeteksi ancaman secara real-time.
Tech Stack:
Backend: Python 3.11, FastAPI, SQLAlchemy, PostgreSQL 18, Redis
ML: scikit-learn, XGBoost, LightGBM, SHAP, MLflow
Scraping: Playwright, BeautifulSoup4, httpx
Task Queue: Celery
Auth: python-jose (JWT), passlib (bcrypt)
Frontend: Next.js 16.2.9 (sudah selesai)
📊 STATUS SAAT INI (JUNI 2026)
✅ YANG SUDAH SELESAI:
Struktur Folder Backend - Sudah lengkap dengan semua folder yang diperlukan
Virtual Environment - Python 3.11 dengan semua dependencies terinstall
Database PostgreSQL - Database threatsense sudah dibuat dengan 6 tabel
File Konfigurasi - .env, config.py, database.py sudah ada
Pydantic Schemas - File app/schemas/scan.py sudah dibuat dengan semua model
Service Layer - File app/services/scan_service.py sudah dibuat dengan logika dummy
Routers - Semua router sudah dibuat (url_scan.py, email_scan.py, file_scan.py, dashboard.py)
SQLAlchemy Models - File app/models/threat.py sudah dibuat dengan 3 model (ScanHistory, DomainReputation, FileSignature)
Frontend Next.js - Sudah selesai dan berjalan di http://localhost:3000
✅ SUDAH TERATASI: Error `Could not import module "app.main"`.
File main.py sekarang berada di backend/app/main.py dan backend berjalan
normal dengan `uvicorn app.main:app --reload` dari dalam folder backend/.

✅ FITUR URL SCANNER: SELESAI DAN TERSAMBUNG KE APLIKASI

RIWAYAT MASALAH (penting untuk bab metodologi laporan)

Versi pertama mencetak akurasi 99,55% — dan angka itu palsu. Dataset
PhiUSIIL ternyata bocor secara struktural: dari 235.795 barisnya, NOL URL
legitimate yang memakai http atau punya path. Model tidak belajar ciri
phishing, melainkan cara data dikumpulkan ("ada path berarti berbahaya").
Saat diuji URL sungguhan akurasinya cuma 69,2%, dan github.com/torvalds/linux
divonis berbahaya 99,97%.

CARA MEMPERBAIKINYA

  1. Sisi legitimate diganti dari PhiUSIIL ke Tranco, diambil menyebar dari
     peringkat 1 sampai 1.000.000 (bukan cuma situs terkenal).
  2. Fitur dihitung HANYA dari nama domain. Path dan protokol tidak pernah
     dibaca model, jadi kebocoran seperti itu mustahil terulang — bukan
     karena datanya kebetulan bagus, tapi karena fiturnya tidak bisa melihat
     bagian tersebut.
  3. Setiap dataset wajib lolos check_leakage.py sebelum dipakai training.

ARSITEKTUR AKHIR: TIGA LAPISAN

  Lapisan 1 - Daftar putih  : 100rb domain terpopuler (Tranco)
  Lapisan 2 - Aturan        : judi online, peniruan merek, typosquatting,
                              alamat IP, hosting gratis, akhiran menyamar
  Lapisan 3 - Model ML      : XGBoost, HANYA didengar saat keyakinannya
                              >= 0,90 (di titik itu ketepatannya 97,9%)

Kenapa gabungan, bukan model saja: ditemukan batas keras bahwa menebak dari
nama domain saja mentok di ~64%. Sebabnya sebagian besar phishing menumpang
SITUS SAH YANG DIRETAS (contoh nyata di dataset: aperfectbrow.com,
mygummyjelly.com). Nama domainnya polos — tidak ada model yang bisa
menebaknya tanpa membaca isi halaman.

HASIL PENGUKURAN (diuji dengan data yang tidak dipakai melatih)

  Phishing nyata terdeteksi (OpenPhish, 300 URL) : 76,7%
  Salah vonis - domain aman peringkat >100rb     : 2,0%
  Salah vonis - situs populer peringkat <50rb    : 1,0%
  Holdout 26 URL pilihan                         : 100%

  Sebagai pembanding, versi pertama: 12,3% deteksi dan 12,5% salah vonis.

BATASAN YANG DIAKUI TERBUKA (tulis ini di laporan, jangan disembunyikan)

  - Tidak bisa mendeteksi situs sah yang diretas lalu dititipi halaman
    phishing. Itu butuh analisis isi halaman, bukan analisis nama domain.
  - Penyalahgunaan subdomain tidak dipelajari model, karena data yang
    tersedia berat sebelah. Ditangani sebagian oleh lapisan aturan.
  - Daftar judi disusun manual dari pola nama domain. TrustPositif Komdigi
    tidak bisa dipakai melatih model karena domainnya disensor di sumbernya
    (bentuknya "s****sqq.com"), tapi tetap dipakai menguji cakupan aturan.

PERINTAH YANG SERING DIPAKAI

  python ml/data/download_sources.py     # unduh data mentah (sekali saja)
  python ml/data/build_dataset.py        # susun dataset
  python ml/data/check_leakage.py        # WAJIB lolos sebelum training
  python ml/models/train_model.py        # latih model
  python ml/evaluation/holdout_test.py   # uji dengan URL nyata
📁 STRUKTUR FOLDER BACKEND
C:\Users\Asus\Documents\ThreatSense\backend\
├── app/
│   ├── __init__.py
│   ├── config.py              # Pydantic Settings untuk konfigurasi
│   ├── database.py            # SQLAlchemy engine & session
│   ├── models/
│   │   ├── __init__.py
│   │   └── threat.py          # SQLAlchemy models (ScanHistory, DomainReputation, FileSignature)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── url_scan.py        # POST /api/v1/scan/url
│   │   ├── email_scan.py      # POST /api/v1/scan/email
│   │   ├── file_scan.py       # POST /api/v1/scan/file
│   │   └── dashboard.py       # GET /api/v1/dashboard/stats, /recent
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── scan.py            # Pydantic models untuk request/response
│   └── services/
│       ├── __init__.py
│       └── scan_service.py    # Business logic dengan dummy ML
├── venv/                      # Virtual environment Python 3.11
├── .env                       # Environment variables
├── main.py                    # FastAPI app instance (DI LUAR folder app/)
├── requirements.txt           # Semua dependencies
└── start.bat                  # Script untuk menjalankan server

🔧 KONFIGURASI YANG SUDAH ADA
File .env:
# Database
DATABASE_URL=postgresql://<user>:<password>@localhost:5432/threatsense

# Redis
REDIS_URL=redis://localhost:6379/0

# App Settings
APP_NAME=ThreatSense
DEBUG=True
SECRET_KEY=<isi-dengan-random-string-minimal-32-karakter>

# ML Settings
MODEL_PATH=<path-absolut-ke>/ThreatSense/ml/models
MLFLOW_TRACKING_URI=http://localhost:5000

File config.py (Pydantic Settings):
Menggunakan BaseSettings dari pydantic_settings
Semua field menggunakan UPPERCASE untuk match dengan .env
Konfigurasi: model_config = ConfigDict(env_file=".env", case_sensitive=True, extra="ignore")
File database.py:
SQLAlchemy engine dengan PostgreSQL
SessionLocal untuk database sessions
Base declarative untuk models
File models/threat.py:
ScanHistory: id (UUID), scan_type, input_value, risk_score, threat_label, features_json (JSONB), shap_values (JSONB), created_at
DomainReputation: id, domain, risk_score, threat_type, first_seen, last_scanned, scan_count, confirmed_bad, source
FileSignature: id, sha256_hash, file_type, threat_name, detected_at, source
File schemas/scan.py:
Request schemas: UrlScanRequest, EmailScanRequest, FileScanRequest
Response schemas: UrlScanResponse, EmailScanResponse, FileScanResponse, DashboardStatsResponse, RecentScansResponse
Base schema: ScanResultBase dengan field umum
File services/scan_service.py:
Dummy feature extraction: dummy_extract_features()
Dummy ML prediction: dummy_predict() (jika ada kata "bank", "login" = malicious)
Service functions: process_url_scan(), process_email_scan(), process_file_scan(), get_dashboard_stats(), get_recent_scans()
File main.py:
FastAPI app instance
CORS middleware configured untuk http://localhost:3000
Routers registered dengan prefix /api/v1/scan dan /api/v1
Base.metadata.create_all(bind=engine) untuk auto-create tables
🚧 ROADMAP LENGKAP SAMPAI BACKEND SELESAI
FASE 1: FIX STARTUP ERROR & VALIDASI FONDASI ️ SEKARANG
Tujuan: Membuat backend bisa start dan endpoint bisa diakses
Tahapan:
✅ Identifikasi error Could not import module "app.main"
Fix struktur import atau cara menjalankan uvicorn
⏳ Verifikasi semua endpoint bisa diakses via Swagger UI
⏳ Test end-to-end: Frontend → Backend → Database
⏳ Pastikan data tersimpan di PostgreSQL dengan benar
Kriteria Selesai:
Backend berjalan di http://localhost:8000
Swagger UI accessible di http://localhost:8000/docs
Endpoint POST /api/v1/scan/url return 200 OK
Data tersimpan di tabel scan_history
FASE 2: FEATURE ENGINEERING URL NEXT
Tujuan: Membuat ekstraktor fitur URL yang sesungguhnya (50-100+ fitur)
Tahapan:
Buat folder ml/features/ di root project
Buat file ml/features/url_features.py
Implementasi Lexical Features (20-30 fitur):
Panjang URL, hostname, path
Jumlah dot, slash, dash, underscore, @, ?
Entropy (Shannon entropy untuk keacakan)
Penggunaan IP address vs domain
HTTPS vs HTTP
Jumlah subdomain
Suspicious TLD detection (.tk, .ml, .xyz, .top, dll)
Typosquatting detection
Penggunaan kata kunci mencurigakan (login, bank, secure, verify)
Implementasi Network Features (10-15 fitur):
Domain age via WHOIS lookup
DNS records (A, MX, NS)
IP reputation check
SSL certificate validation
Test feature extraction dengan berbagai URL
Integrasi dengan service layer (ganti dummy_extract_features)
Simpan fitur ke kolom features_json di database
Dependencies yang Perlu Ditambah:
python-whois untuk WHOIS lookup
dnspython untuk DNS queries
tldextract untuk parsing domain
Kriteria Selesai:
Fungsi extract_url_features(url) return dictionary dengan 50+ fitur
Fitur tersimpan di database sebagai JSONB
Response time < 2 detik per URL
FASE 3: DATASET COLLECTION & PREPROCESSING 📊
Tujuan: Mengumpulkan dan mempersiapkan dataset untuk training model
Tahapan:
Download dataset PhishTank (URL phishing)
Download dataset Alexa 1M atau Tranco (URL legitimate)
Download dataset OpenPhish (opsional, untuk validasi)
Preprocessing data:
Cleaning URL (remove duplicates, invalid URLs)
Labeling (1 = phishing, 0 = legitimate)
Split train/test/validation (70/20/10)
Ekstrak fitur untuk semua URL di dataset menggunakan extract_url_features()
Simpan dataset yang sudah diproses ke format CSV/Parquet
Exploratory Data Analysis (EDA):
Distribusi fitur
Correlation analysis
Feature importance awal
Target Dataset:
Minimum 50,000 URL phishing
Minimum 50,000 URL legitimate
Total: 100,000+ samples
Kriteria Selesai:
Dataset siap training dalam format CSV
Semua URL sudah diekstrak fiturnya
EDA report lengkap
FASE 4: TRAINING MACHINE LEARNING MODEL 🤖
Tujuan: Training ensemble model untuk deteksi URL phishing
Tahapan:
Setup MLflow untuk experiment tracking
Train XGBoost classifier:
Hyperparameter tuning (GridSearch/RandomSearch)
Cross-validation (5-fold)
Metrics: Accuracy, Precision, Recall, F1-Score, ROC-AUC
Train LightGBM classifier:
Hyperparameter tuning
Cross-validation
Metrics comparison dengan XGBoost
Train Ensemble Model (stacking/voting):
Combine XGBoost + LightGBM
Weight optimization
Generate SHAP values untuk explainability:
SHAP summary plot
SHAP dependence plot
Feature importance ranking
Save model ke folder ml/models/:
url_phishing_model.pkl
url_feature_scaler.pkl (jika perlu scaling)
url_shap_explainer.pkl
Dokumentasi hasil training:
Model performance metrics
Confusion matrix
ROC curve
Top 20 important features
Target Performance:
Accuracy: > 95%
Precision: > 94%
Recall: > 95%
F1-Score: > 94%
ROC-AUC: > 0.98
Kriteria Selesai:
Model trained dan saved
Performance metrics memenuhi target
SHAP explainer siap digunakan
MLflow experiment logged
FASE 5: INTEGRASI MODEL ML KE BACKEND 🔌
Tujuan: Mengganti dummy ML dengan model asli di backend
Tahapan:
Buat file ml/services/predictor.py:
Load model dari ml/models/
Load SHAP explainer
Function predict_url(url) yang return risk_score, threat_label, shap_values
Update app/services/scan_service.py:
Ganti dummy_predict() dengan predict_url()
Integrasikan SHAP values ke response
Test end-to-end:
Frontend kirim URL
Backend extract features
Model predict
Return hasil dengan SHAP values
Optimasi performance:
Cache model di memory (load sekali saat startup)
Async prediction jika perlu
Update response schema untuk include SHAP values
Kriteria Selesai:
Backend menggunakan model ML asli
Response include SHAP values untuk explainability
Response time < 1 detik per URL
Accuracy sesuai dengan model training
FASE 6: FEATURE ENGINEERING EMAIL 📧
Tujuan: Membuat ekstraktor fitur untuk email phishing detection
Tahapan:
Buat file ml/features/email_features.py
Implementasi Header Analysis (15-20 fitur):
SPF check (Pass/Fail/None)
DKIM check (Pass/Fail/None)
DMARC check (Pass/Fail/None)
From address analysis
Reply-to vs From mismatch
Received headers analysis
Message-ID validity
Implementasi Content Analysis (20-30 fitur):
Link extraction dan analysis
Suspicious keywords count
Urgency language detection
Grammar/spelling errors
HTML vs plain text ratio
Attachment analysis
Implementasi Sender Reputation (5-10 fitur):
Domain age
Domain reputation score
Previous phishing reports
Collect dataset email phishing (Enron, Phishing Corpus)
Train model untuk email classification
Integrasi ke backend
Kriteria Selesai:
Fungsi extract_email_features(email_content) siap
Model email phishing trained
Endpoint /api/v1/scan/email berfungsi dengan ML
FASE 7: FEATURE ENGINEERING FILE
Tujuan: Membuat ekstraktor fitur untuk malware detection
Tahapan:
Buat file ml/features/file_features.py
Implementasi Static Analysis (30-40 fitur):
File type detection (magic bytes)
File entropy (Shannon entropy)
String extraction (printable strings)
PE header analysis (untuk EXE)
Import/Export table analysis
Section analysis
Macro detection (untuk Office docs)
JavaScript detection (untuk PDF)
Implementasi Behavioral Indicators (10-15 fitur):
Suspicious API calls
Registry modifications
Network connections
File system operations
Collect dataset malware (VirusShare, MalwareBazaar)
Train model untuk file classification
Integrasi ke backend dengan file upload handling
Kriteria Selesai:
Fungsi extract_file_features(file_bytes) siap
Model malware detection trained
Endpoint /api/v1/scan/file berfungsi dengan ML
File upload handling dengan size limit
FASE 8: BACKGROUND TASKS & OPTIMIZATION ⚡
Tujuan: Implementasi async processing untuk file scan yang besar
Tahapan:
Setup Celery dengan Redis broker
Buat Celery tasks untuk:
File scanning (async)
Batch URL scanning
Feature extraction (untuk dataset besar)
Implementasi WebSocket untuk real-time progress:
Progress bar untuk file scan
Status update real-time
Implementasi Redis Cache:
Cache domain features (WHOIS, DNS)
Cache scan results (untuk URL yang sama)
Cache model predictions
Rate limiting untuk API endpoints
Logging dan monitoring
Kriteria Selesai:
Celery worker berjalan
File scan async dengan progress update
Redis cache aktif
Response time optimal
FASE 9: AUTHENTICATION & USER MANAGEMENT
Tujuan: Implementasi user authentication dan authorization
Tahapan:
Setup JWT Authentication:
User registration endpoint
Login endpoint
Token refresh mechanism
Implementasi Role-Based Access Control:
Admin role (full access)
User role (scan only)
Guest role (limited scans)
Password hashing dengan bcrypt
Session management
API key generation untuk programmatic access
Rate limiting per user
Kriteria Selesai:
User bisa register dan login
JWT token valid untuk protected endpoints
Role-based access control berfungsi
Password tersimpan dengan aman (hashed)
FASE 10: TESTING & DOCUMENTATION 📝
Tujuan: Memastikan kualitas kode dan dokumentasi lengkap
Tahapan:
Unit Testing:
Test untuk semua service functions
Test untuk feature extraction
Test untuk model prediction
Test untuk database operations
Integration Testing:
Test end-to-end flow
Test API endpoints
Test database transactions
Load Testing:
Test dengan concurrent requests
Test response time under load
Identify bottlenecks
Documentation:
API documentation (Swagger sudah auto-generated)
Code comments dan docstrings
Architecture diagrams
Deployment guide
Security Audit:
SQL injection prevention
XSS prevention
Input validation
File upload security
Kriteria Selesai:
Test coverage > 80%
All tests passing
Documentation lengkap
Security vulnerabilities addressed
FASE 11: DEPLOYMENT & MONITORING 🚀
Tujuan: Deploy backend ke production environment
Tahapan:
Setup Docker containerization:
Dockerfile untuk backend
Docker Compose untuk full stack (backend + database + redis + celery)
Setup CI/CD Pipeline:
GitHub Actions untuk automated testing
Automated deployment
Setup Production Environment:
PostgreSQL production database
Redis production instance
Environment variables management
Setup Monitoring:
Application performance monitoring (APM)
Error tracking (Sentry)
Logging aggregation
Setup Backup Strategy:
Database backup automation
Model versioning dengan MLflow
Performance optimization:
Database indexing
Query optimization
Caching strategy
Kriteria Selesai:
Backend deployed dan accessible
Monitoring aktif
Backup automation berjalan
Performance optimal
🎯 PRIORITAS SAAT INI
URGENT (Hari Ini):
Fix error Could not import module "app.main"
Verifikasi backend bisa start
Test endpoint via Swagger UI
SHORT TERM (Minggu Ini):
Fase 2: Feature Engineering URL
Collect dataset untuk training
MEDIUM TERM (2 Minggu):
Fase 3: Dataset Collection & Preprocessing
Fase 4: Training ML Model
LONG TERM (1 Bulan):
Fase 5-7: Integrasi ML untuk semua vector (URL, Email, File)
Fase 8-9: Background tasks & Authentication
📝 CATATAN PENTING
Masalah yang Perlu Diperhatikan:
Struktur Import Python:
File main.py berada di backend/ (root), bukan di backend/app/
Perlu konsistensi dalam cara menjalankan uvicorn
Rekomendasi: Gunakan uvicorn main:app (tanpa app.)
Database Schema:
Tabel sudah dibuat dengan struktur yang benar
Kolom features_json dan shap_values sudah ada sebagai JSONB
ID menggunakan UUID (bukan Integer)
Frontend Integration:
Frontend menggunakan prefix /api/v1/ untuk semua requests
Backend sudah dikonfigurasi dengan prefix yang sama
CORS sudah configured untuk http://localhost:3000
ML Model Path:
Model akan disimpan di C:\Projects\ThreatSense\ml\models
Perlu membuat folder ini jika belum ada
Model files: .pkl atau .joblib format
Performance Considerations:
WHOIS lookup bisa lambat (1-3 detik)
Perlu caching untuk domain yang sudah di-scan
File scan bisa lama untuk file besar → perlu async
RESOURCE & REFERENCES
Dataset yang Direkomendasikan:
PhishTank: https://www.phishtank.com/
OpenPhish: https://openphish.com/
Alexa 1M: http://s3.amazonaws.com/alexa-static/top-1m.csv.zip
Tranco List: https://tranco-list.eu/
Enron Email Dataset: https://www.cs.cmu.edu/~enron/
VirusShare: https://virusshare.com/
MalwareBazaar: https://bazaar.abuse.ch/
Library Documentation:
FastAPI: https://fastapi.tiangolo.com/
SQLAlchemy: https://www.sqlalchemy.org/
Pydantic: https://docs.pydantic.dev/
XGBoost: https://xgboost.readthedocs.io/
LightGBM: https://lightgbm.readthedocs.io/
SHAP: https://shap.readthedocs.io/
MLflow: https://mlflow.org/
Celery: https://docs.celeryq.dev/
Tools:
pgAdmin: Untuk manage PostgreSQL
Redis Desktop Manager: Untuk monitor Redis
Postman/Insomnia: Untuk test API
Docker Desktop: Untuk containerization