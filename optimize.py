import re
import json

class FoodItem:
    def __init__(self, name, protein, carbs, fat, calories):
        self.name = name
        self.protein = protein
        self.carbs = carbs
        self.fat = fat
        self.cals = calories
    
    def __repr__(self):
        return f"FoodItem('{self.name}', P:{self.protein}, C:{self.carbs}, F:{self.fat}, Cal:{self.cals})"

def calculate_distance(target_protein, target_carbs, target_fat, target_cals, 
                      current_protein, current_carbs, current_fat, current_cals):

    protein_diff = abs(target_protein - current_protein)
    carbs_diff = abs(target_carbs - current_carbs)
    fat_diff = abs(target_fat - current_fat)
    cals_diff = abs(target_cals - current_cals)
    
    return protein_diff + carbs_diff + fat_diff + cals_diff

def find_optimal_foods_greedy(target_protein, target_carbs, target_fat, target_cals, food_items, max_items=10):
    selected_foods = []
    current_protein = 0
    current_carbs = 0
    current_fat = 0
    current_cals = 0
    available_foods = food_items.copy()
    
    for _ in range(max_items):
        if not available_foods:
            break
            
        # Check if we've reached or exceeded all targets
        if (current_protein >= target_protein and 
            current_carbs >= target_carbs and 
            current_fat >= target_fat or 
            current_cals >= target_cals or
            len(selected_foods) >= 5):
            break
            
        best_food = None
        best_distance = float('inf')
        
        # Try adding each available food and see which gets us closest to target
        for food in available_foods:
            new_protein = current_protein + food.protein
            new_carbs = current_carbs + food.carbs
            new_fat = current_fat + food.fat
            new_cals = current_cals + food.cals
            
            distance = calculate_distance(target_protein, target_carbs, target_fat, target_cals,
                                        new_protein, new_carbs, new_fat, new_cals)
            
            if distance < best_distance:
                best_distance = distance
                best_food = food
        
        if best_food:
            selected_foods.append(best_food)
            current_protein += best_food.protein
            current_carbs += best_food.carbs
            current_fat += best_food.fat
            current_cals += best_food.cals
            available_foods.remove(best_food)
    
    return selected_foods, (current_protein, current_carbs, current_fat, current_cals)


def create_food_item(name, nutrition_data):
    """Take nutrition column data and return a FoodItem object"""
    
    # Handle PostgreSQL array format with escaped JSON
    data_str = str(nutrition_data)
    
    # Remove outer braces and split by comma, then clean up each JSON string
    if data_str.startswith('{') and data_str.endswith('}'):
        # Remove outer braces
        data_str = data_str[1:-1]
        
        # Split by comma and parse each JSON string
        json_parts = []
        current_part = ""
        in_quotes = False
        escape_next = False
        
        for char in data_str:
            if escape_next:
                current_part += char
                escape_next = False
            elif char == '\\':
                escape_next = True
                current_part += char
            elif char == '"' and not escape_next:
                in_quotes = not in_quotes
                current_part += char
            elif char == ',' and not in_quotes:
                if current_part.strip():
                    # Remove surrounding quotes and unescape
                    clean_part = current_part.strip().strip('"').replace('\\"', '"')
                    json_parts.append(clean_part)
                current_part = ""
            else:
                current_part += char
        
        # Don't forget the last part
        if current_part.strip():
            clean_part = current_part.strip().strip('"').replace('\\"', '"')
            json_parts.append(clean_part)
    else:
        json_parts = [data_str]
    
    # Now parse each JSON string and extract nutrition values
    calories = fat = carbs = protein = 0
    
    for json_str in json_parts:
        try:
            fact = json.loads(json_str)
            name_field = fact.get('name', '').lower()
            value = fact.get('value')
            
            if value is not None:
                if 'calories' in name_field and 'from fat' not in name_field:
                    calories = value
                elif 'total fat' in name_field:
                    fat = value
                elif 'total carbohydrate' in name_field:
                    carbs = value
                elif name_field == 'protein':
                    protein = value
        except json.JSONDecodeError:
            continue
    
    return FoodItem(
        name=name,
        protein=round(protein, 1),
        carbs=round(carbs, 1),
        fat=round(fat, 1),
        calories=int(calories)
    )

def find_optimal_foods_balanced(target_protein, target_carbs, target_fat, target_cals, food_items, max_items=5):
    selected_foods = []
    current_protein = 0
    current_carbs = 0
    current_fat = 0
    current_cals = 0
    
    # Classify foods using heuristics
    main_dishes = []
    vegetables = []
    sides = []
    
    for food in food_items:
        protein_ratio = food.protein / max(food.cals, 1) if food.cals > 0 else 0
        
        # Main dish: high protein OR high calories OR good protein density
        if (food.protein >= 15 or food.cals >= 200 or protein_ratio >= 0.15):
            main_dishes.append(food)
        # Vegetable: low calories, low fat, moderate carbs
        elif (food.cals <= 50 and food.fat <= 2 and food.carbs <= 15):
            vegetables.append(food)
        # Everything else is a side
        else:
            sides.append(food)
    
    # Step 1: Pick the best main dish
    if main_dishes:
        best_main = None
        best_main_score = float('-inf')
        
        for main in main_dishes:
            protein_score = min(main.protein / max(target_protein * 0.6, 1), 1.0) * 100
            cal_efficiency = main.protein / max(main.cals, 1)
            score = protein_score + cal_efficiency * 30
            
            if score > best_main_score:
                best_main_score = score
                best_main = main
        
        if best_main:
            selected_foods.append(best_main)
            current_protein += best_main.protein
            current_carbs += best_main.carbs
            current_fat += best_main.fat
            current_cals += best_main.cals
    
    # Step 2: Add 1-2 vegetables for balance
    vegetables_added = 0
    for veg in sorted(vegetables, key=lambda x: x.carbs, reverse=True)[:3]:
        if vegetables_added < 2 and len(selected_foods) < max_items:
            selected_foods.append(veg)
            current_protein += veg.protein
            current_carbs += veg.carbs
            current_fat += veg.fat
            current_cals += veg.cals
            vegetables_added += 1
    
    # Step 3: Fill remaining with best options
    remaining_foods = [f for f in (sides + main_dishes + vegetables) if f not in selected_foods]
    remaining_slots = max_items - len(selected_foods)
    
    for _ in range(remaining_slots):
        if not remaining_foods:
            break
        
        best_food = None
        best_distance = float('inf')
        
        for food in remaining_foods:
            new_protein = current_protein + food.protein
            new_carbs = current_carbs + food.carbs
            new_fat = current_fat + food.fat
            new_cals = current_cals + food.cals
            
            # Bonus for vegetables if we need more
            vegetable_bonus = 0
            if (food.cals <= 50 and food.fat <= 2 and food.carbs <= 15 and vegetables_added < 2):
                vegetable_bonus = -20
            
            distance = calculate_distance(target_protein, target_carbs, target_fat, target_cals,
                                        new_protein, new_carbs, new_fat, new_cals) + vegetable_bonus
            
            if distance < best_distance:
                best_distance = distance
                best_food = food
        
        if best_food:
            selected_foods.append(best_food)
            current_protein += best_food.protein
            current_carbs += best_food.carbs
            current_fat += best_food.fat
            current_cals += best_food.cals
            remaining_foods.remove(best_food)
            
            # Track vegetables
            if (best_food.cals <= 50 and best_food.fat <= 2 and best_food.carbs <= 15):
                vegetables_added += 1
    
    return selected_foods, (current_protein, current_carbs, current_fat, current_cals)