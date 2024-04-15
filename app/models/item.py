from . import Base
from sqlalchemy import Column, Integer, String, Boolean, Float

class Item(Base):
    
    __tablename__="item"
    
    id = Column(Integer,primary_key=True)
    name = Column(String(80), nullable=False, unique=True, index=True)
    description = Column(String(240), nullable=False)
    quantity = Column(Integer, nullable=False)
    owner_id = Column(Integer, nullable=False, index=True)
    ver = Column(Integer, nullable=False, default=1)
    
    __mapper_args__ = {
        "version_id_col" : ver
    }