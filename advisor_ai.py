import os
from pydantic import BaseModel
from google import genai
from google.genai import types
from typing import List, Optional
import os

# Define a model for a single chat message
class ChatMessage(BaseModel):
    role: str
    text: str

class MealPlanRequest(BaseModel):
    user_goal: str
    food_info: str
    # This line makes it optional
    chat_history: Optional[List[ChatMessage]] = None

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

IMAGE_PROMPT_TEMPLATE = """Please give the most accurate and realistic nutritional estimate for this food.

First, enumerate what you see in the photo, second, Google nutritional information for it, third calculate and summarize and lastly put into json format.


INSTRUCTIONS:
1. First, enumerate what you see in the photo and consider any objects of reference or obstruction.
2. Second, Google nutritional information for ALL of them and create bullet points along with estiamting their quantity.
3. Third calculate and summarize and consider sanity checks then output your justification and final estimates.
4. Lastly put into json format.
5. ALWAYS try your best and ALWAYS do these reasoning steps FIRST.

Please send your reasoning then send json surrounded by ||s
JSON FORMAT:
This is how it should be formatted: 
||{
  "items": [
    {
      "name": "Scrambled Eggs With Tabasco",
      "Calories": 140.2355,
      "Total fat": 7.0118,
      "Saturated fat": 1.5025,
      "Cholesterol": 372.0,
      "Sodium": 265.1598,
      "Total Carbohydrate": 1.532,
      "Sugar": 1.0168,
      "Added Sugar": 0.0,
      "Dietary Fiber": 0.0,
      "Protein": 12.5817,
      "Calcium": 60.0101,
      "Iron": 1.7517,
      "allergens": [
        "Egg"
      ],
      "other_potential_issues_health_hazards_etc": "Consuming raw or undercooked eggs may increase your risk of foodborne illness, such as Salmonella infection. Individuals with an egg allergy should avoid this dish.",
      "ingredients": [
        "2 large eggs",
        "1 tsp butter",
        "1 tbsp milk",
        "1/4 tsp Tabasco sauce",
        "Salt to taste",
        "Pepper to taste"
      ],
      "estimated_flavor": "The flavor is primarily savory and rich from the eggs, with a spicy and vinegary kick from the Tabasco sauce. The texture is soft and creamy."
    },
    {
      "name": "Grilled Chicken Salad",
      "Calories": 350.5,
      "Total fat": 15.2,
      "Saturated fat": 3.5,
      "Cholesterol": 85.0,
      "Sodium": 450.8,
      "Total Carbohydrate": 10.5,
      "Sugar": 5.2,
      "Added Sugar": 2.1,
      "Dietary Fiber": 3.8,
      "Protein": 42.3,
      "Calcium": 80.5,
      "Iron": 2.1,
      "allergens": [
        "Dairy (from cheese, if added)",
        "Soy (from some dressings)"
      ],
      "other_potential_issues_health_hazards_etc": "Ensure chicken is cooked to an internal temperature of 165°F (74°C) to prevent foodborne illness. Some salad dressings can be high in sodium and added sugars.",
      "ingredients": [
        "6 oz grilled chicken breast",
        "2 cups mixed greens",
        "1/4 cup cherry tomatoes",
        "1/4 cup cucumber",
        "2 tbsp balsamic vinaigrette",
        "1 oz feta cheese (optional)"
      ],
      "estimated_flavor": "A fresh and savory salad with the smoky taste of grilled chicken, complemented by the tangy and slightly sweet balsamic vinaigrette. The vegetables add a crisp and refreshing texture."
    },
    {
      "name": "Spaghetti with Marinara Sauce",
      "Calories": 410.0,
      "Total fat": 8.5,
      "Saturated fat": 1.5,
      "Cholesterol": 0.0,
      "Sodium": 650.0,
      "Total Carbohydrate": 75.0,
      "Sugar": 12.0,
      "Added Sugar": 4.0,
      "Dietary Fiber": 6.0,
      "Protein": 12.0,
      "Calcium": 60.0,
      "Iron": 3.5,
      "allergens": [
        "Wheat",
        "Gluten"
      ],
      "other_potential_issues_health_hazards_etc": "Individuals with celiac disease or gluten sensitivity should opt for gluten-free pasta. The sodium content can be high depending on the sauce.",
      "ingredients": [
        "2 oz spaghetti",
        "1 cup marinara sauce",
        "1/2 tbsp olive oil",
        "1 clove garlic",
        "Fresh basil for garnish"
      ],
      "estimated_flavor": "A classic Italian dish with the savory and slightly acidic taste of tomato-based marinara sauce, enhanced with garlic and fresh basil. The pasta provides a satisfying, chewy texture."
    }
  ]
}||
"""

async def image_stream_generator(image_bytes: bytes):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        yield "Error: GOOGLE_API_KEY not configured on the server."
        return

    client = genai.Client(api_key=api_key)

    model = "gemini-2.5-pro"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type='image/jpeg',
                ),
                types.Part.from_text(text=IMAGE_PROMPT_TEMPLATE),

            ],
        ),
    ]
    tools = [
        types.Tool(googleSearch=types.GoogleSearch(
        )),
    ]
    generate_content_config = types.GenerateContentConfig(
        thinking_config = types.ThinkingConfig(
            thinking_budget=-1,
        ),
        tools=tools,
    )

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        yield chunk.text
        print(chunk.text, end="")


async def stream_generator(user_goal: str, food_info: str, chat_history: Optional[List[ChatMessage]] = None):
    """
    Generates a meal plan stream based on user goals and food information.
    """

    history = ""
    for x in chat_history:
        f'Role: {x.role}\nText: {x.text}\n\n'
    
    try:
        client = genai.Client(
            api_key=os.getenv("GOOGLE_API_KEY"),
        )

        model = "gemini-2.5-flash"
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=f"History: {history}\n\n" + USER_INSTRUCTIONS_TEMPLATE.format(
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
            yield chunk.text
            print(chunk.text, end="")
    except Exception as e:
        error_message = f"An error occurred while generating the meal plan: {str(e)}"
        yield error_message
