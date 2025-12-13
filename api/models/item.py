from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship

from api.db import Base

class Item(Base):
    __tablename__ = "items"

    id = Column(String(36), primary_key=True)

    seller_id = Column(String(36), ForeignKey("user.id"), nullable=False)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True) # 長文はText型推奨
    price = Column(Integer, nullable=False)
    
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=True)
    condition_id = Column(Integer, ForeignKey("item_conditions.id"), nullable=False)
    
    status = Column(String(20), default="on_sale")
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    # リレーション: これを書くと、item.seller.username のようにアクセスできます
    seller = relationship("User", back_populates="items")
    category = relationship("Category", back_populates="items")
    brand = relationship("Brand", back_populates="items")
    condition = relationship("ItemCondition", back_populates="items")
    comments = relationship("Comment", back_populates="item", cascade="all, delete")
    images = relationship("ItemImage", back_populates="item", cascade="all, delete")
    vector = relationship("ItemVector", back_populates="item", uselist=False, cascade="all, delete-orphan")