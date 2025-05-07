from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Trade(Base):
    __tablename__ = 'trades'

    id = Column(Integer, primary_key=True, autoincrement=True)
    decision = Column(String, nullable=False)
    outcome = Column(Boolean, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
