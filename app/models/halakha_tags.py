from sqlalchemy import Column, Integer, ForeignKey
from .base import Base

class HalakhaTag(Base):
    __tablename__ = "halakha_tags"

    halakha_id = Column(Integer, ForeignKey('halakhot.id'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tags.id'), primary_key=True)
