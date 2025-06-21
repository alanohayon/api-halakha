from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from .base import Base

class Halakha(Base):
    __tablename__ = "halakhot"
    
    id = Column(Integer, primary_key=True, index=True)
    question = Column(String(500), nullable=False, index=True)
    content = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    text_post = Column(Text, nullable=True)
    legend = Column(Text, nullable=True)
    prompt_dalle = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    notion_page_id = Column(String(100), nullable=True)
    status = Column(String(50), default="pending", index=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())