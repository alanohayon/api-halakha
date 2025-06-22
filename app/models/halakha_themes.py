from sqlalchemy import Column, Integer, ForeignKey
from app.core.database import Base

class HalakhaTheme(Base):
    __tablename__ = "halakha_themes"

    halakha_id = Column(Integer, ForeignKey('halakhot.id'), primary_key=True)
    theme_id = Column(Integer, ForeignKey('themes.id'), primary_key=True) 