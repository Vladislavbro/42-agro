from sqlalchemy import (
    Column, Integer, String, Date, Float, ForeignKey, func
)
from sqlalchemy.orm import relationship
from app.core.base import Base

class Message(Base):
    __tablename__ = "messages"

    id         = Column(Integer, primary_key=True, index=True)
    text       = Column(String, nullable=False)
    created_at = Column(Date, server_default=func.current_date())

    reports    = relationship("ReportModel", back_populates="message")


class ReportModel(Base):
    __tablename__ = "reports"

    id          = Column(Integer, primary_key=True, index=True)
    message_id  = Column(Integer, ForeignKey("messages.id"), nullable=False)
    date        = Column(Date, nullable=False)
    department  = Column(String, nullable=True)
    operation   = Column(String, nullable=True)
    crop        = Column(String, nullable=True)
    area_day    = Column(Float, nullable=True)
    area_total  = Column(Float, nullable=True)
    yield_day   = Column(Float, nullable=True)
    yield_total = Column(Float, nullable=True)

    message     = relationship("Message", back_populates="reports")
