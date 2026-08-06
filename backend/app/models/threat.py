"""
threat.py
=========
Definisi SELURUH tabel database ThreatSense (SQLAlchemy ORM).

SUMBER KEBENARAN TUNGGAL
------------------------
File INI adalah satu-satunya acuan bentuk tabel. File m.sql di root project
sudah dipensiunkan (isinya dinonaktifkan) karena isinya sempat berbeda
dengan file ini — misalnya domain_reputation.id di sana bertipe SERIAL
(angka urut) sedangkan di sini UUID. Perbedaan seperti itu tidak ketahuan
saat aplikasi jalan, karena Base.metadata.create_all() hanya MEMBUAT tabel
yang belum ada — dia tidak pernah mengubah tabel yang sudah terlanjur ada.
Akibatnya error baru muncul belakangan, saat tabelnya mulai dipakai.

Kalau nanti perlu mengubah struktur tabel, JANGAN edit SQL manual. Pakai
Alembic (sudah ada di requirements.txt):
    alembic revision --autogenerate -m "keterangan perubahan"
    alembic upgrade head
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, text
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid


class ScanHistory(Base):
    """Riwayat setiap pemindaian yang pernah dilakukan."""

    __tablename__ = "scan_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Pemilik riwayat ini.
    #
    # nullable=True DISENGAJA: saat fitur akun ditambahkan, sudah ada 38 baris
    # riwayat lama yang tidak punya pemilik. Kalau kolom ini diwajibkan,
    # penambahannya akan gagal dan data lama harus dibuang. Baris tanpa
    # pemilik itu tetap tersimpan tapi tidak muncul di riwayat siapa pun.
    #
    # ondelete CASCADE: menghapus akun ikut menghapus riwayatnya.
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True, index=True,
    )

    scan_type = Column(String(50), nullable=False, index=True)  # 'url' | 'email' | 'file'
    input_value = Column(Text, nullable=False)  # URL, cuplikan email, atau nama file
    risk_score = Column(Float, nullable=False)  # 0.0 - 1.0
    threat_label = Column(String(50), nullable=False, index=True)  # 'Safe' | 'Suspicious' | 'Malicious'
    features_json = Column(JSONB, nullable=True)  # fitur hasil ekstraksi
    shap_values = Column(JSONB, nullable=True)  # kontribusi tiap fitur (explainability)
    # Alasan berbahasa manusia, contoh: "Menyebut 'bri' padahal bukan domain
    # resminya". Disimpan terpisah dari shap_values karena ini kalimat untuk
    # dibaca pengguna, bukan angka kontribusi fitur.
    explanations = Column(JSONB, nullable=True)
    # Bukti hasil pemeriksaan mendalam (umur domain, negara server, dan
    # seterusnya). Kosong untuk pemindaian cepat yang hanya membaca nama.
    evidence_summary = Column(JSONB, nullable=True)
    # server_default dinyatakan di sini, bukan hanya default=False.
    #
    # default=False saja hanya berlaku saat baris dibuat lewat ORM. Kalau ada
    # yang menyisipkan baris lewat SQL langsung (skrip pemindahan data,
    # perbaikan manual), kolom NOT NULL tanpa nilai bawaan akan menolak.
    # Menyatakannya di sini juga membuat model dan database sepakat, sehingga
    # Alembic tidak terus-menerus melaporkan perbedaan yang sebenarnya
    # disengaja.
    deep_scan = Column(Boolean, default=False, server_default=text("false"),
                       nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User", back_populates="scans")

    def __repr__(self):
        return f"<ScanHistory(id={self.id}, type={self.scan_type}, score={self.risk_score})>"


class DomainReputation(Base):
    """
    Reputasi domain yang terkumpul dari waktu ke waktu.

    Dipakai supaya domain yang sudah pernah diperiksa tidak perlu dianalisis
    ulang dari nol setiap kali muncul.
    """

    __tablename__ = "domain_reputation"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    domain = Column(String(255), unique=True, nullable=False, index=True)
    risk_score = Column(Float, nullable=False)
    threat_type = Column(String(100), nullable=True)  # 'phishing' | 'judi' | 'malware' | ...
    first_seen = Column(DateTime(timezone=True), server_default=func.now())
    last_scanned = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    scan_count = Column(Integer, default=1)
    confirmed_bad = Column(Boolean, default=False)
    source = Column(String(100), nullable=True)  # 'ml_detected' | 'kominfo' | 'phishtank' | ...

    def __repr__(self):
        return f"<DomainReputation(domain={self.domain}, score={self.risk_score})>"


class DomainFeaturesCache(Base):
    """
    Simpanan sementara fitur jaringan sebuah domain (WHOIS, DNS, SSL).

    KENAPA PERLU: pencarian WHOIS makan waktu 1-3 detik dan ada batas
    kuota permintaan. Tanpa simpanan ini, memindai URL dari domain yang
    sama berulang kali akan lambat dan berisiko diblokir penyedia WHOIS.

    Kolom expires_at menandai kapan data dianggap basi dan perlu diambil
    ulang (umumnya 7-30 hari, karena umur domain jarang berubah).
    """

    __tablename__ = "domain_features_cache"

    domain = Column(String(255), primary_key=True)
    features_json = Column(JSONB, nullable=True)
    cached_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)

    def __repr__(self):
        return f"<DomainFeaturesCache(domain={self.domain}, expires={self.expires_at})>"


class FileSignature(Base):
    """Daftar sidik jari (hash SHA-256) file yang sudah dipastikan berbahaya."""

    __tablename__ = "file_signatures"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sha256_hash = Column(String(64), unique=True, nullable=False, index=True)
    file_type = Column(String(50), nullable=False)
    threat_name = Column(String(255), nullable=True)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    source = Column(String(100), nullable=True)  # 'malwarebazaar' | 'virusshare' | ...

    def __repr__(self):
        return f"<FileSignature(hash={self.sha256_hash[:12]}..., type={self.file_type})>"


class ScanFeedback(Base):
    """
    Koreksi dari pengguna saat model salah menebak.

    KENAPA PENTING UNTUK TA: ini bahan bakar continuous learning. Setiap kali
    pengguna menandai "ini sebenarnya aman" atau "ini sebenarnya berbahaya",
    baris di sini bertambah. Kumpulan koreksi itu jadi data latih tambahan
    untuk versi model berikutnya — sekaligus bukti nyata di laporan bahwa
    sistemmu bisa memperbaiki diri, bukan sekadar model sekali latih.
    """

    __tablename__ = "scan_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id = Column(UUID(as_uuid=True), ForeignKey("scan_history.id"), nullable=False, index=True)
    ml_prediction = Column(Float, nullable=True)  # skor yang tadinya diberikan model
    user_correction = Column(String(20), nullable=True)  # 'safe' | 'malicious' | 'suspicious'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<ScanFeedback(scan_id={self.scan_id}, koreksi={self.user_correction})>"


class ModelVersion(Base):
    """
    Catatan setiap versi model yang pernah dilatih.

    Berguna untuk membandingkan performa antar percobaan pelatihan, dan untuk
    menandai model mana yang sedang aktif dipakai (is_active). Di laporan TA,
    tabel ini jadi bukti bahwa proses pelatihanmu terdokumentasi.
    """

    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_type = Column(String(50), nullable=False)  # 'url' | 'email' | 'file'
    version = Column(String(20), nullable=False)
    accuracy = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    trained_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=False, index=True)

    def __repr__(self):
        return f"<ModelVersion({self.model_type} v{self.version}, aktif={self.is_active})>"
