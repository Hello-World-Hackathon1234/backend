import requests
import os
import json
import re

BASE_URL = "http://127.0.0.1:8000" 
ENDPOINT = "/estimate-nutrition"
IMAGE_FILENAME = "./image.png"

def test_image_upload():
    url = f"{BASE_URL}{ENDPOINT}"

    if not os.path.exists(IMAGE_FILENAME):
        print(f"Error: Image file not found at '{IMAGE_FILENAME}'")
        print("Please make sure the image is in the same directory as this script.")
        return

    try:
        with open(IMAGE_FILENAME, "rb") as image_file:
            files = {"file": (os.path.basename(IMAGE_FILENAME), image_file, "image/jpeg")}
            
            print(f"Uploading '{IMAGE_FILENAME}' to {url}...")
            response = requests.post(url, files=files, stream=True)
            
            if response.status_code == 200:
                print("\nSuccess!")
                
                full_response_text = ""
                for chunk in response.iter_content(decode_unicode=True):
                    if chunk:
                        print(chunk, end="", flush=True)
                        full_response_text += chunk
                
                print("\n\nEnd of Stream")
                json_match = re.search(r'\|\|(.*?)\|\|', full_response_text, re.DOTALL)
                if json_match:
                    try:
                        json_data = json.loads(json_match.group(1))
                        print("\n--- Parsed JSON Data ---")
                        print(json.dumps(json_data, indent=2))
                    except json.JSONDecodeError:
                        print("\nCould not parse the extracted JSON content.")
                else:
                    print("\nCould not find a JSON object wrapped in '||' in the response.")

            else:
                print(response.text)

    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ Connection Error: Could not connect to the server at {BASE_URL}.")
        print("Please make sure your FastAPI application is running.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    test_image_upload()
