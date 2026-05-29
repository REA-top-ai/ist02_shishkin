from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Journalist(Base):
    __tablename__ = "journalists"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False, unique=True)
    email_address = Column(String(150), nullable=False, unique=True)
    joined_at = Column(DateTime, default=datetime.utcnow)

    publications = relationship("Publication", back_populates="journalist", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Journalist(username='{self.username}', email_address='{self.email_address}')>"


class Publication(Base):
    __tablename__ = "publications"

    id = Column(Integer, primary_key=True, index=True)
    caption = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    journalist_id = Column(Integer, ForeignKey("journalists.id"), nullable=False)

    journalist = relationship("Journalist", back_populates="publications")
    feedbacks = relationship("Feedback", back_populates="publication", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Publication(caption='{self.caption}', is_published={self.is_published})>"


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(Text, nullable=False)
    sender_name = Column(String(100), nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    publication_id = Column(Integer, ForeignKey("publications.id"), nullable=False)

    publication = relationship("Publication", back_populates="feedbacks")

    def __repr__(self):
        return f"<Feedback(publication_id={self.publication_id}, sender_name='{self.sender_name}')>"


if __name__ == "__main__":
    from database import engine, Base
    Base.metadata.create_all(bind=engine)
    print("✓ Таблицы созданы!")
