from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.config.database import Base

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
