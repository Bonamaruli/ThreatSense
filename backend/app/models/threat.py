from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base


class ScanHistory(Base):
    """
    Model untuk menyimpan history scan
    """
    __tablename__ = "scan_history"

    id = Column(Integer, primary_key=True, index=True)
    scan_type = Column(String(50), nullable=False)  # 'url', 'email', 'file'
    input_value = Column(Text, nullable=False)  # URL, email content, atau filename
    risk_score = Column(Float, nullable=False)  # 0.0 - 100.0
    threat_label = Column(String(50), nullable=False)  # 'safe', 'suspicious', 'dangerous'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<ScanHistory(id={self.id}, type={self.scan_type}, score={self.risk_score})>"