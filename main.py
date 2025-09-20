from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from starlette import status
from typing import List
import schema
from database import get_db

app = FastAPI()

@app.post("/create_user", response_model=schema.RequestResponse)
async def new_user(user_data: schema.UserCreate, db: Session = Depends(get_db)):
    try:
        # Check if email already exists
        existing_user = db.query(schema.User).filter(schema.User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        db_user = schema.User(**user_data.dict())
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return db_user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )

@app.post("/update_user_macs", response_model=schema.RequestResponse)
async def update_user(update: schema.UserValuesUpdate, db: Session = Depends(get_db)):
    
    try:
        # Use the actual User model, not schema
        user = db.query(schema.User).filter(schema.User.email == update.email).first()
        if not user:
            return schema.RequestResponse(success=False, message="User does not exist")
            
        if update.cals is not None:
            user.cals = update.cals
        if update.protein is not None:
            user.protein = update.protein
        if update.carbs is not None:
            user.carbs = update.carbs
        if update.fat is not None:
            user.fat = update.fat
        db.commit()
        db.refresh(user)
        return schema.RequestResponse(success=True, message="Ok")
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user information: {str(e)}"
        )
