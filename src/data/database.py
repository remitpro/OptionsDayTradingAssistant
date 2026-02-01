"""Database connection and model definitions."""

from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, JSON
from sqlalchemy.orm import sessionmaker, declarative_base
from config.settings import get_settings

Base = declarative_base()

class TradeModel(Base):
    """SQLAlchemy model for storing trades."""
    __tablename__ = 'trades'

    id = Column(Integer, primary_key=True)
    symbol = Column(String, index=True)
    strategy = Column(String)
    bias = Column(String)
    status = Column(String, default='OPEN')
    timestamp = Column(DateTime, default=datetime.now)
    underlying_price = Column(Float)
    
    # Risk Metrics
    max_loss = Column(Float)
    max_gain = Column(Float)
    risk_reward_ratio = Column(Float)
    probability_of_profit = Column(Float, nullable=True)
    score = Column(Float, nullable=True)
    
    # Store complex structures as JSON
    legs = Column(JSON)
    risk_metrics = Column(JSON)
    explanation = Column(String)

def get_db_engine():
    """Create and return database engine."""
    output_dir = Path("outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    db_path = output_dir / "trades.db"
    
    return create_engine(f"sqlite:///{db_path}")

def init_db():
    """Initialize database tables."""
    engine = get_db_engine()
    Base.metadata.create_all(engine)

def get_session():
    """Get a new database session."""
    engine = get_db_engine()
    Session = sessionmaker(bind=engine)
    return Session()
