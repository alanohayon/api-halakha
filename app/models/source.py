
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .base import Base

class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    # Relation one-to-many avec Halakha
    halakhot = relationship("Halakha", back_populates="source")