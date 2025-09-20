from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from starlette import status
from typing import List
import schema
from database import get_db

app = FastAPI()

@app.get("/")
async def root():
    return {"greeting": "Hello, World!", "message": "Welcome to FastAPI!"}

@app.get("/clubs", response_model=List[schema.ClubModel])
async def get_club_list(db: Session = Depends(get_db)):
    clubs = db.query(schema.Club).all()

    return clubs

