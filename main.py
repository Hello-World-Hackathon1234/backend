from fastapi import FastAPI, HTTPException, Depends, Response, Request, Cookie, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from starlette import status
from typing import List, Annotated
import schema
from database import get_db
from auth_handler import sign_jwt, decode_jwt
from optimize import find_optimal_foods_greedy, create_food_item, find_optimal_foods_balanced
import os
from fastapi.responses import StreamingResponse
from advisor_ai import *
import datetime
from PIL import Image
import io
import json
from fastapi import UploadFile, HTTPException, File
import pytz

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/generate-meal-plan-stream")
async def generate_meal_plan_stream(request: MealPlanRequest = Body(...)):
    if not os.getenv("GOOGLE_API_KEY"):
        raise HTTPException(
            status_code=500, detail="GOOGLE_API_KEY environment variable not set."
        )
    
    return StreamingResponse(
        stream_generator(request.user_goal, request.food_info, request.chat_history),
        media_type="text/plain",
    )

@app.post("/estimate-nutrition")
async def estimate_nutrition(file: UploadFile = File(...)):
    if not os.getenv("GOOGLE_API_KEY"):
        raise HTTPException(
            status_code=500, detail="GOOGLE_API_KEY environment variable not set."
        )
    
    image_bytes = await file.read()
    
    return StreamingResponse(
        image_stream_generator(image_bytes),
        media_type="text/plain",
    )
    
@app.get("/register")
async def new_user(response: Response, db: Session = Depends(get_db)):
    try:
        
        # Create new user
        db_user = schema.User(**{})
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        token = sign_jwt(db_user.id, os.environ["JWT_SECRET"])

        response.set_cookie(key="token", value=token, httponly=True)
        
        return {"success": "YAYYYYY"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )

@app.post("/update_user_macs", response_model=schema.RequestResponse)
async def update_user(request: Request, update: schema.UserValuesUpdate, db: Session = Depends(get_db)):
    decoded = decode_jwt(request.cookies.get('token'), os.environ["JWT_SECRET"])
    try:
        # Use the actual User model, not schema
        user = db.query(schema.User).filter(schema.User.id == decoded['user_id']).first()
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user information: {str(e)}"
        )

@app.post("/login", response_model=schema.RequestResponse)
async def login(data: schema.LoginRequest, response: Response, db: Session = Depends(get_db)):
    try:
        user = db.query(schema.User).filter(schema.User.email == data.email).filter(schema.User.password == data.password).first()

        if not user:
            return schema.RequestResponse({success: False, message: "Either username or password is incorrect"})

        token = sign_jwt(data.email, os.environ["JWT_SECRET"])
        response.set_cookie(key="token", value=token, httponly=True, secure=True)
        return schema.RequestResponse({success: True})
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Hmmmm"
        )

#
# UNFINISHED
#
@app.get("/recommend")
async def get_recs_hilly(day: int, hall: str, meal_type: str, request: Request, db: Session = Depends(get_db)):
    decoded = decode_jwt(request.cookies.get('token'), os.environ["JWT_SECRET"])
    try:
        user = db.query(schema.User).filter(schema.User.id == decoded['user_id']).first()

        # Define meal times
        meal_times = {
            "breakfast": 8.5,  # 8:30 AM
            "lunch": 12.0,     # 12:00 PM  
            "dinner": 18.0     # 6:00 PM
        }
        
        if meal_type not in meal_times:
            raise HTTPException(status_code=400, detail="Invalid meal type. Use: breakfast, lunch, dinner")
        
        # Get the target date and set specific meal time
        target_date = datetime.datetime.now().date() + datetime.timedelta(days=day)
        meal_hour = meal_times[meal_type]
        
        # Create datetime for the specific meal time
        target_time = datetime.datetime.combine(
            target_date, 
            datetime.time(hour=int(meal_hour), minute=int((meal_hour % 1) * 60))
        )
        
        base = db.query(schema.Food).join(
            schema.Menu,
            schema.Food.id == schema.Menu.item_id
        ).filter(
            schema.Food.nutrition != "{}",
            schema.Menu.start_time <= target_time,  # Menu starts before or at meal time
            schema.Menu.end_time >= target_time     # Menu ends after or at meal time
        )
        
        items = base.filter(schema.Menu.location == hall).all()
        items_list = []
        for entry in items:
            if "Sauce" in entry.name:
                continue
            items_list.append(create_food_item(entry.name, entry.nutrition))
        
        result_list = find_optimal_foods_balanced(user.protein, user.carbs, user.fat, user.cals, items_list)
        return result_list
        
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/rectest")
async def test(day: int, hall: str, meal_type: str, data: schema.GetMealRequest, db: Session = Depends(get_db)):
    # Define meal times
    meal_times = {
        "breakfast": 8.5,  # 8:30 AM
        "lunch": 12.0,     # 12:00 PM  
        "dinner": 18.0     # 6:00 PM
    }
    
    if meal_type not in meal_times:
        raise HTTPException(status_code=400, detail="Invalid meal type. Use: breakfast, lunch, dinner")
    
    # Get the target date and set specific meal time
    target_date = datetime.datetime.now().date() + datetime.timedelta(days=day)
    meal_hour = meal_times[meal_type]
    
    # Create datetime for the specific meal time
    target_time = datetime.datetime.combine(
        target_date, 
        datetime.time(hour=int(meal_hour), minute=int((meal_hour % 1) * 60))
    )
    
    base = db.query(schema.Food).join(
        schema.Menu,
        schema.Food.id == schema.Menu.item_id
    ).filter(
        schema.Food.nutrition != "{}",
        schema.Menu.start_time <= target_time,  # Menu starts before or at meal time
        schema.Menu.end_time >= target_time     # Menu ends after or at meal time
    )
    
    items = base.filter(schema.Menu.location == hall).all()
    items_list = []
    for entry in items:
        if "Sauce" in entry.name:
            continue
        items_list.append(create_food_item(entry.name, entry.nutrition))
    
    result_list = find_optimal_foods_balanced(data.protein, data.carbs, data.fat, data.cals, items_list)
    return result_list
