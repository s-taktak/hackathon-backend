from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from api.db import Base

class ItemVector(Base):
    __tablename__ = "item_vectors"

    # IDはItemと同じにするか、独自ID＋ForeignKeyにする
    # ここでは item_id を主キーにして 1:1 を強制します
    item_id = Column(String(36), ForeignKey("items.id"), primary_key=True)
    
    # ここにベクトルを保存 (MySQLのJSON型)
    embedding = Column(JSON, nullable=False)

    item = relationship("Item", back_populates="vector")