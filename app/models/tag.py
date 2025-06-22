from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.core.database import Base

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    # Relation many-to-many avec Halakha
    halakhot = relationship("Halakha", secondary="halakha_tags", back_populates="tags")
    
# from sqlalchemy.orm import sessionmaker
# from models.halakha import Halakha
# from models.tag import Tag

# # Supposons que tu as déjà configuré une session SQLAlchemy
# Session = sessionmaker(bind=engine)
# session = Session()

# # Rechercher des Halakhot par un mot-clé spécifique
# tag_name = "kashrut"
# halakhot = session.query(Halakha).join(Halakha.tags).filter(Tag.name == tag_name).all()

# for halakha in halakhot:
#     print(halakha.title)