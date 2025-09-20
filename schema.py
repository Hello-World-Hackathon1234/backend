from database import Base
from sqlalchemy import Column, Integer, String, Boolean, text
from pydantic import BaseModel
from typing import List

class User(Base):
    __tablename__ = "Users"

    id = Column(Integer,primary_key=True,nullable=False)
    name = Column(String,nullable=False)

# Implement this later for users

class Club(Base):
    __tablename__ = "Clubs"

    id = Column(Integer,primary_key=True,nullable=False)
    name = Column(String,nullable=False)
    description = Column(String,nullable=False)
    tags = Column(List[String],nullable=True)
    imageUrl = Column(String,nullable=True)

class ClubModel(BaseModel):

    id: int
    name: str
    description: str
    tags: List[str]
    imageUrl: str
    
    class Config:
        orm_model = True

