from database import Base
from sqlalchemy import Column, Integer, String, Boolean, text
from pydantic import BaseModel

class User(Base):
    __tablename__ = "Users"

    id = Column(Integer,primary_key=True,nullable=False)
    name = Column(String,nullable=False)

# Implement this later for users

class Club(Base):
    __tablename__ = "public.Clubs"

    id = Column(Integer,primary_key=True,nullable=False)
    name = Column(String,nullable=False)
    description = Column(String,nullable=False)
    tags = Column(String,nullable=True)
    imageUrl = Column(String,nullable=True)

class ClubModel(BaseModel):

    id: int
    name: str
    description: str
    tags: str
    imageUrl: str
    
    class Config:
        orm_model = True

