import requests
import json

def get_streaming_meal_plan(user_goal: str, food_info: str, api_url: str = "http://127.0.0.1:8000/generate-meal-plan-stream"):
    """
    Queries the meal plan API and prints the streaming response.

    Args:
        user_goal (str): The user's dietary goal.
        food_info (str): Information about available food.
        api_url (str, optional): The URL of the API endpoint. Defaults to "http://127.0.0.1:8000/generate-meal-plan-stream".
    """
    request_data = {
        "user_goal": user_goal,
        "food_info": food_info
    }

    try:
        with requests.post(api_url, json=request_data, stream=True) as response:
            response.raise_for_status()

            print("--- Streaming Meal Plan ---")
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    print(chunk.decode('utf-8'), end='')
            print("\n--- End of Stream ---")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    except json.JSONDecodeError:
        print("Error decoding JSON from the response.")

if __name__ == '__main__':
    goal = "I want to lose weight and need a low-calorie lunch."
    foods = """
    Available at Wiley Dining Court:
    - Salad Bar with mixed greens, tomatoes, cucumbers, grilled chicken strips, light vinaigrette
    - Turkey and Swiss on whole wheat bread
    - Apple
    - Banana
    """
    get_streaming_meal_plan(goal, foods)