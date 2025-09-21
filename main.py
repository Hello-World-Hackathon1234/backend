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
    
@app.post("/register")
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

@app.post("/update_user_prefs", response_model=schema.RequestResponse)
async def update_user_prefs(request:Request, update: schema.UserPrefsUpdate, db: Session = Depends(get_db)):
    decoded = decode_jwt(request.cookies.get('token'), os.environ["JWT_SECRET"])
    try:
        user = db.query(schema.User).filter(schema.User.id == decoded['user_id']).first()

        user.plans = update.prefs

        db.commit()
        db.refresh(user)
        return schema.RequestResponse(success=True, message="Ok")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user information: {str(e)}"
        )

#
# UNFINISHED
#
@app.post("/recommend_mean")
async def get_mean(data: schema.RecommendRequest, request: Request, db: Session = Depends(get_db)):
    decoded = decode_jwt(request.cookies.get('token'), os.environ["JWT_SECRET"])
    try:
        user = db.query(schema.User).filter(schema.User.id == decoded['user_id']).first()
        
        meal_times = {
            "breakfast": 8.5,
            "lunch": 12.0,
            "dinner": 18.0
        }
        
        if data.meal_type not in meal_times:
            raise HTTPException(status_code=400, detail="Invalid meal type")
        
        target_date = datetime.datetime.now().date() + datetime.timedelta(days=data.day)
        meal_hour = meal_times[data.meal_type]
        target_time = datetime.datetime.combine(
            target_date,
            datetime.time(hour=int(meal_hour), minute=int((meal_hour % 1) * 60))
        )
        
        base = db.query(schema.Food).join(
            schema.Menu,
            schema.Food.id == schema.Menu.item_id
        ).filter(
            schema.Food.nutrition != "{}",
            schema.Menu.start_time <= target_time,
            schema.Menu.end_time >= target_time
        )
        
        items = base

        if user.plans is None:
            user.plans = []
            db.commit()
            db.refresh(user)

        if "Vegan" in user.plans:
            items = items.filter(schema.Food.traits.any("Vegan"))
        if "Vegetarian" in user.plans:
            items = items.filter(schema.Food.traits.any("Vegetarian"))
        

        if "Peanuts" in user.plans:
            items = items.filter(~schema.Food.traits.any("Peanuts"))
        if "Dairy" in user.plans:
            items = items.filter(~schema.Food.traits.any("Milk"))
        if "Eggs" in user.plans:
            items = items.filter(~schema.Food.traits.any("Eggs"))
        if "Fish" in user.plans:
            items = items.filter(~schema.Food.traits.any("Fish"))
        if "Shellfish" in user.plans:
            items = items.filter(~schema.Food.traits.any("Shellfish"))
        if "Soy" in user.plans:
            items = items.filter(~schema.Food.traits.any("Soy"))
        if "Gluten" in user.plans:
            items = items.filter(~schema.Food.traits.any("Gluten"))

        earhart = items.filter(schema.Menu.location == "Earhart").all()
        ford = items.filter(schema.Menu.location == "Ford").all()
        hilly = items.filter(schema.Menu.location == "Hillenbrand").all()
        wiley = items.filter(schema.Menu.location == "Wiley").all()
        windsor = items.filter(schema.Menu.location == "Windsor").all()

        e_list = []
        for entry in earhart:
            if "Sauce" in entry.name:
                continue
            e_list.append(create_food_item(entry.name, entry.nutrition))

        f_list = []
        for entry in ford:
            if "Sauce" in entry.name:
                continue
            f_list.append(create_food_item(entry.name, entry.nutrition))

        h_list = []
        for entry in hilly:
            if "Sauce" in entry.name:
                continue
            h_list.append(create_food_item(entry.name, entry.nutrition))
        
        w_list = []
        for entry in wiley:
            if "Sauce" in entry.name:
                continue
            w_list.append(create_food_item(entry.name, entry.nutrition))
        
        wi_list = []
        for entry in windsor:
            if "Sauce" in entry.name:
                continue
            wi_list.append(create_food_item(entry.name, entry.nutrition))
        
        e_result, e_tot = find_optimal_foods_balanced(user.protein / 3, user.carbs / 3, user.fat / 3, user.cals / 3, e_list)
        f_result, f_tot = find_optimal_foods_balanced(user.protein / 3, user.carbs / 3, user.fat / 3, user.cals / 3, f_list)
        h_result, h_tot = find_optimal_foods_balanced(user.protein / 3, user.carbs / 3, user.fat / 3, user.cals / 3, h_list)
        w_result, w_tot = find_optimal_foods_balanced(user.protein / 3, user.carbs / 3, user.fat / 3, user.cals / 3, w_list)
        wi_result, wi_tot = find_optimal_foods_balanced(user.protein / 3, user.carbs / 3, user.fat / 3, user.cals / 3, wi_list)
        
        r = find_best_hall(user.protein / 3, user.carbs / 3, user.fat / 3, user.cals / 3, e_tot, f_tot, h_tot, w_tot, wi_tot)

        sol = None
        name = None
        if r == "e":
            sol = e_result
            name = "Earhart"
        if r == "f":
            sol = f_result
            name = "Ford"
        if r == "h":
            sol = r_result
            name = "Hillenbrand"
        if r == "w":
            sol = w_result
            name = "Wiley"
        if r == "wi":
            sol = wi_result
            name = "Windsor"

        foods_json = []
        for food in sol:
            foods_json.append({
                "name": food.name,
                "protein": food.protein,
                "carbs": food.carbs,
                "fat": food.fat,
                "calories": food.cals
            })
        
        return {"foods": foods_json, "name": name}

    except Exception as e:
        pass

@app.post("/recommend")
async def get_recs_hilly(data: schema.RecommendRequest, request: Request, db: Session = Depends(get_db)):
    decoded = decode_jwt(request.cookies.get('token'), os.environ["JWT_SECRET"])
    try:
        user = db.query(schema.User).filter(schema.User.id == decoded['user_id']).first()
        
        meal_times = {
            "breakfast": 8.5,
            "lunch": 12.0,
            "dinner": 18.0
        }
        
        if data.meal_type not in meal_times:
            raise HTTPException(status_code=400, detail="Invalid meal type")
        
        target_date = datetime.datetime.now().date() + datetime.timedelta(days=data.day)
        meal_hour = meal_times[data.meal_type]
        target_time = datetime.datetime.combine(
            target_date,
            datetime.time(hour=int(meal_hour), minute=int((meal_hour % 1) * 60))
        )
        
        base = db.query(schema.Food).join(
            schema.Menu,
            schema.Food.id == schema.Menu.item_id
        ).filter(
            schema.Food.nutrition != "{}",
            schema.Menu.start_time <= target_time,
            schema.Menu.end_time >= target_time
        )
        
        items = base.filter(schema.Menu.location == data.hall)

        if user.plans is None:
            user.plans = []
            db.commit()
            db.refresh(user)

        if "Vegan" in user.plans:
            items = items.filter(schema.Food.traits.any("Vegan"))
        if "Vegetarian" in user.plans:
            items = items.filter(schema.Food.traits.any("Vegetarian"))
        

        if "Peanuts" in user.plans:
            items = items.filter(~schema.Food.traits.any("Peanuts"))
        if "Dairy" in user.plans:
            items = items.filter(~schema.Food.traits.any("Milk"))
        if "Eggs" in user.plans:
            items = items.filter(~schema.Food.traits.any("Eggs"))
        if "Fish" in user.plans:
            items = items.filter(~schema.Food.traits.any("Fish"))
        if "Shellfish" in user.plans:
            items = items.filter(~schema.Food.traits.any("Shellfish"))
        if "Soy" in user.plans:
            items = items.filter(~schema.Food.traits.any("Soy"))
        if "Gluten" in user.plans:
            items = items.filter(~schema.Food.traits.any("Gluten"))
        
        items = items.all()

        if items is None:
            items = []

        items_list = []
        for entry in items:
            if "Sauce" in entry.name:
                continue
            items_list.append(create_food_item(entry.name, entry.nutrition))
        
        result_list, totals = find_optimal_foods_balanced(user.protein / 3, user.carbs / 3, user.fat / 3, user.cals / 3, items_list)
        
        foods_json = []
        for food in result_list:
            foods_json.append({
                "name": food.name,
                "protein": food.protein,
                "carbs": food.carbs,
                "fat": food.fat,
                "calories": food.cals
            })
        
        return {"foods": foods_json}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

def find_best_hall(target_protein, target_carbs, target_fat, target_cals, 
                   e_tot, f_tot, h_tot, w_tot, wi_tot):
    """
    Find which dining hall total is closest to targets
    
    Returns:
        String name of the best hall ('e', 'f', 'h', 'w', or 'wi')
    """
    halls = {
        'e': e_tot,
        'f': f_tot, 
        'h': h_tot,
        'w': w_tot,
        'wi': wi_tot
    }
    
    best_hall = None
    best_score = float('inf')
    
    for hall_name, totals in halls.items():
        if totals is None:
            continue
            
        # Calculate distance from targets
        protein_diff = abs(target_protein - totals[0])
        carbs_diff = abs(target_carbs - totals[1])
        fat_diff = abs(target_fat - totals[2])
        cals_diff = abs(target_cals - totals[3])
        
        # Simple weighted score
        score = protein_diff * 2 + carbs_diff + fat_diff + cals_diff * 3
        
        if score < best_score:
            best_score = score
            best_hall = hall_name
    
    return best_hall