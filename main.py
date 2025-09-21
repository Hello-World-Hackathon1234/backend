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
        stream_generator(request.user_goal, request.food_info),
        media_type="text/plain",
    )

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
async def update_user(request: Request, update: schema.UserValuesUpdate, db: Session = Depends(get_db)):
    decoded = decode_jwt(request.cookies.get('token'), os.environ("JWT_TOKEN"))
    try:
        # Use the actual User model, not schema
        user = db.query(schema.User).filter(schema.User.email == decoded['email']).first()
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
async def get_recs(request: Request, db: Session = Depends(get_db)):
    decoded = decode_jwt(request.cookies.get('token'), os.environ["JWT_SECRET"])
    try:
        user = db.query(schema.User).filter(schema.User == decoded['email']).first()
        
        # also, make sure that we calculate a different amoutn depending on meal. we dont want a rec for every meal to fill all daily reqs lol
        item_list = find_optimal_foods_greedy(user.protein, user.carbs, user.fat, user.cals, [])
    except Exception as e:
        pass

@app.post("/rectest")
async def test(data: schema.GetMealRequest, db: Session = Depends(get_db)):
    base = db.query(schema.Food).join(
        schema.Menu,
        schema.Food.id == schema.Menu.item_id
    ).filter(
        schema.Food.nutrition != "{}"
    )

    hilly = base.filter(schema.Menu.location == "Hillenbrand").all()

    food_list = []

    for entry in hilly:
        food_list.append(create_food_item(entry.name, entry.nutrition))

    result_list = find_optimal_foods_balanced(data.protein, data.carbs, data.fat, data.cals, food_list)

    return result_list