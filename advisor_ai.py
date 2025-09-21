import os
from pydantic import BaseModel
from google import genai
from google.genai import types

class MealPlanRequest(BaseModel):
    user_goal: str
    food_info: str
    
SYSTEM_PROMPT = """
You are a diet advisor. You should help the user reach their goals using the information provided to you. Please start by Google searching, research best practices and tips/tricks, any other useful information including best communication methods. There is a dictionary of all food at Purdue. Please use it and don't suggest anything not there. Say specific item names etc. Whenever you suggest food send the name from the dictionary and some of their ingredients.

THE ONLY FOOD THEY CAN EAT IS THE FOOD IN THE PROVIDED LIST. IF IT IS NOT THERE, THEY CANNOT EAT IT. IF THERE IS NO SUITABLE FOOD, EXPLAIN WHY. LISTEN TO THEIR GOALS AND ENSURE YOU RESPECT THEIR HARD CONSTRAINTS. SHARE THE NUTRIENT INFO OF THE DIET YOU PROPOSE AND SPECIFIC ITEMS.
"""

USER_INSTRUCTIONS_TEMPLATE = """
DINING COURT FOOD:
{food_info}

You are a dining court diet advisor for Purdue University. Your only goal is to help the user with the information provided. Please start by Google searching to research the best practices and tips/tricks for their goal.

Dining courts at Purdue work like this:
One meal swipe gets one meal at one dining court. Students get a set amount every week, but the food at the dining courts is unlimited per entry. Theoretically, they could stay in a dining court and eat multiple meals there, but they won't get re-entry on the same swipe. They can carry food out, but it's limited to one main dish and two sides, along with a fountain drink.

INSTRUCTIONS:
1. First, consider what is healthy and safe for the user.
2. Second, consider their hard constraints, soft constraints, and any other information.
3. Third, write the options and consider tradeoffs. Think and plan your response.
4. Finally, send their finalized meal plan in the specified JSON format. To ensure we only parse the JSON file, put the entire JSON object inside ||s.

JSON FORMAT:
WE also need total carbs, sugars, etc.
This is how it should be formatted:

||{{
  "dinner": {{
    "location_dinner": "Earhart",
    "justification_dinner": "A Malibu Burger on a GF bun offers a plant-based protein source and fiber. Roasted broccolini and corn provide essential vitamins, minerals, and additional fiber for a well-rounded meal.",
    "total_cals_dinner": 580.68,
    "total_fat_dinner": 24.8,
    "items": [
      {{
        "item_name": "Malibu Burger on GF Bun",
        "substation": "Grill",
        "servings": 1,
        "ingredients": ["Malibu Burger", "Gluten-Free Bun"],
        "common_allergens": ["Soy", "Wheat"],
        "total_cals_item": 450,
        "total_fat_item": 20
      }}
    ]
  }},
  "daily_totals": {{
    "meals": 1,
    "justification": "They are only eating one meal with us and will get their recommended daily nutrition.",
    "total_calories": 1247.26,
    "total_fat": 47.92,
    "total_protein": 41.73
  }}
}}||

If they ask for something impossible, state it in the justification, but do your best to meet their needs. THEY MIGHT WANT MORE THAN ONE MEAL AND HAVE OTHER CONSTRAINTS.

User Goal: {user_goal}
"""

async def stream_generator(user_goal: str, food_info: str):
    try:
        client = genai.Client(
            api_key=os.getenv("GOOGLE_API_KEY"),
        )

        model = "gemini-2.5-flash"
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=USER_INSTRUCTIONS_TEMPLATE.format(
                    food_info=food_info, user_goal=user_goal
                )),
                ],
            ),
        ]
        tools = [
            types.Tool(url_context=types.UrlContext()),
            types.Tool(googleSearch=types.GoogleSearch(
            )),
        ]
        generate_content_config = types.GenerateContentConfig(
            temperature=0,
            thinking_config = types.ThinkingConfig(
                thinking_budget=-1,
            ),
            tools=tools,
            system_instruction=[
                types.Part.from_text(text=SYSTEM_PROMPT),
            ],
        )

        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            print(chunk.text, end="")
            yield chunk.text
    except Exception as e:
        error_message = f"An error occurred while generating the meal plan: {str(e)}"
        yield error_message