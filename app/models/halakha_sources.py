# app/models/halakha_sources.py
from sqlalchemy import Column, Integer, ForeignKey
from app.core.database import Base

class HalakhaSource(Base):
    __tablename__ = "halakha_sources"
    halakha_id = Column(Integer, ForeignKey('halakhot.id'), primary_key=True)
    source_id = Column(Integer, ForeignKey('sources.id'), primary_key=True)