from database import Base
from sqlalchemy import Column, Integer, String, Boolean, text, ARRAY, TIMESTAMP, Float
from pydantic import BaseModel
from typing import List, Optional

class User(Base):
    __tablename__ = "Users"

    id = Column(Integer,primary_key=True,nullable=False)
    email = Column(String,nullable=False,unique=True)
    password = Column(String,nullable=False)
    protein = Column(Float,nullable=False)
    fat = Column(Float,nullable=False)
    carbs = Column(Float,nullable=False)
    cals = Column(Integer,nullable=False)
    plans = Column(ARRAY(String))
    favorites = Column(ARRAY(String),nullable=True)

class RequestResponse(BaseModel):
    success: bool
    message: Optional[str] = ""

class UserCreate(BaseModel):

    email: str
    password: str
    protein: float
    fat: float
    carbs: float
    cals: int
    plans: Optional[List[str]] = []
    favorites: Optional[List[str]] = []

class UserValuesUpdate(BaseModel):

    protein: Optional[float] = None
    fat: Optional[float] = None
    carbs: Optional[float] = None
    cals: Optional[int] = None

class LoginRequest(BaseModel):

    email: str
    password: str