from database import Base
from sqlalchemy import Column, Integer, String, Boolean, text, ARRAY, TIMESTAMP, Float
from pydantic import BaseModel
from typing import List, Optional

class User(Base):
    __tablename__ = "Users"

    id = Column(Integer,primary_key=True,nullable=False)
    email = Column(String,nullable=False,unique=True)
    protein = Column(Float,nullable=False)
    fat = Column(Float,nullable=False)
    carbs = Column(Float,nullable=False)
    favorites = Column(ARRAY(String),nullable=True)

class UserCreate(BaseModel):

    email: str
    protein: float
    fat: float
    carbs: float
    favorites: Optional[List[str]] = []