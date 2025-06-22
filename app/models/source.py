from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.core.database import Base

class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    page = Column(String, nullable=True)  # page peut être une chaîne (ex: "301-45")
    full_src = Column(String, nullable=False)

    # Relation one-to-many avec Halakha
    halakhot = relationship("Halakha", secondary="halakha_sources", back_populates="sources")