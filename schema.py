from database import Base
from sqlalchemy import Column, Integer, String, Boolean, text

class User(Base):
    __tablename__ = "Users"

    id = Column(Integer,primary_key=True,nullable=False)
    name = Column(String,nullable=False)

class Club(Base):
    __tablename__ = "Clubs"

    id = Column(Integer,primary_key=True,nullable=False)
    name = Column(String,nullable=False)
    description = Column(String,nullable=False)
    tags = Column(String,nullable=True)
    imageUrl = Column(String,nullable=True)

