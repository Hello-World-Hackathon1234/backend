class FoodItem:
    def __init__(self, name, protein, carbs, fat, cals):
        self.name = name
        self.protein = protein
        self.carbs = carbs
        self.fat = fat
        self.cals = cals
    
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
            
            # Stop if we're very close to target
            if best_distance < 5:  # Adjust threshold as needed
                break
    
    return selected_foods, (current_protein, current_carbs, current_fat, current_cals)


def create_food_item(name, nutrition_data):
    """Take nutrition column data and return a FoodItem object"""
    
    # Extract values
    calories = re.search(r'"name":\s*"Calories".*?"value":\s*([\d.]+)', nutrition_data)
    fat = re.search(r'"name":\s*"Total fat".*?"value":\s*([\d.]+)', nutrition_data)
    carbs = re.search(r'"name":\s*"Total Carbohydrate".*?"value":\s*([\d.]+)', nutrition_data)
    protein = re.search(r'"name":\s*"Protein".*?"value":\s*([\d.]+)', nutrition_data)
    
    return FoodItem(
        name=name,
        protein=round(float(protein.group(1)), 1) if protein else 0,
        carbs=round(float(carbs.group(1)), 1) if carbs else 0,
        fat=round(float(fat.group(1)), 1) if fat else 0,
        calories=int(float(calories.group(1))) if calories else 0
    )