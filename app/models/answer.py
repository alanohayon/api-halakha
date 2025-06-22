from sqlalchemy import Column, Integer, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    answer = Column(Text, nullable=False)

    # Relation
    halakha = relationship("Halakha", back_populates="answer", uselist=False)
