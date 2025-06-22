from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Halakha(Base):
    __tablename__ = "halakhot"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text, nullable=False)
    theme = Column(String, index=True)
    tags = Column(String, index=True)

    # Clé étrangère pour la source
    source_id = Column(Integer, ForeignKey('sources.id'), nullable=False)
    question_id = Column(Integer, ForeignKey('questions.id', ondelete="CASCADE"), nullable=False)
    answer_id = Column(Integer, ForeignKey('answers.id', ondelete="CASCADE"), nullable=False)
    
    # Relations
    source = relationship("Source", back_populates="halakhot")
    question = relationship("Question", back_populates="halakha")
    answer = relationship("Answer", back_populates="halakha")
    tags = relationship("Tag", secondary="halakha_tags", back_populates="halakhot")