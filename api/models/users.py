from sqlalchemy import Column, Integer, String, ForeignKey,Date,DateTime
from sqlalchemy.orm import relationship

from api.db import Base

class User(Base):
    __tablename__ = "user"

    id = Column(String(36),primary_key=True)
    username = Column(String(50),nullable=False)
    email= Column(String(50),nullable=False,unique=True)
    hashed_password = Column(String(255),nullable=False)
    gender = Column(String(20), default="undefined")
    birth_date = Column(Date, nullable=True)
    created_at = Column(DateTime,nullable=False)
    
    items = relationship("Item", back_populates="seller")