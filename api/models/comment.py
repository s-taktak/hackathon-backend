from sqlalchemy import Column, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from api.db import Base

class Comment(Base):
    __tablename__ = "comments"

    id = Column(String(36), primary_key=True)
    content = Column(Text, nullable=False)
    
    user_id = Column(String(36), ForeignKey("user.id"), nullable=False)
    item_id = Column(String(36), ForeignKey("items.id"), nullable=False)
    created_at = Column(DateTime, nullable=False)

    user = relationship("User")
    item = relationship("Item", back_populates="comments")