from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from api.db import Base

class History(Base):
    __tablename__ = "histories"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("user.id"), nullable=False)
    item_id = Column(String(36), ForeignKey("items.id"), nullable=False)
    
    viewed_at = Column(DateTime, nullable=False)

    item = relationship("Item")