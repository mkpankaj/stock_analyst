from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import enum

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    configs = relationship("Config", back_populates="user")

class Config(Base):
    __tablename__ = "config"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    stock_universe = Column(String, default="NIFTY_50")  # NIFTY_50 or NIFTY_100
    duration_days = Column(Integer, default=120)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="configs")

class StockPrice(Base):
    __tablename__ = "stock_prices"

    id = Column(Integer, primary_key=True)
    ticker = Column(String, index=True)
    date = Column(Date, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)

    def __repr__(self):
        return f"<StockPrice({self.ticker}, {self.date}, {self.close})>"

class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id = Column(Integer, primary_key=True)
    date = Column(Date, unique=True, index=True)  # One analysis per date
    config_snapshot_json = Column(Text)  # Store config params as JSON
    status = Column(String, default="pending")  # pending, running, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)

    results = relationship("AnalysisResult", back_populates="analysis_run")

class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True)
    analysis_run_id = Column(Integer, ForeignKey("analysis_runs.id"))
    ticker = Column(String, index=True)
    rank_type = Column(String)  # "gainer" or "loser"
    rank = Column(Integer)  # 1-10
    price_change_pct = Column(Float)
    trend_label = Column(String)  # Strong Upward, Weak Uptrend, etc.
    price_d1 = Column(Float)
    price_d120 = Column(Float)

    analysis_run = relationship("AnalysisRun", back_populates="results")

class NewsHeadline(Base):
    __tablename__ = "news_headlines"

    id = Column(Integer, primary_key=True)
    ticker = Column(String, index=True)
    headline = Column(String)
    url = Column(String)
    published_at = Column(DateTime)
    source = Column(String)  # Business Standard, Mint, ET

