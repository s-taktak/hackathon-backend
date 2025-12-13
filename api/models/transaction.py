from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from api.db import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True)
    
    item_id = Column(String(36), ForeignKey("items.id"), nullable=False)
    buyer_id = Column(String(36), ForeignKey("user.id"), nullable=False)
    seller_id = Column(String(36), ForeignKey("user.id"), nullable=False)
    
    transaction_price = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now())

    item = relationship("Item")
    buyer = relationship("User", foreign_keys=[buyer_id])
    seller = relationship("User", foreign_keys=[seller_id])