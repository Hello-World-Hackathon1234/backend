from database import Base
from sqlalchemy import Column, Integer, String, Boolean, text, ARRAY, TIMESTAMP, Float
from pydantic import BaseModel
from typing import List, Optional

class User(Base):
    __tablename__ = "Users"

    id = Column(Integer,primary_key=True,nullable=False)
    protein = Column(Float,nullable=True)
    fat = Column(Float,nullable=True)
    carbs = Column(Float,nullable=True)
    cals = Column(Integer,nullable=True)
    plans = Column(ARRAY(String),nullable=True)
    favorites = Column(ARRAY(String),nullable=True)

class Menu(Base):
    __tablename__ = "menus"

    id = Column(Integer,primary_key=True)
    location = Column(String,nullable=False)
    date = Column(String,nullable=True)
    item_id = Column(String,nullable=False)
    start_time = Column(TIMESTAMP,nullable=True)
    end_time = Column(TIMESTAMP,nullable=True)

class Food(Base):
    __tablename__ = "foods"

    id = Column(String,primary_key=True,nullable=False)
    name = Column(String,nullable=True)
    ingredients = Column(String,nullable=True)
    nutrition = Column(String,nullable=True)
    station = Column(String,nullable=True)
    traits = Column(ARRAY(String),nullable=True)
    food_group = Column(ARRAY(String),nullable=True)
    food_type = Column(ARRAY(String),nullable=True)

class GetMealRequest(BaseModel):

    fat: float
    carbs: float
    protein: float
    cals: int

class RequestResponse(BaseModel):

    success: bool
    message: Optional[str] = ""

class UserValuesUpdate(BaseModel):

    protein: Optional[float] = None
    fat: Optional[float] = None
    carbs: Optional[float] = None
    cals: Optional[int] = None

class UserPrefsUpdate(BaseModel):

    prefs: List[str]

class LoginRequest(BaseModel):

    email: str
    password: str

class RecommendRequest(BaseModel):
    day: int
    hall: str
    meal_type: str
