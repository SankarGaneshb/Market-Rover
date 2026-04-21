from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..config.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    google_id = Column(String(255), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    name = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Promoter(Base):
    __tablename__ = "promoters"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), unique=True, index=True)
    company_name = Column(String(255))
    governance_score = Column(Float, default=5.0)
    total_shares = Column(Float)  # Represented in millions or actual

    # Enriched Metrics (Persisted from Scans)
    holding_pct = Column(Float, default=0.0)
    pledged_pct = Column(Float, default=0.0)
    skin_in_the_game = Column(Float, default=0.0)
    skin_layer1 = Column(Float, default=0.0)
    skin_layer2 = Column(Float, default=0.0)
    survival_score = Column(Float, default=0.0)
    intent_label = Column(String(50), default="Neutral")
    trust_signal = Column(String(50), default="Stable")
    release_create_ratio = Column(Float, default=1.0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    pledges = relationship("PledgeEvent", back_populates="promoter")

class PledgeEvent(Base):
    __tablename__ = "pledge_events"
    id = Column(Integer, primary_key=True, index=True)
    promoter_id = Column(Integer, ForeignKey("promoters.id"))
    pledgee_name = Column(String(255))      # NBFC or Bank name
    percentage_pledged = Column(Float)
    purpose = Column(Text)                  # "Personal", "Business Growth" etc.
    ltv_ratio = Column(Float, nullable=True) # Loan to Value
    trigger_price = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    promoter = relationship("Promoter", back_populates="pledges")

class AnalysisRun(Base):
    __tablename__ = "analysis_runs"
    id = Column(Integer, primary_key=True, index=True)
    promoter_id = Column(Integer, ForeignKey("promoters.id"))
    trigger_source = Column(String(255))    # SAST, LODR, manual
    debate_log = Column(JSON)               # The Skeptic vs Actuary conversation
    final_sentiment = Column(String(50))    # Growth, Survival, Neutral
    governance_score_calc = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class GlobalScanStatus(Base):
    __tablename__ = "global_scan_status"
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(50), default="idle") # idle, scanning, completed, failed
    last_scan_at = Column(DateTime(timezone=True), onupdate=func.now())
    message = Column(String(255), default="")
